from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from db_config import init_mysql
from controllers.auth import auth_bp, init_mail
from controllers.reportes import reportes_bp
from controllers.admin_routes import admin_routes
from controllers.extensions import mail
from controllers.api_routes import api_routes
import os  # Para variables de entorno y puerto dinámico

# Crear la app
app = Flask(__name__)
CORS(app)

# Inicializar Flask-Mail
mail.init_app(app)

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = 'clave_secreta_super_segura'
app.config['UPLOAD_FOLDER'] = 'static/uploads/campanias'
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
JWTManager(app)

# Configuración de MySQL
init_mysql(app)

# Configuración de correo electrónico usando variables de entorno
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # Definir en el servidor
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # Definir en el servidor
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
init_mail(app)

# Registrar Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(reportes_bp)
app.register_blueprint(admin_routes, url_prefix='/admin')
app.register_blueprint(api_routes)

# Ruta de prueba
@app.route('/')
def home():
    return "✅ API AguaConecta funcionando correctamente"

# Ejecutar la app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Puerto dinámico asignado por el servidor
    app.run(host='0.0.0.0', port=port, debug=False)  # Debug desactivado en producción
