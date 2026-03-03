from passlib.context import CryptContext


def get_crypt_context() -> CryptContext:
    """
    Build passlib crypt context instance.

    :return: crypt context
    """
    return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
