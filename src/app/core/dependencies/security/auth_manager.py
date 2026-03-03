from passlib.context import CryptContext

from src.app.core.dependencies.security.crypt_context import get_crypt_context
from src.app.core.security.auth_manager import AuthManager


def get_auth_manager(context: CryptContext | None = None) -> AuthManager:
    """
    Build auth manager instance.

    :param context: optional crypt context

    :return: auth manager
    """
    active_context = context or get_crypt_context()
    return AuthManager(context=active_context)
