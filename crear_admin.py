from flask import Flask
from werkzeug.security import generate_password_hash
from db_config import mysql, init_mysql  # ✅ Importa la función init_mysql

app = Flask(__name__)
init_mysql(app)  # ✅ Aquí inicializas la base de datos correctamente

with app.app_context():
    nombre = "admin"
    correo = "ivancolin2002@gmail.com"
    contrasena_plana = "220123"

    # Generar el hash
    hash_contrasena = generate_password_hash(contrasena_plana)
    print("🔐 Hash generado:", hash_contrasena)

    try:
        cursor = app.mysql.connection.cursor()  # ✅ Aquí usas app.mysql
        cursor.execute("INSERT INTO administradores (nombre, correo, contrasena) VALUES (%s, %s, %s)",
                       (nombre, correo, hash_contrasena))
        app.mysql.connection.commit()
        cursor.close()
        print("✅ Administrador registrado correctamente.")
    except Exception as e:
        print("❌ Error al registrar el administrador:", str(e))
