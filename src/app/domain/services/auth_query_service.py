from src.app.core.exceptions.auth_exc import InvalidCredentials, UserNotFound
from src.app.core.security.auth_manager import AuthManager
from src.app.domain.models.db.user import User
from src.app.domain.repositories.user_repository import UserRepository


class AuthQueryService:
    """
    Query side service for auth reads.

    :param user_repository: user repository
    :param auth_manager: auth manager
    """

    def __init__(self, user_repository: UserRepository, auth_manager: AuthManager) -> None:
        self._user_repository = user_repository
        self._auth_manager = auth_manager

    async def get_me(self, token: str) -> User:
        """
        Resolve current user by jwt.

        :param token: jwt access token

        :return: user model
        """
        payload = self._auth_manager.decode_jwt(token=token)
        subject = payload.get("sub")
        if subject is None:
            raise InvalidCredentials("invalid token")

        user = await self._user_repository.get_by_id(user_id=int(subject))
        if user is None:
            raise UserNotFound("user not found")

        return user
