
class AuthError(Exception):
    status_code: int = 400
    detail: str = "Ошибка приложения"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


###
class TokenDecodeError(AuthError):
    status_code: int = 401
    detail: str = "Ошибка декодирования токена"


class TokenExpiredError(TokenDecodeError):
    status_code: int = 401
    detail: str = "Токен просрочен"


class InvalidTokenTypeError(TokenDecodeError):
    status_code: int = 401
    detail: str = "Неверный тип токена"


class InvalidTokenError(TokenDecodeError):
    status_code: int = 401
    detail: str = "Недействительный токен"


###
class TokenBlacklistError(AuthError):
    status_code = 401
    detail: str = "Токен в чёрном списке"


###
class InvalidUserDataError(AuthError):
    status_code: int = 401
    detail: str = "Неверные учётные данные"


class UserNotFoundError(InvalidUserDataError):
    status_code: int = 401
    detail: str = "Пользователь не найден"


class InvalidPasswordError(InvalidUserDataError):
    status_code: int = 401
    detail: str = "Неверный пароль"


###
class UserCreateError(AuthError):
    status_code: int = 400
    detail: str = "Ошибка создания пользователя"


class UsernameAlreadyExistsError(UserCreateError):
    status_code: int = 400
    detail: str = "Пользователь с таким username уже существует"


class EmailAlreadyExistsError(UserCreateError):
    status_code: int = 400
    detail: str = "Пользователь с таким email уже существует"
