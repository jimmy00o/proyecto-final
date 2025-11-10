from flask import Flask
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)


password_plano = "mi_contraseña_secreta"

hash_password = bcrypt.generate_password_hash(password_plano).decode('utf-8')
print(f"Contraseña encriptada: {hash_password}")
contraseña_valida = bcrypt.check_password_hash(hash_password, password_plano)
print(f"contraseña interna: {contraseña_valida}")
