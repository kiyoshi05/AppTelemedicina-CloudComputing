import hashlib
import hmac
import os

ITERACIONES = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${salt.hex()}${digest.hex()}"


def verify_password(password: str, almacenado: str) -> bool:
    try:
        _, iteraciones, salt, esperado = almacenado.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), int(iteraciones)
    )
    return hmac.compare_digest(digest.hex(), esperado)
