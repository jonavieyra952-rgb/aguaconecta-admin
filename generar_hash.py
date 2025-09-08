# archivo: generar_hash.py
from werkzeug.security import generate_password_hash

nueva_contrasena = "220123"
hash_generado = generate_password_hash(nueva_contrasena)
print(f"🔐 Hash generado:\n{hash_generado}")
