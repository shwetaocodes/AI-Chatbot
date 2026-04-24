from fastapi import HTTPException


class AppException(HTTPException):
    """
    Base exception for all application errors.
    Adds a typed error_code to standard HTTPException.

    Usage:
        raise AppException(
            status_code=400,
            error_code="EMAIL_TAKEN",
            message="This email is already registered.",
        )
    """
    def __init__(self, status_code: int, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(status_code=status_code, detail=message)



class EmailTakenError(AppException):
    def __init__(self):
        super().__init__(
            status_code=400,
            error_code="EMAIL_TAKEN",
            message="This email is already registered.",
        )


class InvalidCredentialsError(AppException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
        )


class AccountDisabledError(AppException):
    def __init__(self):
        super().__init__(
            status_code=403,
            error_code="ACCOUNT_DISABLED",
            message="This account has been disabled.",
        )


class InvalidTokenError(AppException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code="INVALID_TOKEN",
            message="Invalid or expired token.",
        )


class InvalidRefreshTokenError(AppException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code="INVALID_REFRESH_TOKEN",
            message="Invalid or expired refresh token.",
        )


class TokenRevokedError(AppException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code="TOKEN_REVOKED",
            message="This token has already been revoked.",
        )