
class OrderError(Exception):
    status_code: int = 400
    detail: str = "Ошибка приложения"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


###
class OrderNotFoundError(OrderError):
    status_code: int = 404
    detail: str = "Заказ не найден"


class OrderOwnershipError(OrderError):
    status_code: int = 403
    detail: str = "Вы не являетесь создателем этого заказа"
