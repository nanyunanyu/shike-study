class DomainError(Exception):
    """框架无关的领域异常基类，由全局异常处理器统一转换为 HTTP JSON 响应。"""

    def __init__(self, status_code: int, detail: str, headers: dict[str, str] | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.headers = headers


class BadRequestError(DomainError):
    def __init__(self, detail: str):
        super().__init__(400, detail)


class UnauthorizedError(DomainError):
    def __init__(self, detail: str):
        super().__init__(401, detail)


class ForbiddenError(DomainError):
    def __init__(self, detail: str):
        super().__init__(403, detail)


class NotFoundError(DomainError):
    def __init__(self, detail: str):
        super().__init__(404, detail)


class ConflictError(DomainError):
    def __init__(self, detail: str):
        super().__init__(409, detail)


class ValidationDomainError(DomainError):
    def __init__(self, detail: str):
        super().__init__(422, detail)


class RateLimitError(DomainError):
    def __init__(self, detail: str, retry_after: int):
        super().__init__(429, detail, headers={'Retry-After': str(retry_after)})


def register_exception_handlers(app) -> None:
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    @app.exception_handler(DomainError)
    async def domain_error_handler(_, error: DomainError):
        return JSONResponse({'detail': error.detail}, status_code=error.status_code, headers=error.headers)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_, error: RequestValidationError):
        return JSONResponse(
            {'detail': '输入或备份格式不正确', 'fields': [list(e['loc']) for e in error.errors()[:10]]},
            status_code=422,
        )

    @app.exception_handler(OverflowError)
    async def invalid_timestamp(_, _error: OverflowError):
        return JSONResponse({'detail': '日期超出有效范围'}, status_code=422)
