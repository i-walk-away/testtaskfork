from sqlalchemy.ext.asyncio import AsyncSession

from src.app.domain.repositories.password_reset_repository import PasswordResetRepository


def get_password_reset_repository(session: AsyncSession) -> PasswordResetRepository:
    """
    Build password reset repository from database session.

    :param session: async database session

    :return: password reset repository
    """
    return PasswordResetRepository(session=session)
