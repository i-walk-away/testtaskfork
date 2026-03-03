class AuthError(Exception):
    """
    Base authentication exception.

    :param self: exception instance
    """


class UserAlreadyExists(AuthError):
    """
    Raised when username or email already exists.

    :param self: exception instance
    """


class InvalidCredentials(AuthError):
    """
    Raised when credentials are invalid.

    :param self: exception instance
    """


class UserNotFound(AuthError):
    """
    Raised when user does not exist.

    :param self: exception instance
    """


class ResetTokenCooldownExceeded(AuthError):
    """
    Raised when reset token is requested too often.

    :param self: exception instance
    """


class InvalidResetToken(AuthError):
    """
    Raised when reset token is invalid, expired or already used.

    :param self: exception instance
    """


class WeakPassword(AuthError):
    """
    Raised when password does not satisfy policy.

    :param self: exception instance
    """
