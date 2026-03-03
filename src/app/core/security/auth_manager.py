from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from jwt import decode, encode
from passlib.context import CryptContext

from src.cfg.cfg import settings


class AuthManager:
    """
    Authentication security primitives.

    :param context: password hashing context
    """

    def __init__(self, context: CryptContext) -> None:
        self._context = context

    def hash_password(self, password: str) -> str:
        """
        Hash plain password.

        :param password: plain password

        :return: hashed password
        """
        return self._context.hash(secret=password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against stored hash.

        :param plain_password: plain password
        :param hashed_password: stored hash

        :return: verification result
        """
        return self._context.verify(secret=plain_password, hash=hashed_password)

    def generate_jwt(self, user_id: int) -> str:
        """
        Generate jwt access token for user.

        :param user_id: unique user id

        :return: jwt access token
        """
        now = datetime.now(tz=UTC)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_lifespan_minutes),
            "jti": str(uuid4()),
        }
        return encode(
            payload=payload,
            key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def decode_jwt(self, token: str) -> dict[str, str]:
        """
        Decode and validate jwt token.

        :param token: jwt token

        :return: payload dictionary
        """
        return decode(
            jwt=token,
            key=settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate raw password reset token.

        :return: raw reset token
        """
        return token_urlsafe(32)

    @staticmethod
    def hash_reset_token(token: str) -> str:
        """
        Hash reset token before persistence.

        :param token: raw reset token

        :return: reset token hash
        """
        return sha256(token.encode()).hexdigest()
