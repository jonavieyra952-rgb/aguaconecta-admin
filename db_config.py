# Importa la clase MySQL del paquete flask_mysqldb, que permite conectar y trabajar con bases de datos MySQL desde Flask
from flask_mysqldb import MySQL 
# Crea una instancia de MySQL que se utilizará para conectar con la base de datos
mysql = MySQL()  
# Define una función para inicializar la configuración de MySQL en la aplicación Flask
def init_mysql(app):
    # Configura la dirección del servidor de la base de datos (en este caso, local)
    app.config['MYSQL_HOST'] = 'localhost'
    # Configura el nombre de usuario para conectarse a MySQL (por defecto, 'root')
    app.config['MYSQL_USER'] = 'root'
    # Configura la contraseña del usuario de MySQL (en este caso está vacía)
    app.config['MYSQL_PASSWORD'] = ''
    # Configura el nombre de la base de datos que se usará 
    app.config['MYSQL_DB'] = 'agua_bd'
    # Establece una clave secreta para la aplicación Flask (usada para sesiones, etc.)
    app.secret_key = 'clave_secreta'
    # Configura el tipo de cursor que se usará, en este caso un diccionario (los resultados se devolverán como diccionarios)
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    # Inicializa la instancia MySQL con la aplicación Flask
    mysql.init_app(app)
    # Asocia la instancia MySQL a la aplicación Flask para poder acceder a ella fácilmente desde otras partes del código
    app.mysql = mysql  
