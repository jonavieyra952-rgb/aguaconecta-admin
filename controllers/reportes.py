from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from flask_mail import Message
from controllers.extensions import mail  # Asegúrate de tener esta instancia
import traceback
from controllers.extensions import mail


reportes_bp = Blueprint('reportes', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def extension_valida(nombre_archivo):
    return '.' in nombre_archivo and nombre_archivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 📤 Crear nuevo reporte
@reportes_bp.route('/api/reportes', methods=['POST'])
@jwt_required()
def crear_reporte():
    print("➡️ Form fields:", dict(request.form))
    print("➡️ Archivos recibidos:", request.files)

    usuario_id = get_jwt_identity()
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    direccion = request.form.get('direccion')
    ubicacion_raw = request.form.get('ubicacion')
    imagen = request.files.get('imagen')
    nombre_ciudadano = request.form.get('nombre_ciudadano')
    telefono = request.form.get('telefono_ciudadano') or request.form.get('telefono')

    # Validaciones
    if not titulo:
        return jsonify({'mensaje': 'El campo título es obligatorio'}), 400
    if not descripcion:
        return jsonify({'mensaje': 'El campo descripción es obligatorio'}), 400
    if not ubicacion_raw:
        return jsonify({'mensaje': 'La ubicación es obligatoria'}), 400
    if not nombre_ciudadano:
        return jsonify({'mensaje': 'El nombre del ciudadano es obligatorio'}), 400
    if not telefono:
        return jsonify({'mensaje': 'El número de teléfono es obligatorio'}), 400

    # Procesar ubicación (lat,long)
    partes = ubicacion_raw.strip().split(',')
    if len(partes) >= 2:
        try:
            lat = float(partes[0])
            lng = float(partes[1])
            ubicacion = f"{lat},{lng}"
        except ValueError:
            return jsonify({'mensaje': 'Las coordenadas no son válidas'}), 400
    else:
        return jsonify({'mensaje': 'Ubicación inválida, debe ser latitud,longitud'}), 400

    nombre_imagen = None
    if imagen and imagen.filename and imagen.filename.lower() != 'imagen':
        if extension_valida(imagen.filename):
            nombre_imagen = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{imagen.filename}")
            carpeta_uploads = os.path.join('static', 'uploads')
            os.makedirs(carpeta_uploads, exist_ok=True)
            ruta_guardado = os.path.join(carpeta_uploads, nombre_imagen)
            imagen.save(ruta_guardado)
        else:
            return jsonify({'mensaje': 'Tipo de archivo no permitido'}), 400

    estado = "pendiente"
    fecha = datetime.now()

    try:
        cursor = current_app.mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO reportes (
                usuario_id, titulo, descripcion, imagen, direccion,
                ubicacion, estado, fecha, nombre_ciudadano, telefono_ciudadano
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            usuario_id, titulo, descripcion, nombre_imagen, direccion,
            ubicacion, estado, fecha, nombre_ciudadano, telefono
        ))
        current_app.mysql.connection.commit()

        # 🔹 Enviar notificación a administradores
        try:
            cursor.execute("SELECT correo FROM administradores WHERE verificado = 1")
            admin_correos = [row['correo'] for row in cursor.fetchall()]

            if admin_correos:
                asunto = "📢 Nuevo reporte ciudadano - AguaConecta"
                enlace_panel = "http://192.168.252.211:5000/admin/reportes"  # Cambiar por tu URL real
                html_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                        <div style="background-color: white; padding: 20px; border-radius: 8px;">
                            <h2 style="color: #007BFF;">Nuevo reporte ciudadano</h2>
                            <p><strong>Título:</strong> {titulo}</p>
                            <p><strong>Descripción:</strong> {descripcion}</p>
                            <p><strong>Ubicación:</strong> {ubicacion}</p>
                            <p><strong>Ciudadano:</strong> {nombre_ciudadano}</p>
                            <p><strong>Teléfono:</strong> {telefono}</p>
                            {"<img src='http://192.168.252.211:5000/static/uploads/" + nombre_imagen + "' style='max-width:300px;border-radius:5px;'/>" if nombre_imagen else ""}
                            <p style="margin-top:20px;">
                                <a href="{enlace_panel}" 
                                   style="display:inline-block; padding:10px 15px; background-color:#007BFF; color:white; text-decoration:none; border-radius:5px;">
                                    Ver en el panel
                                </a>
                            </p>
                        </div>
                    </body>
                </html>
                """
                msg = Message(asunto, recipients=admin_correos)
                msg.html = html_body
                mail.send(msg)  # ✅ envío correcto

        except Exception as e:
            print("❌ Error enviando notificación a administradores:")
            print(traceback.format_exc())

        return jsonify({'mensaje': 'Reporte enviado con éxito ✅'}), 201

    except Exception as e:
        print("❌ Error al insertar en la base de datos:", e)
        return jsonify({'mensaje': 'Error al enviar el reporte', 'error': str(e)}), 500
    finally:
        cursor.close()

# 🔍 Obtener reportes del usuario autenticado
@reportes_bp.route('/api/reportes/mis-reportes', methods=['GET'])
@jwt_required()
def obtener_reportes_usuario():
    usuario_id = get_jwt_identity()
    try:
        cur = current_app.mysql.connection.cursor(dictionary=True)
        cur.execute("""
            SELECT id, titulo, descripcion, imagen, ubicacion, direccion, estado, fecha,
                   nombre_ciudadano, telefono_ciudadano
            FROM reportes
            WHERE usuario_id = %s AND eliminado = 0
            ORDER BY fecha DESC
        """, (usuario_id,))
        reportes = cur.fetchall()
        cur.close()
        return jsonify(reportes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 🗑 Eliminar reporte (y su imagen)
@reportes_bp.route('/api/reportes/<int:reporte_id>', methods=['DELETE'])
@jwt_required()
def eliminar_reporte(reporte_id):
    usuario_id = get_jwt_identity()
    try:
        cursor = current_app.mysql.connection.cursor()
        cursor.execute("SELECT * FROM reportes WHERE id = %s AND usuario_id = %s", (reporte_id, usuario_id))
        fila = cursor.fetchone()

        if not fila:
            return jsonify({'mensaje': 'Reporte no encontrado o no autorizado'}), 404

        columnas = [col[0] for col in cursor.description]
        reporte = dict(zip(columnas, fila))

        if reporte['imagen']:
            ruta_imagen = os.path.join('static', 'uploads', reporte['imagen'])
            if os.path.exists(ruta_imagen):
                os.remove(ruta_imagen)

        cursor.execute("DELETE FROM reportes WHERE id = %s", (reporte_id,))
        current_app.mysql.connection.commit()
        return jsonify({'mensaje': 'Reporte eliminado correctamente ✅'}), 200

    except Exception as e:
        print("❌ Error al eliminar reporte:", e)
        return jsonify({'mensaje': 'Error al eliminar el reporte', 'error': str(e)}), 500
    finally:
        cursor.close()

# 🖼 Servir imágenes desde /uploads
@reportes_bp.route('/uploads/<path:filename>')
def obtener_imagen(filename):
    return send_from_directory(os.path.join('static', 'uploads'), filename)
