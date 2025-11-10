from cryptography.fernet import Fernet

texto = "x?1_p-M.4!eM"

# generar una clave y crear un onjeto

clave = Fernet.generate_key()
objeto = Fernet(clave)

texto_encriptado = objeto.encrypt(texto.encode())
print(f"texto encriptado: {texto_encriptado}")

texto_desencriptado = objeto.decrypt(texto_encriptado).decode()
print(f"¿el texto es corecto? {texto_desencriptado}")
