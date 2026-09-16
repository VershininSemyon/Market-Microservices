
class ReviewError(Exception):
    status_code: int = 400
    detail: str = "Ошибка приложения"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class ReviewNotFoundError(ReviewError):
    status_code: int = 404
    detail: str = "Отзыв не найден"


class ReviewAlreadyExistsError(ReviewError):
    status_code: int = 409
    detail: str = "Вы уже оставили отзыв на этот продукт"


class ReviewOwnershipError(ReviewError):
    status_code: int = 403
    detail: str = "Вы не являетесь создателем этого отзыва"


class ProductNotFoundError(ReviewError):
    status_code: int = 404
    detail: str = "Продукт не найден"
