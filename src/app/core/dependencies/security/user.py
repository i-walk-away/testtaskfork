from fastapi import Request

from src.app.core.exceptions.auth_exc import AuthError


def get_bearer_token(request: Request) -> str:
    """
    Parse bearer token from request headers.

    :param request: http request

    :return: raw jwt token
    """
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        raise AuthError("authorization header is required")

    return authorization.removeprefix("Bearer ")
