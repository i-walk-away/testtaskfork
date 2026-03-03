import strawberry
from fastapi import Request

from src.app.api.v1.contracts.auth_graphql import (
    ConfirmPasswordResetInput,
    LoginInput,
    RegisterInput,
    RequestPasswordResetInput,
    ResetTokenOutput,
    TokenOutput,
    UserOutput,
)
from src.app.core.dependencies.security.user import get_bearer_token
from src.app.core.dependencies.services.auth import (get_auth_query_service, get_auth_service)


@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: strawberry.Info) -> UserOutput:
        """
        Return authenticated user profile.

        :param info: graphql resolver info

        :return: user output
        """
        request = _get_request(info=info)
        token = get_bearer_token(request=request)
        service = get_auth_query_service(request=request)
        user = await service.get_me(token=token)
        return UserOutput(id=user.id, username=user.username, email=user.email)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def register(self, info: strawberry.Info, input_data: RegisterInput) -> TokenOutput:
        """
        Register user and return access token.

        :param info: graphql resolver info
        :param input_data: registration payload

        :return: token output
        """
        request = _get_request(info=info)
        service = get_auth_service(request=request)
        access_token = await service.register(
            username=input_data.username,
            email=input_data.email,
            password=input_data.password,
        )
        return TokenOutput(access_token=access_token)

    @strawberry.mutation
    async def login(self, info: strawberry.Info, input_data: LoginInput) -> TokenOutput:
        """
        Login user and return access token.

        :param info: graphql resolver info
        :param input_data: login payload

        :return: token output
        """
        request = _get_request(info=info)
        service = get_auth_service(request=request)
        access_token = await service.login(username=input_data.username, password=input_data.password)
        return TokenOutput(access_token=access_token)

    @strawberry.mutation
    async def request_password_reset(
            self,
            info: strawberry.Info,
            input_data: RequestPasswordResetInput,
    ) -> ResetTokenOutput:
        """
        Issue password reset token.

        :param info: graphql resolver info
        :param input_data: reset request payload

        :return: reset token output
        """
        request = _get_request(info=info)
        service = get_auth_service(request=request)
        reset_token = await service.request_password_reset(email=input_data.email)
        return ResetTokenOutput(reset_token=reset_token)

    @strawberry.mutation
    async def reset_password(self, info: strawberry.Info, input_data: ConfirmPasswordResetInput) -> bool:
        """
        Reset password by token.

        :param info: graphql resolver info
        :param input_data: reset confirmation payload

        :return: operation result
        """
        request = _get_request(info=info)
        service = get_auth_service(request=request)
        await service.reset_password(token=input_data.token, new_password=input_data.new_password)
        return True


def _get_request(info: strawberry.Info) -> Request:
    """
    Extract HTTP request from resolver context.

    :param info: graphql resolver info

    :return: http request
    """
    return info.context["request"]


def build_schema() -> strawberry.Schema:
    """
    Build graphql schema.

    :return: graphql schema
    """
    return strawberry.Schema(query=Query, mutation=Mutation)
