# controllers/api_routes.py
from flask import Blueprint, jsonify, url_for
from db_config import mysql
from flask_mysqldb import MySQLdb
from MySQLdb.cursors import DictCursor
from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import MySQLdb.cursors
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from flask import send_from_directory

api_routes = Blueprint('api_routes', __name__)

# ✅ Ruta pública para servir archivos PDF de documentos legales
@api_routes.route('/docs/<path:filename>', methods=['GET'])
def servir_pdf_docs(filename):
    docs_path = os.path.join(os.getcwd(), 'static', 'docs')
    return send_from_directory(docs_path, filename)


# ✅ Ruta pública para obtener campañas activas
@api_routes.route('/api/campanias', methods=['GET'])
def obtener_campanias_activas():
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM campanias WHERE estado = 'activa'")
        campanias = cur.fetchall()
        cur.close()

        for c in campanias:
            if c['imagen']:
                c['imagen'] = url_for('static', filename='uploads/campanias/' + c['imagen'], _external=True)

        return jsonify(campanias)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ✅ Ruta pública para obtener la lista de tutoriales
# Define una ruta accesible mediante una petición GET en la URL '/api/tutoriales'
@api_routes.route('/api/tutoriales', methods=['GET'])
def obtener_tutoriales():
    try:
        # Crea un cursor para interactuar con la base de datos utilizando formato de diccionario (DictCursor)
        cur = mysql.connection.cursor(DictCursor)
        # Ejecuta una consulta SQL que obtiene todos los registros de la tabla 'tutoriales',
        # ordenados por la fecha de creación de forma descendente (más recientes primero)
        cur.execute("SELECT * FROM tutoriales ORDER BY fecha_creacion DESC")
        # Recupera todos los resultados de la consulta y los almacena en una lista de diccionarios
        tutoriales = cur.fetchall()
        # Cierra el cursor después de completar la consulta
        cur.close()
        # Itera sobre cada tutorial obtenido
        for t in tutoriales:
            # Si el campo 'archivo_pdf' tiene un valor (es decir, hay un PDF asociado al tutorial)
            if t['archivo_pdf']:
                # Genera la URL pública completa al archivo PDF dentro de la carpeta 'static/tutoriales'
                # con _external=True se genera una URL absoluta (incluye dominio)
                t['archivo_pdf'] = url_for('static', filename='tutoriales/' + t['archivo_pdf'], _external=True)
        # Devuelve la lista de tutoriales en formato JSON como respuesta al cliente
        return jsonify(tutoriales)
    # En caso de ocurrir un error durante el proceso, se captura la excepción
    except Exception as e:
        # Devuelve un mensaje de error con el detalle del error y un código de estado HTTP 500 (error interno del servidor)
        return jsonify({'error': str(e)}), 500


@api_routes.route('/api/interes-campania', methods=['POST'])
def registrar_interes_campania():
    try:
        data = request.json
        usuario_id = data.get('usuario_id')
        campania_id = data.get('campania_id')
        quiere_asistir = data.get('quiere_asistir')

        if not usuario_id or not campania_id:
            return jsonify({'error': 'Faltan datos'}), 400

        cur = mysql.connection.cursor(DictCursor)

        # Verificar si ya existe
        cur.execute('''
            SELECT * FROM interes_campanias 
            WHERE usuario_id = %s AND campania_id = %s
        ''', (usuario_id, campania_id))
        existente = cur.fetchone()

        if existente:
            # Actualizar el estado si ya existe
            cur.execute('''
                UPDATE interes_campanias
                SET quiere_asistir = %s, fecha_registro = CURRENT_TIMESTAMP
                WHERE usuario_id = %s AND campania_id = %s
            ''', (quiere_asistir, usuario_id, campania_id))
            mysql.connection.commit()
            cur.close()
            return jsonify({'mensaje': 'Interés actualizado'}), 200
        else:
            # Insertar nuevo si no existe
            cur.execute('''
                INSERT INTO interes_campanias (usuario_id, campania_id, quiere_asistir)
                VALUES (%s, %s, %s)
            ''', (usuario_id, campania_id, quiere_asistir))
            mysql.connection.commit()
            cur.close()
            return jsonify({'mensaje': 'Interés registrado'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_routes.route('/api/interes-campania/usuario/<int:usuario_id>/campania/<int:campania_id>', methods=['GET'])
def obtener_interes_usuario(usuario_id, campania_id):
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute('''
            SELECT quiere_asistir FROM interes_campanias
            WHERE usuario_id = %s AND campania_id = %s
        ''', (usuario_id, campania_id))
        resultado = cur.fetchone()
        cur.close()

        if resultado:
            return jsonify({'quiere_asistir': resultado['quiere_asistir']}), 200
        else:
            return jsonify({'quiere_asistir': False}), 200  # No hay registro = no le interesa

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@api_routes.route('/api/interes-campania/consulta', methods=['POST'])
def consultar_interes_campania():
    try:
        data = request.json
        usuario_id = data.get('usuario_id')
        campania_id = data.get('campania_id')

        if not usuario_id or not campania_id:
            return jsonify({'error': 'Faltan datos'}), 400

        cur = mysql.connection.cursor(DictCursor)
        cur.execute('''
            SELECT quiere_asistir FROM interes_campanias 
            WHERE usuario_id = %s AND campania_id = %s
        ''', (usuario_id, campania_id))
        resultado = cur.fetchone()
        cur.close()

        if resultado:
            return jsonify({'quiere_asistir': resultado['quiere_asistir']}), 200
        else:
            return jsonify({'quiere_asistir': False}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_routes.route('/api/campanias/favoritas/<int:usuario_id>', methods=['GET'])
def obtener_campanias_favoritas(usuario_id):
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute('''
            SELECT c.*, i.fecha_registro FROM campanias c
            JOIN interes_campanias i ON c.id = i.campania_id
            WHERE i.usuario_id = %s AND i.quiere_asistir = 1
            ORDER BY i.fecha_registro DESC
        ''', (usuario_id,))
        campanias = cur.fetchall()
        cur.close()

        for c in campanias:
            if not c['imagen'].startswith('http'):
                c['imagen'] = url_for('static', filename=f'uploads/campanias/{c["imagen"]}', _external=True)

        return jsonify(campanias), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_routes.route('/api/campanias/favoritas/eliminar/<int:usuario_id>', methods=['DELETE'])
def eliminar_favoritos(usuario_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute('''
            DELETE FROM interes_campanias
            WHERE usuario_id = %s AND quiere_asistir = 1
        ''', (usuario_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'mensaje': 'Campañas favoritas eliminadas'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_routes.route('/api/reportes_usuario/<int:usuario_id>', methods=['GET'])
def reportes_por_usuario(usuario_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT 
                id,
                titulo,
                descripcion,
                imagen,
                ubicacion,
                direccion,
                estado,
                fecha,
                nombre_ciudadano,
                telefono_ciudadano
            FROM reportes
            WHERE usuario_id = %s 
              AND eliminado = 0 
              AND archivado = 0 
              AND visible_para_usuario = 1  -- 🔍 solo los visibles
            ORDER BY fecha DESC
        """, (usuario_id,))
        
        rows = cur.fetchall()
        return jsonify(rows), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_routes.route('/api/reportes/<int:reporte_id>/editar', methods=['POST'])
def editar_reporte(reporte_id):
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT estado FROM reportes WHERE id = %s", (reporte_id,))
        reporte = cur.fetchone()

        if not reporte:
            return jsonify({'error': 'Reporte no encontrado'}), 404

        if reporte['estado'].lower() != 'pendiente':
            return jsonify({'error': 'Solo se puede editar un reporte pendiente'}), 403

        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        direccion = request.form.get('direccion')
        ubicacion = request.form.get('ubicacion')  # ✅ nuevo campo
        imagen = request.files.get('imagen')

        if not titulo or not descripcion or not direccion or not ubicacion:
            return jsonify({'error': 'Faltan campos obligatorios'}), 400

        campos_sql = "titulo = %s, descripcion = %s, direccion = %s, ubicacion = %s"
        valores = [titulo, descripcion, direccion, ubicacion]

        if imagen:
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join('static/uploads', filename))
            campos_sql += ", imagen = %s"
            valores.append(filename)

        valores.append(reporte_id)
        cur.execute(f"UPDATE reportes SET {campos_sql} WHERE id = %s", valores)
        mysql.connection.commit()
        cur.close()

        return jsonify({'mensaje': 'Reporte actualizado'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_routes.route('/api/reportes/<int:reporte_id>/eliminar', methods=['DELETE'])
def eliminar_reporte(reporte_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM reportes WHERE id = %s", (reporte_id,))
        reporte = cur.fetchone()

        if not reporte:
            return jsonify({'error': 'Reporte no encontrado'}), 404

        # 🟡 En lugar de eliminar, marcamos como no visible
        cur.execute("UPDATE reportes SET visible_para_usuario = 0 WHERE id = %s", (reporte_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({'mensaje': 'Reporte ocultado para el usuario'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Ruta pública para obtener datos del usuario
@api_routes.route('/api/usuario/<int:id>', methods=['GET'])
def obtener_usuario(id):
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("""
            SELECT id, nombre, apellido, correo, fecha_registro, edad, genero
            FROM usuarios
            WHERE id = %s
        """, (id,))
        usuario = cur.fetchone()
        cur.close()

        if usuario:
            # ✅ Convertir fecha a formato ISO
            if isinstance(usuario['fecha_registro'], datetime):
                usuario['fecha_registro'] = usuario['fecha_registro'].isoformat()

            return jsonify(usuario)
        else:
            return jsonify({'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        print("❌ Error al obtener usuario:", e)
        return jsonify({'error': str(e)}), 500

@api_routes.route('/api/cambiar-contrasena', methods=['POST'])
def cambiar_contrasena():
    try:
        data = request.json
        usuario_id = data.get('usuario_id')
        contrasena_actual = data.get('contrasena_actual')
        nueva_contrasena = data.get('nueva_contrasena')

        if not all([usuario_id, contrasena_actual, nueva_contrasena]):
            return jsonify({"error": "Faltan campos obligatorios"}), 400

        cur = mysql.connection.cursor(DictCursor)

        # ✅ Nombre de columna correcto con ñ
        cur.execute("SELECT contraseña FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cur.fetchone()

        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # ✅ Acceso con clave correcta: 'contraseña'
        contrasena_db = usuario['contraseña']

        if not check_password_hash(contrasena_db, contrasena_actual):
            return jsonify({"error": "La contraseña actual es incorrecta"}), 401

        nueva_hash = generate_password_hash(nueva_contrasena)
        cur.execute("UPDATE usuarios SET contraseña = %s WHERE id = %s", (nueva_hash, usuario_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Contraseña actualizada exitosamente"})

    except Exception as e:
        print("❌ Error al cambiar contraseña:", e)
        return jsonify({"error": str(e)}), 500
