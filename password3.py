from passlib.context import CryptContext

contexto = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=30000
)

texto = "x?1_p-M.4!.eh"
texto_encriptado = contexto.hash(texto)
print(f"Texto encriptado: {texto_encriptado}")

print(f"¿El texto es correcto? {contexto.verify(texto, texto_encriptado)}")








