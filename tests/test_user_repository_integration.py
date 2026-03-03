import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.app.domain.models.db.base import Base
from src.app.domain.models.db.user import User
from src.app.domain.repositories.user_repository import UserRepository
from src.cfg.cfg import settings


@pytest.mark.asyncio
async def test_user_repository_create_and_get() -> None:
    engine = create_async_engine(url=settings.database_url)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        repository = UserRepository(session=session)
        created = await repository.create(
            username="alex",
            email="alex@example.com",
            hashed_password="hashed",
        )
        await session.commit()

        fetched = await repository.get_by_username(username="alex")

        assert created.id > 0
        assert fetched is not None
        assert fetched.email == "alex@example.com"

    async with session_factory() as verification_session:
        stored = await verification_session.get(entity=User, ident=1)
        assert stored is not None

    await engine.dispose()
