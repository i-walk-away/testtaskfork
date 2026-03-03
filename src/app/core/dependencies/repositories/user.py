from sqlalchemy.ext.asyncio import AsyncSession

from src.app.domain.repositories.user_repository import UserRepository


def get_user_repository(session: AsyncSession) -> UserRepository:
    """
    Build user repository from database session.

    :param session: async database session

    :return: user repository
    """
    return UserRepository(session=session)
