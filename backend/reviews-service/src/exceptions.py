
class ReviewError(Exception):
    status_code: int = 400
    detail: str = "Ошибка приложения"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)
