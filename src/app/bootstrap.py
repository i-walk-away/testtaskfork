import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from jwt import InvalidTokenError

from src.app.api.v1 import router as api_router
from src.app.core.dependencies.db import SessionLocal, engine
from src.app.core.exceptions.auth_exc import AuthError
from src.app.domain.models.db.base import Base
from src.app.domain.models.db.password_reset_token import PasswordResetToken
from src.app.domain.models.db.user import User


logger = logging.getLogger(name="auth_challenge")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Handle application lifespan events.

    :param _: application instance

    :return: lifespan iterator
    """
    _ = User, PasswordResetToken
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    """
    Build and configure FastAPI application.

    :return: configured application instance
    """
    app = FastAPI(title="Auth Challenge", lifespan=lifespan)
    app.include_router(router=api_router, prefix="/api/v1")

    register_middleware(app=app)
    register_routes(app=app)
    register_exception_handlers(app=app)

    return app


def register_middleware(app: FastAPI) -> None:
    """
    Register HTTP middleware.

    :param app: application instance
    """

    @app.middleware("http")
    async def db_session_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Attach database session per request.

        :param request: http request
        :param call_next: next middleware callback

        :return: http response
        """
        request.state.db = SessionLocal()
        try:
            response = await call_next(request)
            await request.state.db.commit()
            return response
        except Exception:
            await request.state.db.rollback()
            raise
        finally:
            await request.state.db.close()

    @app.middleware("http")
    async def logging_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Log request latency for basic observability.

        :param request: http request
        :param call_next: next middleware callback

        :return: http response
        """
        started_at = perf_counter()
        response = await call_next(request)
        elapsed_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "request path=%s method=%s status=%s duration_ms=%s",
            request.url.path,
            request.method,
            response.status_code,
            elapsed_ms,
        )
        return response


def register_routes(app: FastAPI) -> None:
    """
    Register lightweight technical routes.

    :param app: application instance
    """

    @app.get(path="/health")
    async def healthcheck() -> PlainTextResponse:
        """
        Return healthcheck response.

        :return: health status
        """
        return PlainTextResponse(content="ok")


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers.

    :param app: application instance
    """

    @app.exception_handler(exc_class_or_status_code=AuthError)
    def auth_error_handler(_: Request, exc: AuthError) -> JSONResponse:
        """
        Return json response for auth domain exceptions.

        :param _: request object
        :param exc: raised exception

        :return: json response
        """
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(exc_class_or_status_code=InvalidTokenError)
    def invalid_token_handler(_: Request, exc: InvalidTokenError) -> JSONResponse:
        """
        Return json response for invalid jwt token.

        :param _: request object
        :param exc: raised exception

        :return: json response
        """
        return JSONResponse(status_code=401, content={"detail": str(exc)})


app = create_app()
