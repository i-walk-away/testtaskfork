import asyncio
import subprocess
import time
from collections.abc import Generator

import httpx
import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from src.app.domain.models.db.base import Base
from src.cfg.cfg import settings


APP_BASE_URL = "http://127.0.0.1:8001"
GRAPHQL_URL = f"{APP_BASE_URL}/api/v1/graphql"
pytestmark = pytest.mark.usefixtures("running_app")


@pytest.fixture(scope="session")
def running_app() -> Generator[None]:
    process = subprocess.Popen(
        args=[
            "uv",
            "run",
            "uvicorn",
            "src.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_healthy()
        yield
    finally:
        process.terminate()
        process.wait(timeout=5)


@pytest.fixture(autouse=True)
def clean_database() -> None:
    _recreate_database()


def _wait_until_healthy() -> None:
    for _ in range(50):
        try:
            response = httpx.get(url=f"{APP_BASE_URL}/health", timeout=1.0)
            if response.status_code == 200 and response.text == "ok":
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    raise RuntimeError


def _recreate_database() -> None:
    async def _run() -> None:
        engine = create_async_engine(url=settings.database_url)
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.drop_all)
                await connection.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    asyncio.run(_run())


def _execute_graphql(
    query: str,
    variables: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    response = httpx.post(
        url=GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers=headers or {},
        timeout=10.0,
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    return payload


def test_graphql_register_login_and_me() -> None:
    unique_suffix = str(int(time.time()))
    username = f"alex_{unique_suffix}"
    email = f"{username}@example.com"

    register_payload = _execute_graphql(
        query="""
            mutation Register($inputData: RegisterInput!) {
              register(inputData: $inputData) {
                accessToken
              }
            }
        """,
        variables={
            "inputData": {
                "username": username,
                "email": email,
                "password": "Verystrongpass1!",
            },
        },
    )
    assert "errors" not in register_payload
    register_token = register_payload["data"]["register"]["accessToken"]
    assert isinstance(register_token, str)
    assert register_token

    login_payload = _execute_graphql(
        query="""
            mutation Login($inputData: LoginInput!) {
              login(inputData: $inputData) {
                accessToken
              }
            }
        """,
        variables={
            "inputData": {
                "username": username,
                "password": "Verystrongpass1!",
            },
        },
    )
    assert "errors" not in login_payload
    access_token = login_payload["data"]["login"]["accessToken"]
    assert isinstance(access_token, str)
    assert access_token

    me_payload = _execute_graphql(
        query="""
            query {
              me {
                id
                username
                email
              }
            }
        """,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert "errors" not in me_payload
    assert me_payload["data"]["me"]["username"] == username
    assert me_payload["data"]["me"]["email"] == email


def test_graphql_password_reset_flow() -> None:
    unique_suffix = str(int(time.time()))
    username = f"alex_{unique_suffix}"
    email = f"{username}@example.com"

    _execute_graphql(
        query="""
            mutation Register($inputData: RegisterInput!) {
              register(inputData: $inputData) {
                accessToken
              }
            }
        """,
        variables={
            "inputData": {
                "username": username,
                "email": email,
                "password": "Verystrongpass1!",
            },
        },
    )

    reset_request_payload = _execute_graphql(
        query="""
            mutation RequestPasswordReset($inputData: RequestPasswordResetInput!) {
              requestPasswordReset(inputData: $inputData) {
                resetToken
              }
            }
        """,
        variables={"inputData": {"email": email}},
    )
    assert "errors" not in reset_request_payload
    reset_token = reset_request_payload["data"]["requestPasswordReset"]["resetToken"]
    assert isinstance(reset_token, str)
    assert reset_token

    reset_payload = _execute_graphql(
        query="""
            mutation ResetPassword($inputData: ConfirmPasswordResetInput!) {
              resetPassword(inputData: $inputData)
            }
        """,
        variables={
            "inputData": {
                "token": reset_token,
                "newPassword": "Newstrongpass2!",
            },
        },
    )
    assert "errors" not in reset_payload
    assert reset_payload["data"]["resetPassword"] is True

    old_password_login = _execute_graphql(
        query="""
            mutation Login($inputData: LoginInput!) {
              login(inputData: $inputData) {
                accessToken
              }
            }
        """,
        variables={
            "inputData": {
                "username": username,
                "password": "Verystrongpass1!",
            },
        },
    )
    assert "errors" in old_password_login

    new_password_login = _execute_graphql(
        query="""
            mutation Login($inputData: LoginInput!) {
              login(inputData: $inputData) {
                accessToken
              }
            }
        """,
        variables={
            "inputData": {
                "username": username,
                "password": "Newstrongpass2!",
            },
        },
    )
    assert "errors" not in new_password_login
    assert new_password_login["data"]["login"]["accessToken"]
