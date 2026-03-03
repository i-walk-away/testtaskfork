from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.app.core.dependencies.security.crypt_context import get_crypt_context
from src.app.core.exceptions.auth_exc import (
    InvalidCredentials,
    InvalidResetToken,
    ResetTokenCooldownExceeded,
    UserAlreadyExists,
    WeakPassword,
)
from src.app.core.security.auth_manager import AuthManager
from src.app.domain.services.auth_service import AuthService


@dataclass(slots=True)
class FakeUser:
    id: int
    username: str
    email: str
    hashed_password: str


@dataclass(slots=True)
class FakeResetToken:
    id: int
    user_id: int
    token_hash: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None


class FakeUserRepository:
    def __init__(self) -> None:
        self._users: dict[int, FakeUser] = {}
        self._next_id = 1

    async def create(self, username: str, email: str, hashed_password: str) -> FakeUser:
        user = FakeUser(
            id=self._next_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
        )
        self._users[user.id] = user
        self._next_id += 1
        return user

    async def get_by_username(self, username: str) -> FakeUser | None:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    async def get_by_email(self, email: str) -> FakeUser | None:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def get_by_id(self, user_id: int) -> FakeUser | None:
        return self._users.get(user_id)

    async def update_password(self, user_id: int, hashed_password: str) -> None:
        user = self._users.get(user_id)
        if user is None:
            return
        user.hashed_password = hashed_password


class FakeResetRepository:
    def __init__(self) -> None:
        self._tokens: dict[int, FakeResetToken] = {}
        self._next_id = 1

    async def create(self, user_id: int, token_hash: str, expires_at: datetime) -> FakeResetToken:
        token = FakeResetToken(
            id=self._next_id,
            user_id=user_id,
            token_hash=token_hash,
            created_at=datetime.now(tz=UTC),
            expires_at=expires_at,
            used_at=None,
        )
        self._tokens[token.id] = token
        self._next_id += 1
        return token

    async def get_latest_for_user(self, user_id: int) -> FakeResetToken | None:
        user_tokens = [token for token in self._tokens.values() if token.user_id == user_id]
        if not user_tokens:
            return None
        return sorted(user_tokens, key=lambda token: token.created_at, reverse=True)[0]

    async def get_active_by_hash(self, token_hash: str) -> FakeResetToken | None:
        now = datetime.now(tz=UTC)
        for token in self._tokens.values():
            if token.token_hash != token_hash:
                continue
            if token.used_at is not None:
                continue
            if token.expires_at < now:
                continue
            return token
        return None

    async def mark_used(self, token_id: int) -> None:
        token = self._tokens.get(token_id)
        if token is None:
            return
        token.used_at = datetime.now(tz=UTC)

    async def invalidate_all_for_user(self, user_id: int) -> None:
        now = datetime.now(tz=UTC)
        for token in self._tokens.values():
            if token.user_id != user_id:
                continue
            if token.used_at is not None:
                continue
            token.used_at = now


@pytest.fixture
def auth_service() -> AuthService:
    user_repository = FakeUserRepository()
    reset_repository = FakeResetRepository()
    auth_manager = AuthManager(context=get_crypt_context())
    return AuthService(
        user_repository=user_repository,
        reset_repository=reset_repository,
        auth_manager=auth_manager,
    )


@pytest.mark.asyncio
async def test_register_and_login_success(auth_service: AuthService) -> None:
    access_token = await auth_service.register(
        username="alex",
        email="alex@example.com",
        password="Verystrongpass1!",
    )

    assert access_token

    login_token = await auth_service.login(username="alex", password="Verystrongpass1!")
    assert login_token


@pytest.mark.asyncio
async def test_register_duplicate_user_fails(auth_service: AuthService) -> None:
    await auth_service.register(
        username="alex",
        email="alex@example.com",
        password="Verystrongpass1!",
    )

    with pytest.raises(expected_exception=UserAlreadyExists):
        await auth_service.register(
            username="alex",
            email="other@example.com",
            password="Verystrongpass1!",
        )


@pytest.mark.asyncio
async def test_login_invalid_credentials(auth_service: AuthService) -> None:
    await auth_service.register(
        username="alex",
        email="alex@example.com",
        password="Verystrongpass1!",
    )

    with pytest.raises(expected_exception=InvalidCredentials):
        await auth_service.login(username="alex", password="wrongpass123")


@pytest.mark.asyncio
async def test_reset_request_has_cooldown(auth_service: AuthService) -> None:
    await auth_service.register(
        username="alex",
        email="alex@example.com",
        password="Verystrongpass1!",
    )
    await auth_service.request_password_reset(email="alex@example.com")

    with pytest.raises(expected_exception=ResetTokenCooldownExceeded):
        await auth_service.request_password_reset(email="alex@example.com")


@pytest.mark.asyncio
async def test_reset_password_token_is_single_use(auth_service: AuthService) -> None:
    await auth_service.register(
        username="alex",
        email="alex@example.com",
        password="Verystrongpass1!",
    )
    token = await auth_service.request_password_reset(email="alex@example.com")

    await auth_service.reset_password(token=token, new_password="Newstrongpass2!")

    with pytest.raises(expected_exception=InvalidResetToken):
        await auth_service.reset_password(token=token, new_password="Otherstrongpass3!")


@pytest.mark.asyncio
async def test_reset_password_allows_login_with_new_password(
    auth_service: AuthService,
) -> None:
    await auth_service.register(
        username="alex",
        email="alex@example.com",
        password="Verystrongpass1!",
    )
    token = await auth_service.request_password_reset(email="alex@example.com")

    await auth_service.reset_password(token=token, new_password="Newstrongpass2!")

    with pytest.raises(expected_exception=InvalidCredentials):
        await auth_service.login(username="alex", password="Verystrongpass1!")

    fresh_token = await auth_service.login(username="alex", password="Newstrongpass2!")
    assert fresh_token


@pytest.mark.asyncio
async def test_register_weak_password_fails(auth_service: AuthService) -> None:
    with pytest.raises(expected_exception=WeakPassword):
        await auth_service.register(
            username="alex",
            email="alex@example.com",
            password="weakpass",
        )


@pytest.mark.asyncio
async def test_request_reset_for_unknown_email_is_enumeration_safe(
    auth_service: AuthService,
) -> None:
    token = await auth_service.request_password_reset(email="unknown@example.com")
    assert token


@pytest.mark.asyncio
async def test_new_reset_request_invalidates_old_token() -> None:
    user_repository = FakeUserRepository()
    reset_repository = FakeResetRepository()
    service = AuthService(
        user_repository=user_repository,
        reset_repository=reset_repository,
        auth_manager=AuthManager(context=get_crypt_context()),
    )

    await service.register(
        username="alex",
        email="alex@example.com",
        password="Verystrongpass1!",
    )
    old_token = await service.request_password_reset(email="alex@example.com")

    latest = await reset_repository.get_latest_for_user(user_id=1)
    assert latest is not None
    latest.created_at = datetime.now(tz=UTC).replace(year=2000)

    _ = await service.request_password_reset(email="alex@example.com")

    with pytest.raises(expected_exception=InvalidResetToken):
        await service.reset_password(token=old_token, new_password="Otherstrongpass3!")
