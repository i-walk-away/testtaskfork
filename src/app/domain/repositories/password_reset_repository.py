from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.domain.models.db.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    """
    Password reset token repository.

    :param session: database session
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: int, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        """
        Create reset token record.

        :param user_id: user id
        :param token_hash: reset token hash
        :param expires_at: token expiration date

        :return: created reset token
        """
        token = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self._session.add(instance=token)
        await self._session.flush()
        return token

    async def get_latest_for_user(self, user_id: int) -> PasswordResetToken | None:
        """
        Fetch latest reset token for user.

        :param user_id: user id

        :return: latest reset token if found
        """
        statement = (
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .order_by(desc(PasswordResetToken.created_at))
            .limit(1)
        )
        result = await self._session.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_active_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        """
        Fetch active reset token by hash.

        :param token_hash: reset token hash

        :return: token if active and valid
        """
        now = datetime.now(tz=UTC)
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at >= now,
        )
        result = await self._session.execute(statement=statement)
        return result.scalar_one_or_none()

    async def mark_used(self, token_id: int) -> None:
        """
        Mark token as used.

        :param token_id: unique token id
        """
        token = await self._session.get(entity=PasswordResetToken, ident=token_id)
        if token is None:
            return

        token.used_at = datetime.now(tz=UTC)
        self._session.add(instance=token)
        await self._session.flush()

    async def invalidate_all_for_user(self, user_id: int) -> None:
        """
        Mark all active user tokens as used.

        :param user_id: unique user id
        """
        now = datetime.now(tz=UTC)
        statement = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
        result = await self._session.execute(statement=statement)
        tokens = result.scalars().all()
        for token in tokens:
            token.used_at = now
            self._session.add(instance=token)

        await self._session.flush()
