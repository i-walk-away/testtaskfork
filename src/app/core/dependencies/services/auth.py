from fastapi import Request

from src.app.core.dependencies.repositories.password_reset import get_password_reset_repository
from src.app.core.dependencies.repositories.user import get_user_repository
from src.app.core.dependencies.security.auth_manager import get_auth_manager
from src.app.domain.services.auth_query_service import AuthQueryService
from src.app.domain.services.auth_service import AuthService


def get_auth_service(request: Request) -> AuthService:
    """
    Build auth command service from request dependencies.

    :param request: http request

    :return: auth service
    """
    db_session = request.state.db
    user_repository = get_user_repository(session=db_session)
    reset_repository = get_password_reset_repository(session=db_session)
    auth_manager = get_auth_manager()

    return AuthService(
        user_repository=user_repository,
        reset_repository=reset_repository,
        auth_manager=auth_manager,
    )


def get_auth_query_service(request: Request) -> AuthQueryService:
    """
    Build auth query service from request dependencies.

    :param request: http request

    :return: auth query service
    """
    db_session = request.state.db
    user_repository = get_user_repository(session=db_session)
    auth_manager = get_auth_manager()

    return AuthQueryService(user_repository=user_repository, auth_manager=auth_manager)
