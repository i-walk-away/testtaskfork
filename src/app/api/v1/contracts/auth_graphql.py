import strawberry


@strawberry.type
class TokenOutput:
    access_token: str


@strawberry.type
class ResetTokenOutput:
    reset_token: str


@strawberry.type
class UserOutput:
    id: int
    username: str
    email: str


@strawberry.input
class RegisterInput:
    username: str
    email: str
    password: str


@strawberry.input
class LoginInput:
    username: str
    password: str


@strawberry.input
class RequestPasswordResetInput:
    email: str


@strawberry.input
class ConfirmPasswordResetInput:
    token: str
    new_password: str
