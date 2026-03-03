from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.domain.models.db.user import User


class UserRepository:
    """
    User repository for persistence operations.

    :param session: database session
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, username: str, email: str, hashed_password: str) -> User:
        """
        Create a new user.

        :param username: unique username
        :param email: unique email
        :param hashed_password: hashed password

        :return: created user
        """
        user = User(username=username, email=email, hashed_password=hashed_password)
        self._session.add(instance=user)
        await self._session.flush()
        return user

    async def get_by_username(self, username: str) -> User | None:
        """
        Find user by username.

        :param username: unique username

        :return: user instance if found
        """
        statement = select(User).where(User.username == username)
        result = await self._session.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Find user by email.

        :param email: unique email

        :return: user instance if found
        """
        statement = select(User).where(User.email == email)
        result = await self._session.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """
        Find user by id.

        :param user_id: unique user id

        :return: user instance if found
        """
        return await self._session.get(entity=User, ident=user_id)

    async def update_password(self, user_id: int, hashed_password: str) -> None:
        """
        Update user password hash.

        :param user_id: unique user id
        :param hashed_password: hashed password
        """
        user = await self.get_by_id(user_id=user_id)
        if user is None:
            return

        user.hashed_password = hashed_password
        self._session.add(instance=user)
        await self._session.flush()
