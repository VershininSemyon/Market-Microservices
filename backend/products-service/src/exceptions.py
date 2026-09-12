
class ProductError(Exception):
    status_code: int = 400
    detail: str = "Ошибка приложения"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


###
class ProductNotFoundError(ProductError):
    status_code: int = 404
    detail: str = "Продукт не найден"


class ProductAlreadyExistsError(ProductError):
    status_code: int = 400
    detail: str = "Продукт с таким названием уже существует"
