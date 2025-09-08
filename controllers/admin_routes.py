from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from flask import current_app as app
from db_config import mysql
from MySQLdb.cursors import DictCursor
import requests
from random import randint
from flask_mail import Message
from controllers.extensions import mail 
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
from controllers.extensions import mail 
from flask_mail import Message
from flask import flash
from datetime import datetime
from flask import jsonify, url_for
from flask import render_template, make_response
from xhtml2pdf import pisa
from io import BytesIO



# Carpeta donde se guardarán las imágenes de campañas
UPLOAD_CARPETA_CAMPANIAS = os.path.join('static', 'uploads', 'campanias')

# Carpeta donde se guardarán los archivos PDF
UPLOAD_FOLDER = 'static/tutoriales'
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

admin_routes = Blueprint('admin_routes', __name__, url_prefix='/admin')

# Función para convertir coordenadas a dirección
def obtener_direccion(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=es"
        headers = {
            "User-Agent": "AguaConecta/1.0"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('display_name', 'Dirección no disponible')
        else:
            return "Error al obtener dirección"
    except Exception as e:
        print(f"❌ Error en obtener_direccion: {e}")
        return "Error al obtener dirección"

# Login del administrador
@admin_routes.route('/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        contrasena = request.form.get('contrasena', '').strip()

        if not correo or not contrasena:
            return render_template('admin/login.html', error="Por favor, completa todos los campos.")

        cursor = mysql.connection.cursor(DictCursor)
        cursor.execute("SELECT id, nombre, contrasena FROM administradores WHERE correo = %s", (correo,))
        admin = cursor.fetchone()
        cursor.close()

        if admin is None:
            return render_template('admin/login.html', error="Correo no encontrado.")

        if check_password_hash(admin['contrasena'], contrasena):
            session['admin_id'] = admin['id']
            session['admin_nombre'] = admin['nombre']
            return redirect(url_for('admin_routes.dashboard_admin'))
        else:
            return render_template('admin/login.html', error="Contraseña incorrecta.")

    return render_template('admin/login.html')

# Panel del administrador
# Ruta para mostrar el panel de reportes en la parte del administrador
@admin_routes.route('/reportes')
def panel_reportes():
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    try:
        # 🔹 Lista fija de lugares (aquí pegamos todos los que me diste)
        lugares_fijos = [
            "Arroyo Zarco Centro (Dilatada Centro)",
            "Arroyo Zarco la Mesa",
            "Barrio del Carmen",
            "Barrio del Jacal de Yebuciví",
            "Barrio el Ocote",
            "Barrio la Cabecera Primera Sección",
            "Barrio la Cabecera Tercera Sección",
            "Barrio la Galera (La Galera)",
            "Barrio San Pedro (La Concepción San Pedro)",
            "Barrio Santa Juana",
            "Benito Juárez",
            "Besana Ancha",
            "Buenavista Yebuciví",
            "Cañada de Guadarrama",
            "Casa Nueva (Casa Nueva Yebuciví)",
            "Cerro San Mateo",
            "Cieneguillas de Guadalupe",
            "Cieneguillas de Mañones",
            "Colonia Bellavista",
            "Colonia la Navidad",
            "Colonia Lázaro Cárdenas (La Trampa)",
            "Conjunto Habitacional Ecológico SUTEYM",
            "Dilatada Sur (Dilatada)",
            "Ejido de San Lorenzo Cuauhtenco",
            "Ejido de San Pedro",
            "Ejido de Santa Juana Primera Sección",
            "Ejido del Estanco",
            "Ejido la Gavia (San José la Gavia)",
            "Ejido San Antonio Ocoyotepec",
            "Ejido San Diego",
            "Ejido Tres Barrancas",
            "El Estanco",
            "El Plan",
            "El Plan de San Pedro",
            "El Santito (Barrio el Santito Yebuciví)",
            "El Tepetatal",
            "El Tulillo",
            "Ex-hacienda Boreje",
            "Ex-hacienda la Gavia",
            "Fraccionamiento Colinas del Sol",
            "La Cabecera",
            "La Hortaliza",
            "La Lagunita (Ejido del Jacal Yebuciví)",
            "La Palma (Ejido de San Francisco Tlalcilalcalpan)",
            "La Posta",
            "La Soledad Ocoyotepec",
            "La Tinaja",
            "La Unión Ocoyotepec",
            "Laguna de Tabernillas (El Resbaloso)",
            "Loma Blanca",
            "Loma de Guadalupe",
            "Loma de la Tinaja",
            "Loma de San Miguel",
            "Loma del Jacal (Loma de las Mangas)",
            "Loma del Puente",
            "Loma del Rancho",
            "Loma del Salitre (Colonia Loma del Salitre)",
            "Los Lagartos (Barrio los Lagartos de Yebuciví)",
            "Mayorazgo de León (Estación Río México)",
            "Mextepec (Ex-hacienda Mextepec)",
            "Mina México",
            "Ocoyotepec (Ocoyotepec Centro)",
            "Palos Amarillos",
            "Paredón Centro",
            "Paredón Ejido",
            "Paredón Ejido Norte",
            "Piedras Blancas (Piedras Blancas Centro)",
            "Piedras Blancas Sur",
            "Poteje Norte",
            "Poteje Sur",
            "Ranchería de San Diego (Ciénega de San Diego)",
            "Rancho Atotonilco",
            "Rancho la Soledad",
            "Rancho los Gavilanes",
            "Rancho San Diego Buenavista (Ejido San Diego)",
            "Rancho San José Amealco (Rancho el Capulín)",
            "Rancho San Nicolás",
            "Río Frío (Río Frío Yebuciví)",
            "Rosa Morada",
            "Salitre de Mañones",
            "San Agustín Citlali",
            "San Agustín las Tablas",
            "San Agustín Poteje Centro",
            "San Agustín Tabernillas",
            "San Antonio Atotonilco",
            "San Antonio Buenavista",
            "San Cristóbal",
            "San Francisco Tlalcilalcalpan",
            "San Isidro (El Reservado)",
            "San Lorenzo Cuauhtenco",
            "San Mateo Tlalchichilpan",
            "San Miguel Almoloyán",
            "San Nicolás Amealco",
            "San Pedro de la Hortaliza (Ejido Almoloyán)",
            "Santa Catarina Tabernillas",
            "Santa Juana Centro (La Palma)",
            "Santa Juana Primera Sección",
            "Santa Juana Segunda Sección",
            "Santa María Nativitas",
            "Santiaguito (Tlalcilalcalli)",
            "Tierra y Libertad (Miguel Hidalgo)",
            "Unidad Habitacional Olaldea (Colonia Olaldea)",
            "Villa de Almoloya de Juárez",
            "Yebuciví Centro (Yebuciví)"
        ]

        lugar_seleccionado = request.args.get('lugar', '')

        cur = mysql.connection.cursor(DictCursor)

        if lugar_seleccionado:
            # 🔹 Búsqueda parcial (LIKE)
            cur.execute("""
                SELECT * FROM reportes
                WHERE archivado = 0 AND eliminado = 0 AND direccion LIKE %s
            """, (f"%{lugar_seleccionado}%",))
        else:
            cur.execute("""
                SELECT * FROM reportes
                WHERE archivado = 0 AND eliminado = 0
            """)

        reportes = cur.fetchall()
        cur.close()

        # Procesar direcciones como ya lo tenías...
        for reporte in reportes:
            ubicacion = reporte.get('ubicacion')
            try:
                if ubicacion:
                    partes = [p.strip() for p in ubicacion.split(',')]
                    if len(partes) == 2:
                        lat, lon = partes
                        try:
                            lat_f = float(lat)
                            lon_f = float(lon)
                            reporte['direccion'] = obtener_direccion(lat_f, lon_f)
                        except ValueError:
                            reporte['direccion'] = "Coordenadas inválidas"
                    else:
                        reporte['direccion'] = "Ubicación mal formateada"
                else:
                    reporte['direccion'] = "No disponible"
            except Exception as e:
                print("❌ Error procesando ubicación:", e)
                reporte['direccion'] = "Error al procesar ubicación"

        return render_template(
            'admin/panel.html',
            reportes=reportes,
            lugares=lugares_fijos,
            lugar_seleccionado=lugar_seleccionado
        )

    except Exception as e:
        return f"❌ Error cargando reportes: {str(e)}", 500



    
@admin_routes.route('/archivar-reporte/<int:reporte_id>', methods=['POST'])
def archivar_reporte(reporte_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE reportes SET archivado = TRUE WHERE id = %s", (reporte_id,))
        mysql.connection.commit()
        cur.close()
        flash("📁 Reporte archivado correctamente.")
        return redirect(url_for('admin_routes.panel_reportes'))
    except Exception as e:
        print(f"❌ Error al archivar reporte: {e}")
        return "❌ Error interno al archivar reporte", 500

@admin_routes.route('/desarchivar-reporte/<int:reporte_id>', methods=['POST'])
def desarchivar_reporte(reporte_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE reportes SET archivado = FALSE WHERE id = %s", (reporte_id,))
        mysql.connection.commit()
        cur.close()

        flash("✅ Reporte desarchivado correctamente.")
        return redirect(url_for('admin_routes.historial_reportes'))
    except Exception as e:
        print(f"❌ Error al desarchivar reporte: {e}")
        return "❌ Error interno al desarchivar reporte", 500


    
@admin_routes.route('/historial-reportes')
def historial_reportes():
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM reportes WHERE archivado = TRUE ORDER BY fecha DESC")
        reportes = cur.fetchall()
        cur.close()
        return render_template('admin/historial_reportes.html', reportes=reportes)
    except Exception as e:
        print(f"❌ Error al cargar historial: {e}")
        return "❌ Error al cargar historial", 500

# Ruta para eliminar un reporte (cambia su estado a "eliminado" sin borrarlo de la base de datos)
# Se accede mediante método POST y se espera un parámetro <int:reporte_id> en la URL
@admin_routes.route('/eliminar-reporte/<int:reporte_id>', methods=['POST'])
def eliminar_reportes(reporte_id):
    # Verifica si hay un administrador autenticado en sesión
    if 'admin_id' not in session:
        # Si no hay sesión, redirige al inicio de sesión de administradores
        return redirect(url_for('admin_routes.login_admin'))
    try:
        # Imprime en consola que se está ingresando al proceso de eliminación del reporte
        print(f"🛠️ Entrando a eliminar el reporte con ID: {reporte_id}")
        # Abre un cursor de conexión a la base de datos
        cur = mysql.connection.cursor()
        # Ejecuta una consulta SQL para marcar el reporte como eliminado (no se borra realmente)
        cur.execute("UPDATE reportes SET eliminado = 1 WHERE id = %s", (reporte_id,))
        # Guarda los cambios realizados en la base de datos
        mysql.connection.commit()
        # Cierra el cursor
        cur.close()
        # Muestra un mensaje flash para notificar que el reporte fue marcado como eliminado
        flash("🗑️ Reporte eliminado y enviado a la sección de eliminados.")
        # Redirige al panel principal de reportes del administrador
        return redirect(url_for('admin_routes.panel_reportes'))
    # Captura cualquier error que ocurra durante el proceso
    except Exception as e:
        # Imprime el error en consola para depuración
        print(f"❌ Error al eliminar reporte: {e}")
        # Devuelve un mensaje de error al usuario y código de estado 500
        return "❌ Error interno al eliminar reporte", 500


@admin_routes.route('/reportes-eliminados')
def reportes_eliminados():
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM reportes WHERE eliminado = 1")
    reportes = cur.fetchall()
    cur.close()
    return render_template('reportes_eliminados.html', reportes_eliminados=reportes)

@admin_routes.route('/restaurar-reporte/<int:reporte_id>', methods=['POST'])
def restaurar_reporte(reporte_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE reportes SET eliminado = 0 WHERE id = %s", (reporte_id,))
        mysql.connection.commit()
        cur.close()
        flash("✅ Reporte restaurado exitosamente.")
        return redirect(url_for('admin_routes.reportes_eliminados'))
    except Exception as e:
        print(f"❌ Error al restaurar reporte: {e}")
        return "❌ Error interno al restaurar reporte", 500

# Eliminar definitivamente un solo reporte
@admin_routes.route('/eliminar-definitivo/<int:reporte_id>', methods=['POST'])
def eliminar_definitivo(reporte_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    try:
        cur = mysql.connection.cursor(DictCursor)
        # Obtener imagen si hay
        cur.execute("SELECT imagen FROM reportes WHERE id = %s", (reporte_id,))
        reporte = cur.fetchone()
        if reporte and reporte.get('imagen'):
            ruta = os.path.join('static/uploads', reporte['imagen'])
            if os.path.exists(ruta):
                os.remove(ruta)
        # Eliminar de la BD
        cur.execute("DELETE FROM reportes WHERE id = %s", (reporte_id,))
        mysql.connection.commit()
        cur.close()
        flash("✅ Reporte eliminado permanentemente.")
        return redirect(url_for('admin_routes.reportes_eliminados'))
    except Exception as e:
        print(f"❌ Error al eliminar definitivo: {e}")
        return "❌ Error al eliminar definitivamente", 500


# Eliminar todos los reportes eliminados
@admin_routes.route('/eliminar-todos-reportes-definitivo', methods=['POST'])
def eliminar_todos_reportes_definitivo():
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    try:
        cur = mysql.connection.cursor(DictCursor)
        # Obtener imágenes
        cur.execute("SELECT imagen FROM reportes WHERE eliminado = 1")
        reportes = cur.fetchall()
        for r in reportes:
            imagen = r.get('imagen')
            if imagen:
                ruta = os.path.join('static/uploads', imagen)
                if os.path.exists(ruta):
                    os.remove(ruta)
        # Eliminar de la BD
        cur.execute("DELETE FROM reportes WHERE eliminado = 1")
        mysql.connection.commit()
        cur.close()
        flash("✅ Todos los reportes eliminados fueron borrados definitivamente.")
        return redirect(url_for('admin_routes.reportes_eliminados'))
    except Exception as e:
        print(f"❌ Error al eliminar todos definitivamente: {e}")
        return "❌ Error interno", 500


# Cerrar sesión
@admin_routes.route('/logout')
def logout_admin():
    session.clear()
    return redirect(url_for('admin_routes.login_admin'))

# Solicitar recuperación
@admin_routes.route('/recuperar', methods=['GET', 'POST'])
def solicitar_recuperacion_admin():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()

        if not correo:
            return render_template('admin/solicitar_recuperacion.html', error="Por favor, ingresa tu correo.")

        cursor = mysql.connection.cursor(DictCursor)
        cursor.execute("SELECT id FROM administradores WHERE correo = %s", (correo,))
        admin = cursor.fetchone()
        cursor.close()

        if not admin:
            return render_template('admin/solicitar_recuperacion.html', error="Correo no registrado.")

        codigo = str(randint(100000, 999999))
        session['codigo_recuperacion'] = codigo
        session['correo_recuperacion'] = correo

        try:
            msg = Message("Código de recuperación - AguaConecta", recipients=[correo])
            msg.body = f"""
Hola,

Tu código de recuperación es: {codigo}

Este código es válido por tiempo limitado. Si no solicitaste este código, puedes ignorar este mensaje.
"""
            mail.send(msg)
        except Exception as e:
            print(f"❌ Error enviando correo: {e}")
            return render_template('admin/solicitar_recuperacion.html', error="Error al enviar el correo. Intenta más tarde.")

        return render_template('admin/ingresar_codigo.html', mensaje="✅ Se ha enviado un código a tu correo.")

    return render_template('admin/solicitar_recuperacion.html')

# Restablecer contraseña
@admin_routes.route('/restablecer-contrasena', methods=['GET', 'POST'])
def restablecer_contrasena():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        nueva = request.form.get('nueva_contrasena', '').strip()
        confirmar = request.form.get('confirmar_contrasena', '').strip()

        if not codigo or not nueva or not confirmar:
            return render_template('admin/ingresar_codigo.html', error="Todos los campos son obligatorios")

        if nueva != confirmar:
            return render_template('admin/ingresar_codigo.html', error="Las contraseñas no coinciden")

        if codigo != session.get('codigo_recuperacion'):
            return render_template('admin/ingresar_codigo.html', error="El código es incorrecto")

        correo = session.get('correo_recuperacion')
        if not correo:
            return redirect(url_for('admin_routes.solicitar_recuperacion_admin'))

        contrasena_hash = generate_password_hash(nueva)

        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE administradores SET contrasena = %s WHERE correo = %s", (contrasena_hash, correo))
        mysql.connection.commit()
        cursor.close()

        session.pop('codigo_recuperacion', None)
        session.pop('correo_recuperacion', None)

        return render_template('admin/ingresar_codigo.html',
                               mensaje="✅ Contraseña actualizada correctamente. Redirigiendo al inicio de sesión...",
                               mensaje_exito=True)

    return render_template('admin/ingresar_codigo.html')

# Actualizar estado del reporte
# Ruta para actualizar el estado de un reporte (solo accesible mediante método POST)
@admin_routes.route('/actualizar-estado', methods=['POST'])
def actualizar_estado_reporte():
    # Verifica si el administrador ha iniciado sesión
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))
    try:
        # Obtiene el ID del reporte desde el formulario enviado y elimina espacios
        reporte_id = request.form.get('reporte_id', '').strip()
        # Obtiene el nuevo estado para el reporte y elimina espacios
        nuevo_estado = request.form.get('nuevo_estado', '').strip()
        # Verifica que ambos datos estén presentes
        if not reporte_id or not nuevo_estado:
            return "❌ Datos incompletos para actualizar el estado.", 400
        # Conjunto de estados válidos permitidos
        ESTADOS_VALIDOS = {"Pendiente", "En proceso", "Resuelto"}
        # Si el estado no es válido, devuelve error
        if nuevo_estado not in ESTADOS_VALIDOS:
            return f"❌ Estado no válido: {nuevo_estado}", 400
        # Intenta convertir el ID del reporte a número entero
        try:
            reporte_id_int = int(reporte_id)
        except ValueError:
            return "❌ ID de reporte inválido.", 400
        # Inicia el cursor para ejecutar consultas
        cur = mysql.connection.cursor(DictCursor)
        # Consulta para obtener el usuario que envió el reporte
        cur.execute("SELECT usuario_id FROM reportes WHERE id = %s", (reporte_id_int,))
        reporte = cur.fetchone()
        # Si no se encuentra el reporte, devuelve error
        if not reporte:
            cur.close()
            return "❌ El reporte no existe.", 404
        # Extrae el ID del usuario asociado al reporte
        usuario_id = reporte['usuario_id']
        # Busca el nombre y correo del usuario con ese ID
        cur.execute("SELECT nombre, correo FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cur.fetchone()
        # Si el usuario no existe, devuelve error
        if not usuario:
            cur.close()
            return "❌ Usuario del reporte no encontrado.", 404
        # Extrae correo y nombre del usuario
        correo_usuario = usuario['correo']
        nombre_usuario = usuario['nombre']
        # Obtiene el nombre del administrador que está realizando la actualización
        admin_id = session.get('admin_id')
        cur.execute("SELECT nombre FROM administradores WHERE id = %s", (admin_id,))
        admin = cur.fetchone()
        # Si no se encuentra el nombre del administrador, se coloca como "Desconocido"
        nombre_admin = admin['nombre'] if admin else "Desconocido"
        # Actualiza el estado del reporte y el campo atendido_por con el nombre del administrador
        cur.execute("UPDATE reportes SET estado = %s, atendido_por = %s WHERE id = %s", 
                    (nuevo_estado, nombre_admin, reporte_id_int))
        # Guarda los cambios en la base de datos
        mysql.connection.commit()
        # Cierra el cursor
        cur.close()
        # Intenta enviar un correo al usuario notificando el cambio de estado
        try:
            # Crea el mensaje de correo con título y destinatario
            msg = Message(f"Actualización del estado de tu reporte - AguaConecta", recipients=[correo_usuario])  
            # Cuerpo del mensaje
            msg.body = f"""
Hola {nombre_usuario},

Tu reporte con ID #{reporte_id_int} ha cambiado de estado. Ahora se encuentra como: **{nuevo_estado}**.

Gracias por usar AguaConecta. Estamos trabajando para mejorar el servicio de tu comunidad.

Este mensaje es automático, por favor no respondas.
"""
            # Envía el correo
            mail.send(msg)
        except Exception as e:
            # Si falla el envío del correo, imprime el error en consola
            print(f"❌ Error al enviar correo al usuario: {e}")
        # Redirige nuevamente al panel de reportes tras actualizar
        return redirect(url_for('admin_routes.panel_reportes'))
    except Exception as e:
        # Si ocurre cualquier error inesperado, lo imprime en consola y devuelve un error 500
        print(f"❌ Error al actualizar estado: {e}")
        return "❌ Error interno al actualizar estado del reporte", 500


@admin_routes.route('/dashboard')
def dashboard_admin():
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    nombre = session.get('admin_nombre', 'Administrador')
    return render_template('admin/dashboard_admin.html', nombre_admin=nombre)

@admin_routes.route('/crear-admin', methods=['GET', 'POST'])
def form_crear_admin():
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = generate_password_hash(request.form['contrasena'])
        area = request.form['area']
        tipo = request.form['tipo']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM administradores WHERE correo = %s", (correo,))
        existente = cur.fetchone()

        if existente:
            cur.close()
            return render_template('admin/crear_admin.html', mensaje="❌ El correo ya está registrado.")

        # Generar código de verificación y fecha de expiración
        codigo = str(random.randint(100000, 999999))
        expiracion = datetime.now() + timedelta(minutes=10)

        # Insertar el nuevo administrador (no verificado aún)
        cur.execute("""
            INSERT INTO administradores (nombre, correo, contrasena, area, tipo, codigo_verificacion, expiracion_codigo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, correo, contrasena, area, tipo, codigo, expiracion))
        mysql.connection.commit()
        admin_id = cur.lastrowid
        cur.close()

        # Enviar el código al correo del nuevo administrador
        msg = Message("Código de verificación - AguaConecta",
                      sender="tucorreo@ejemplo.com",  # Usa tu remitente configurado
                      recipients=[correo])
        msg.body = f"Hola {nombre},\n\nTu código de verificación para activar tu cuenta es: {codigo}\nEste código expira en 10 minutos.\n\nGracias por registrarte en AguaConecta."
        mail.send(msg)

        return redirect(url_for('admin_routes.verificar_codigo', admin_id=admin_id))

    return render_template('admin/crear_admin.html')

from flask import redirect, url_for

@admin_routes.route('/verificar-codigo/<int:admin_id>', methods=['GET', 'POST'])
def verificar_codigo(admin_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT correo, codigo_verificacion, expiracion_codigo FROM administradores WHERE id = %s", (admin_id,))
    admin = cur.fetchone()

    if not admin:
        cur.close()
        return "Administrador no encontrado", 404

    correo = admin['correo']
    codigo_real = admin['codigo_verificacion']
    
    expiracion_raw = admin['expiracion_codigo']
    expiracion = datetime.strptime(expiracion_raw, "%Y-%m-%d %H:%M:%S") if isinstance(expiracion_raw, str) else expiracion_raw
    tiempo_restante = int((expiracion - datetime.now()).total_seconds()) if expiracion else 0
    cur.close()

    if request.method == 'POST':
        codigo_ingresado = request.form['codigo']

        if datetime.now() > expiracion:
            return render_template('admin/verificar_codigo.html', correo=correo, error="❌ El código ha expirado.", tiempo_restante=0)

        if codigo_ingresado == codigo_real:
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE administradores
                SET codigo_verificacion = NULL, expiracion_codigo = NULL
                WHERE id = %s
            """, (admin_id,))
            mysql.connection.commit()
            cur.close()
            # Redirigir directamente al panel
            return redirect(url_for('admin_routes.dashboard_admin'))

        return render_template('admin/verificar_codigo.html', correo=correo, error="❌ Código incorrecto.", tiempo_restante=tiempo_restante)

    return render_template('admin/verificar_codigo.html', correo=correo, tiempo_restante=tiempo_restante)


@admin_routes.route('/reenviar-codigo', methods=['POST'])
def reenviar_codigo():
    correo = request.form['correo']
    nuevo_codigo = random.randint(100000, 999999)
    nueva_expiracion = datetime.now() + timedelta(minutes=10)

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE administradores 
        SET codigo_verificacion = %s, expiracion_codigo = %s 
        WHERE correo = %s
    """, (nuevo_codigo, nueva_expiracion, correo))
    mysql.connection.commit()

    # Recuperar ID para la URL
    cur.execute("SELECT id FROM administradores WHERE correo = %s", (correo,))
    admin = cur.fetchone()
    admin_id = admin['id'] if admin else None
    cur.close()

    msg = Message("Nuevo código de verificación - AguaConecta", recipients=[correo])
    msg.body = f"Tu nuevo código de verificación es: {nuevo_codigo}. Expira en 10 minutos."
    mail.send(msg)

    # Redirigir de nuevo a la página de verificación con mensaje
    return redirect(url_for('admin_routes.verificar_codigo', admin_id=admin_id))

@admin_routes.route('/ver-administradores')
def ver_administradores():
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
    SELECT a.*, 
        COUNT(r.id) AS reportes_atendidos
    FROM administradores a
    LEFT JOIN reportes r ON r.atendido_por = a.nombre
    GROUP BY a.id
    """)

    administradores = cur.fetchall()
    cur.close()
    return render_template('admin/ver_administradores.html', administradores=administradores)

@admin_routes.route('/reportes-atendidos/<nombre_admin>')
def reportes_atendidos(nombre_admin):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("""
        SELECT * FROM reportes 
        WHERE atendido_por = %s
        ORDER BY fecha DESC
    """, (nombre_admin,))
    reportes = cur.fetchall()
    cur.close()

    return render_template('admin/reportes_atendidos.html', reportes=reportes, nombre_admin=nombre_admin)

@admin_routes.route('/reporte/<int:reporte_id>')
def ver_detalle_reporte(reporte_id):
    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM reportes WHERE id = %s", (reporte_id,))
    reporte = cur.fetchone()
    cur.close()

    if not reporte:
        return "Reporte no encontrado", 404

    return render_template('admin/detalle_reporte.html', reporte=reporte)

@admin_routes.route('/eliminar-admin/<int:admin_id>')
def eliminar_admin(admin_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM administradores WHERE id = %s", (admin_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_routes.ver_administradores'))



import os
from flask import request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/tutoriales'
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ruta para agregar y mostrar tutoriales en el panel del administrador
# Acepta tanto GET (mostrar formulario) como POST (guardar nuevo tutorial)
@admin_routes.route('/tutoriales', methods=['GET', 'POST'])
def form_tutoriales():
    # Verifica que el administrador haya iniciado sesión
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))
    # Variable para mostrar mensajes en la interfaz (éxito o error)
    mensaje = None
    # Si el método es POST, se está enviando un nuevo tutorial
    if request.method == 'POST':
        # Obtiene los datos enviados desde el formulario HTML
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        enlace = request.form.get('enlace')  # El enlace puede ser opcional
        archivo = request.files.get('archivo_pdf')  # Archivo PDF que sube el usuario
        nombre_pdf = None  # Variable que almacenará el nombre del PDF si se carga
        # Verifica que se haya subido un archivo y que sea un tipo permitido (PDF, por ejemplo)
        if archivo and allowed_file(archivo.filename):
            # Asegura que el nombre del archivo sea seguro para evitar problemas de seguridad
            filename = secure_filename(archivo.filename)
            # Define la ruta completa donde se guardará el archivo
            ruta_pdf = os.path.join(UPLOAD_FOLDER, filename)
            # Guarda el archivo en el servidor
            archivo.save(ruta_pdf)
            # Guarda el nombre del archivo para almacenarlo en la base de datos
            nombre_pdf = filename
        # Inserta los datos del nuevo tutorial en la base de datos
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("""
            INSERT INTO tutoriales (titulo, descripcion, enlace, archivo_pdf)
            VALUES (%s, %s, %s, %s)
        """, (titulo, descripcion, enlace, nombre_pdf))
        mysql.connection.commit()
        cur.close()
        # Define el mensaje de éxito para mostrar en la plantilla
        mensaje = "✅ Tutorial agregado exitosamente."
    # En cualquier caso (GET o después de insertar), se obtienen todos los tutoriales existentes
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, titulo, descripcion, enlace, archivo_pdf FROM tutoriales")
    tutoriales = cur.fetchall()
    cur.close()
    # Renderiza la plantilla HTML con la lista de tutoriales y el mensaje (si existe)
    return render_template('admin/agregar_tutorial.html', mensaje=mensaje, tutoriales=tutoriales)


@admin_routes.route('/ver_tutoriales')
def ver_tutoriales():
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    cur = mysql.connection.cursor(DictCursor)  # ← AQUÍ está la corrección
    cur.execute("SELECT * FROM tutoriales ORDER BY id DESC")
    tutoriales = cur.fetchall()
    cur.close()
    return render_template('admin/ver_tutoriales.html', tutoriales=tutoriales)

# Ruta para eliminar tutorial
@admin_routes.route('/eliminar-tutorial/<int:id>')
def eliminar_tutorial(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT archivo_pdf FROM tutoriales WHERE id = %s", (id,))
    tutorial = cur.fetchone()

    # Borra archivo si existe
    if tutorial and tutorial['archivo_pdf']:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, tutorial['archivo_pdf']))
        except Exception as e:
            print("❌ Error eliminando archivo:", e)

    cur.execute("DELETE FROM tutoriales WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_routes.ver_tutoriales'))

# Ruta para editar tutorial
@admin_routes.route('/editar-tutorial/<int:id>', methods=['GET', 'POST'])
def editar_tutorial(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM tutoriales WHERE id = %s", (id,))
    tutorial = cur.fetchone()

    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        enlace = request.form['enlace']
        archivo = request.files.get('archivo_pdf')
        nuevo_nombre_pdf = tutorial['archivo_pdf']

        if archivo and allowed_file(archivo.filename):
            # Elimina el archivo anterior si existe
            if tutorial['archivo_pdf']:
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, tutorial['archivo_pdf']))
                except Exception as e:
                    print("❌ Error eliminando archivo anterior:", e)

            nuevo_nombre_pdf = secure_filename(archivo.filename)
            archivo.save(os.path.join(UPLOAD_FOLDER, nuevo_nombre_pdf))

        cur.execute("""
            UPDATE tutoriales
            SET titulo = %s, descripcion = %s, enlace = %s, archivo_pdf = %s
            WHERE id = %s
        """, (titulo, descripcion, enlace, nuevo_nombre_pdf, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin_routes.ver_tutoriales'))

    return render_template('admin/editar_tutorial.html', tutorial=tutorial)

# Ruta para eliminar un reporte
"""@admin_routes.route('/eliminar-reporte/<int:reporte_id>', methods=['POST'])
def eliminar_reporte(reporte_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_routes.login_admin'))

    try:
        cur = mysql.connection.cursor(DictCursor)
        
        # Obtener nombre del archivo si existe (para borrarlo del servidor)
        cur.execute("SELECT imagen FROM reportes WHERE id = %s", (reporte_id,))
        reporte = cur.fetchone()

        if not reporte:
            cur.close()
            return "❌ Reporte no encontrado.", 404

        imagen = reporte.get('imagen')
        if imagen:
            ruta_imagen = os.path.join('static/uploads', imagen)
            if os.path.exists(ruta_imagen):
                try:
                    os.remove(ruta_imagen)
                except Exception as e:
                    print(f"❌ Error eliminando imagen: {e}")

        # Eliminar el reporte de la base de datos
        cur.execute("DELETE FROM reportes WHERE id = %s", (reporte_id,))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('admin_routes.panel_reportes'))

    except Exception as e:
        print(f"❌ Error al eliminar el reporte: {e}")
        return "❌ Error interno al eliminar el reporte.", 500 """


@admin_routes.route('/campanias')
def listar_campanias():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campanias ORDER BY creado_en DESC")
    campanias = cur.fetchall()
    cur.close()
    return render_template('admin/campanias/listar_campanias.html', campanias=campanias)


# Ruta para agregar una nueva campaña, acepta tanto GET (mostrar formulario) como POST (guardar datos)
@admin_routes.route('/campanias/nueva', methods=['GET', 'POST'])
def nueva_campania():
    # Si el método de la petición es POST, significa que el formulario fue enviado
    if request.method == 'POST':
        # Obtiene los valores del formulario HTML
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        direccion = request.form['direccion']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        estado = request.form['estado']  # Puede ser "activa" o "inactiva"
        # Procesa la imagen cargada desde el formulario
        imagen_file = request.files['imagen']
        nombre_imagen = None  # Valor por defecto si no se sube imagen
        # Verifica si se ha enviado una imagen y tiene nombre
        if imagen_file and imagen_file.filename:
            # Limpia el nombre del archivo para que sea seguro (sin caracteres peligrosos)
            nombre_imagen = secure_filename(imagen_file.filename)
            # Construye la ruta completa donde se guardará la imagen en el servidor
            ruta_imagen = os.path.join(UPLOAD_CARPETA_CAMPANIAS, nombre_imagen)
            # Guarda el archivo de imagen en la carpeta correspondiente
            imagen_file.save(ruta_imagen)
        # Inserta los datos de la nueva campaña en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO campanias (titulo, descripcion, direccion, imagen, fecha_inicio, fecha_fin, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (titulo, descripcion, direccion, nombre_imagen, fecha_inicio, fecha_fin, estado))
        # Confirma la transacción en la base de datos
        mysql.connection.commit()
        # Cierra el cursor
        cur.close()
        # Redirige al listado de campañas tras guardar exitosamente
        return redirect(url_for('admin_routes.listar_campanias'))
    # Si la petición es GET, simplemente muestra el formulario para registrar una nueva campaña
    return render_template('admin/campanias/nueva_campania.html')



@admin_routes.route('/campanias/editar/<int:id>', methods=['GET', 'POST'])
def editar_campania(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campanias WHERE id = %s", (id,))
    campania = cur.fetchone()

    if not campania:
        return "Campaña no encontrada", 404

    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        direccion = request.form['direccion']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        estado = request.form['estado']

        nueva_imagen = request.files['imagen']
        nombre_imagen = campania['imagen']
        if nueva_imagen and nueva_imagen.filename:
            nombre_imagen = secure_filename(nueva_imagen.filename)
            ruta_imagen = os.path.join(UPLOAD_CARPETA_CAMPANIAS, nombre_imagen)
            nueva_imagen.save(ruta_imagen)

        cur.execute("""
            UPDATE campanias
            SET titulo=%s, descripcion=%s, direccion=%s, imagen=%s, fecha_inicio=%s, fecha_fin=%s, estado=%s
            WHERE id=%s
        """, (titulo, descripcion, direccion, nombre_imagen, fecha_inicio, fecha_fin, estado, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin_routes.listar_campanias'))

    cur.close()
    return render_template('admin/campanias/editar_campania.html', campania=campania)


@admin_routes.route('/campanias/eliminar/<int:id>', methods=['POST'])
def eliminar_campania(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM campanias WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_routes.listar_campanias'))

@admin_routes.route('/campanias/estado/<int:id>', methods=['POST'])
def cambiar_estado_campania(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT estado FROM campanias WHERE id = %s", (id,))
    resultado = cur.fetchone()

    if not resultado:
        cur.close()
        return redirect(url_for('admin_routes.listar_campanias'))

    estado_actual = resultado['estado']  # ← aquí el cambio correcto
    nuevo_estado = 'inactiva' if estado_actual == 'activa' else 'activa'

    cur.execute("UPDATE campanias SET estado = %s WHERE id = %s", (nuevo_estado, id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('admin_routes.listar_campanias'))

# Ruta para obtener campañas activas
@admin_routes.route('/api/campanias', methods=['GET'])
def obtener_campanias_activas():
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM campanias WHERE estado = 'activa'")
        campanias = cur.fetchall()
        cur.close()

        for c in campanias:
            c['imagen'] = url_for('static', filename='uploads/campanias/' + c['imagen'], _external=True)

        return jsonify(campanias)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ruta para obtener todos los tutoriales
@admin_routes.route('/api/tutoriales', methods=['GET'])
def obtener_tutoriales():
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM tutoriales")
        tutoriales = cur.fetchall()
        cur.close()

        for t in tutoriales:
            if t['archivo_pdf']:
                t['archivo_pdf'] = url_for('static', filename='tutoriales/' + t['archivo_pdf'], _external=True)

        return jsonify(tutoriales)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@admin_routes.route('/admin/asistentes-campania')
def ver_asistentes_campania():
    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute('''
            SELECT 
                i.id,
                u.nombre,
                u.apellido,
                u.correo,
                i.quiere_asistir,
                c.titulo AS campania,
                c.direccion,
                i.fecha_registro
            FROM interes_campanias i
            JOIN usuarios u ON i.usuario_id = u.id
            JOIN campanias c ON i.campania_id = c.id
            ORDER BY i.fecha_registro DESC
        ''')
        asistentes = cur.fetchall()
        cur.close()
        return render_template('admin/asistentes_campania.html', asistentes=asistentes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from flask import send_file  # ya debes tener otros imports
import os

@admin_routes.route('/reporte/<int:reporte_id>/pdf')
def descargar_pdf_reporte(reporte_id):
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute("SELECT * FROM reportes WHERE id = %s", (reporte_id,))
    reporte = cursor.fetchone()
    cursor.close()

    if not reporte:
        return "Reporte no encontrado", 404

    # Ruta absoluta de la imagen si existe
    imagen_path = None
    if reporte['imagen']:
        imagen_path = os.path.join(os.getcwd(), 'static', 'uploads', reporte['imagen'])
        if not os.path.exists(imagen_path):
            imagen_path = None  # si la imagen no existe físicamente

    html = render_template('reporte_pdf.html', reporte=reporte, imagen_path=imagen_path)

    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_file, link_callback=resolve_static_path)

    if pisa_status.err:
        return "Error al generar PDF", 500

    response = make_response(pdf_file.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_{reporte_id}.pdf'
    return response


# Función necesaria para que xhtml2pdf resuelva las rutas a imágenes
def resolve_static_path(uri, rel):
    if uri.startswith('/static/'):
        path = os.path.join(os.getcwd(), uri.lstrip('/'))
        return path
    return uri
