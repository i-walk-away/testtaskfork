from datetime import UTC, datetime, timedelta
import re

from sqlalchemy.exc import IntegrityError

from src.app.core.exceptions.auth_exc import (
    InvalidCredentials,
    InvalidResetToken,
    ResetTokenCooldownExceeded,
    UserAlreadyExists,
    WeakPassword,
)
from src.app.core.security.auth_manager import AuthManager
from src.app.domain.models.db.user import User
from src.app.domain.repositories.password_reset_repository import PasswordResetRepository
from src.app.domain.repositories.user_repository import UserRepository
from src.cfg.cfg import settings


class AuthService:
    """
    Authentication service for state-changing auth workflows.

    :param user_repository: user repository
    :param reset_repository: reset repository
    :param auth_manager: auth manager
    """

    def __init__(
        self,
        user_repository: UserRepository,
        reset_repository: PasswordResetRepository,
        auth_manager: AuthManager,
    ) -> None:
        self._user_repository = user_repository
        self._reset_repository = reset_repository
        self._auth_manager = auth_manager

    async def register(self, username: str, email: str, password: str) -> str:
        """
        Register a new user.

        :param username: username
        :param email: user email
        :param password: plain password

        :return: access token
        """
        existing_username = await self._user_repository.get_by_username(username=username)
        existing_email = await self._user_repository.get_by_email(email=email)

        if existing_username is not None or existing_email is not None:
            raise UserAlreadyExists("username or email already exists")

        self._validate_password_strength(password=password)

        hashed_password = self._auth_manager.hash_password(password=password)
        try:
            user = await self._user_repository.create(
                username=username,
                email=email,
                hashed_password=hashed_password,
            )
        except IntegrityError as exc:
            raise UserAlreadyExists("username or email already exists") from exc

        return self._auth_manager.generate_jwt(user_id=user.id)

    async def login(self, username: str, password: str) -> str:
        """
        Authenticate user and return jwt.

        :param username: username
        :param password: plain password

        :return: access token
        """
        user = await self._get_authenticated_user(username=username, password=password)
        return self._auth_manager.generate_jwt(user_id=user.id)

    async def request_password_reset(self, email: str) -> str:
        """
        Create a new password reset token.

        :param email: user email

        :return: raw reset token
        """
        user = await self._user_repository.get_by_email(email=email)
        if user is None:
            return self._auth_manager.generate_reset_token()

        latest_token = await self._reset_repository.get_latest_for_user(user_id=user.id)
        if latest_token is not None:
            cooldown_boundary = latest_token.created_at + timedelta(
                seconds=settings.reset_token_cooldown_seconds,
            )
            if datetime.now(tz=UTC) < cooldown_boundary:
                raise ResetTokenCooldownExceeded("try again later")

        await self._reset_repository.invalidate_all_for_user(user_id=user.id)
        raw_token = self._auth_manager.generate_reset_token()
        token_hash = self._auth_manager.hash_reset_token(token=raw_token)
        expires_at = datetime.now(tz=UTC) + timedelta(minutes=settings.reset_token_lifespan_minutes)

        await self._reset_repository.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return raw_token

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset user password by token.

        :param token: raw reset token
        :param new_password: new plain password
        """
        token_hash = self._auth_manager.hash_reset_token(token=token)
        reset_token = await self._reset_repository.get_active_by_hash(token_hash=token_hash)

        if reset_token is None:
            raise InvalidResetToken("invalid or expired token")

        self._validate_password_strength(password=new_password)

        new_hashed_password = self._auth_manager.hash_password(password=new_password)
        await self._user_repository.update_password(
            user_id=reset_token.user_id,
            hashed_password=new_hashed_password,
        )
        await self._reset_repository.mark_used(token_id=reset_token.id)

    async def _get_authenticated_user(self, username: str, password: str) -> User:
        """
        Resolve authenticated user by credentials.

        :param username: username
        :param password: plain password

        :return: authenticated user
        """
        user = await self._user_repository.get_by_username(username=username)

        if user is None:
            raise InvalidCredentials("invalid credentials")

        is_valid = self._auth_manager.verify_password(
            plain_password=password,
            hashed_password=user.hashed_password,
        )
        if not is_valid:
            raise InvalidCredentials("invalid credentials")

        return user

    def _validate_password_strength(self, password: str) -> None:
        """
        Validate password against minimal security policy.

        :param password: plain password
        """
        if len(password) < 8:
            raise WeakPassword("password must be at least 8 characters")
        if re.search(pattern=r"[A-Z]", string=password) is None:
            raise WeakPassword("password must contain at least one uppercase letter")
        if re.search(pattern=r"[a-z]", string=password) is None:
            raise WeakPassword("password must contain at least one lowercase letter")
        if re.search(pattern=r"[0-9]", string=password) is None:
            raise WeakPassword("password must contain at least one digit")
        if re.search(pattern=r"[^A-Za-z0-9]", string=password) is None:
            raise WeakPassword("password must contain at least one special character")
