# utils.py
from flask_mail import Message
from flask import current_app
import random

def generar_codigo_verificacion():
    return str(random.randint(100000, 999999))

def enviar_correo_verificacion(correo_destino, codigo):
    mail = current_app.extensions.get('mail')
    msg = Message(
        subject='Verificación de correo - AguaConecta',
        recipients=[correo_destino],
        body=f'Tu código de verificación es: {codigo}\n\nPor favor ingresa este código en la aplicación para activar tu cuenta.'
    )
    mail.send(msg)
