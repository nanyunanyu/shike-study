from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings


def register_middlewares(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))

    @app.middleware('http')
    async def policy(request, call_next):
        if request.url.path.startswith('/api/') and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            host = request.headers.get('host', '').lower()
            origin = request.headers.get('origin')
            if origin and urlsplit(origin).netloc.lower() not in settings.public_origins | {host}:
                return JSONResponse({'detail': '请求来源不匹配'}, status_code=403)
            if request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail': '拒绝跨站请求'}, status_code=403)
            try:
                raw_size = int(request.headers.get('content-length', '0'))
            except ValueError:
                return JSONResponse({'detail': '请求长度无效'}, status_code=400)
            if (
                raw_size < 0
                or raw_size > settings.max_body_bytes
                or (request.headers.get('transfer-encoding') and not raw_size)
            ):
                return JSONResponse({'detail': '请求过大或缺少长度'}, status_code=413)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response
