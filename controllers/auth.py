from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from MySQLdb.cursors import DictCursor 
# Agrega esto al principio junto con las otras importaciones
from utils import generar_codigo_verificacion, enviar_correo_verificacion
import traceback

import random

auth_bp = Blueprint('auth', __name__)
mail = Mail()

def init_mail(app):
    mail.init_app(app)

# 🔴 Ruta para eliminar cuenta
@auth_bp.route('/eliminar-cuenta', methods=['DELETE'])
@jwt_required()
def eliminar_cuenta():
    import traceback

    data = request.get_json()
    contrasena = data.get('contrasena')

    if not contrasena:
        return jsonify({'success': False, 'message': 'Contraseña requerida'}), 400

    usuario_id = get_jwt_identity()
    print(f"➡️ ID del usuario autenticado: {usuario_id}")

    cursor = None
    try:
        from MySQLdb.cursors import DictCursor
        cursor = current_app.mysql.connection.cursor(DictCursor)

        cursor.execute("SELECT contraseña FROM usuarios WHERE id = %s", (usuario_id,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

        hash_guardado = resultado['contraseña']
        if not check_password_hash(hash_guardado, contrasena):
            return jsonify({'success': False, 'message': 'Contraseña incorrecta'}), 401

        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        current_app.mysql.connection.commit()

        return jsonify({'success': True, 'message': 'Cuenta eliminada correctamente'})
    except Exception as e:
        print("❌ Error al eliminar cuenta:")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al eliminar la cuenta'}), 500
    finally:
        if cursor:
            cursor.close()

# ---------------------------
# REGISTRO DE USUARIO
# ---------------------------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    fecha_nacimiento = data.get('fecha_nacimiento')
    edad = data.get('edad')
    genero = data.get('genero')
    correo = data.get('correo')
    contraseña = data.get('contraseña')

    if not all([nombre, apellido, fecha_nacimiento, edad, genero, correo, contraseña]):
        return jsonify({'mensaje': 'Todos los campos son obligatorios'}), 400

    cursor = None
    try:
        cursor = current_app.mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone():
            return jsonify({'mensaje': 'Este correo ya está registrado'}), 409

        hashed_password = generate_password_hash(contraseña)
        codigo_verificacion = generar_codigo_verificacion()

        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, fecha_nacimiento, edad, genero, correo, contraseña, verificado, codigo_verificacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, fecha_nacimiento, edad, genero, correo, hashed_password, False, codigo_verificacion))
        current_app.mysql.connection.commit()

        enviar_correo_verificacion(correo, codigo_verificacion)

        return jsonify({'mensaje': 'Usuario registrado. Revisa tu correo para verificar tu cuenta'}), 201
    finally:
        if cursor:
            cursor.close()

# ---------------------------
# INICIO DE SESIÓN
# ---------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    correo = data.get('correo')
    contraseña = data.get('contraseña')

    if not correo or not contraseña:
        return jsonify({'mensaje': 'Correo y contraseña son obligatorios'}), 400

    cursor = None
    try:
        cursor = current_app.mysql.connection.cursor(DictCursor)  # ✅ aquí corregido
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        user = cursor.fetchone()

        if user and check_password_hash(user['contraseña'], contraseña):
            token = create_access_token(identity=str(user['id']))
            return jsonify({
                'mensaje': 'Inicio de sesión exitoso',
                'token': token,
                'usuario_id': user['id']  # ✅ se envía el ID
            }), 200
        elif user:
            return jsonify({'mensaje': 'Contraseña incorrecta'}), 401
        else:
            return jsonify({'mensaje': 'Correo no registrado'}), 404
    finally:
        if cursor:
            cursor.close()


# ---------------------------
# PERFIL DEL USUARIO
# ---------------------------
@auth_bp.route('/perfil', methods=['GET'])
@jwt_required()
def perfil_usuario():
    usuario_actual = get_jwt_identity()
    return jsonify({'mensaje': 'Acceso autorizado ✅', 'usuario': usuario_actual}), 200

# ---------------------------
# SOLICITAR RECUPERACIÓN
# ---------------------------
@auth_bp.route('/solicitar-recuperacion', methods=['POST'])
def solicitar_recuperacion():
    data = request.get_json()
    correo = data.get('correo')

    if not correo:
        return jsonify({'mensaje': 'Debes ingresar tu correo'}), 400

    cursor = None
    try:
        cursor = current_app.mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        if not cursor.fetchone():
            return jsonify({'mensaje': 'Este correo no está registrado'}), 404

        cursor.execute("DELETE FROM codigos_recuperacion WHERE correo = %s", (correo,))

        codigo = str(random.randint(100000, 999999))
        expiracion = datetime.now() + timedelta(minutes=15)

        cursor.execute("""
            INSERT INTO codigos_recuperacion (correo, codigo, expiracion)
            VALUES (%s, %s, %s)
        """, (correo, codigo, expiracion))
        current_app.mysql.connection.commit()

        msg = Message(
            subject="Recuperación de contraseña - AguaConecta",
            recipients=[correo],
            body=f"Tu código de recuperación es: {codigo}\nEste código expirará en 15 minutos.\n\nSi no solicitaste este código, ignora este mensaje."
        )
        mail.send(msg)
        return jsonify({'mensaje': 'Código enviado a tu correo electrónico ✅'}), 200
    except Exception as e:
        return jsonify({'mensaje': 'Error al enviar el correo', 'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()

# ---------------------------
# RESTABLECER CONTRASEÑA
# ---------------------------
@auth_bp.route('/restablecer-password', methods=['POST'])
def restablecer_contraseña():
    data = request.get_json()
    correo = data.get('correo')
    codigo = data.get('codigo')
    nueva_contraseña = data.get('nueva_contraseña')

    if not all([correo, codigo, nueva_contraseña]):
        return jsonify({'mensaje': 'Todos los campos son obligatorios'}), 400

    cursor = None
    try:
        cursor = current_app.mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM codigos_recuperacion 
            WHERE correo = %s AND codigo = %s AND expiracion > NOW()
            ORDER BY expiracion DESC LIMIT 1
        """, (correo, codigo))
        if not cursor.fetchone():
            return jsonify({'mensaje': 'Código inválido o expirado'}), 400

        hashed_password = generate_password_hash(nueva_contraseña)
        cursor.execute("UPDATE usuarios SET contraseña = %s WHERE correo = %s", (hashed_password, correo))
        cursor.execute("DELETE FROM codigos_recuperacion WHERE correo = %s", (correo,))
        current_app.mysql.connection.commit()

        return jsonify({'mensaje': 'Contraseña restablecida correctamente'}), 200
    finally:
        if cursor:
            cursor.close()
            
#VERIFICAR CÓDIGO
# En tu archivo de rutas de autenticación, por ejemplo auth_routes.py

# ---------------------------
# VERIFICAR CÓDIGO DE CORREO
# ---------------------------
@auth_bp.route('/verificar-correo', methods=['POST'])
def verificar_correo():
    data = request.get_json()
    correo = data.get('correo')
    codigo = data.get('codigo')

    if not correo or not codigo:
        return jsonify({'error': 'Faltan datos'}), 400

    try:
        cursor = current_app.mysql.connection.cursor()
        cursor.execute("SELECT codigo_verificacion FROM usuarios WHERE correo = %s", (correo,))
        result = cursor.fetchone()

        if not result or result['codigo_verificacion'] is None:
            return jsonify({'error': 'No se encontró el código de verificación para este correo'}), 404

        codigo_guardado = result['codigo_verificacion']

        if codigo == codigo_guardado:
            cursor.execute("UPDATE usuarios SET verificado = 1 WHERE correo = %s", (correo,))
            current_app.mysql.connection.commit()
            return jsonify({'success': True, 'message': 'Correo verificado correctamente'}), 200
        else:
            return jsonify({'success': False, 'message': 'Código incorrecto'}), 400

    except Exception as e:
        import traceback
        print("Error al verificar correo:")
        traceback.print_exc()
        return jsonify({'error': 'Error interno del servidor'}), 500

    finally:
        cursor.close()