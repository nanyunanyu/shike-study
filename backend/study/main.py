import asyncio
import logging
import time
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from .core.config import BACKEND_ROOT, Settings
from .core.context import AppContext
from .core.exceptions import register_exception_handlers
from .core.middleware import register_middlewares
from .core.security import hash_password, new_secret_bytes, new_token
from .db.connection import Store
from .routers import register_routers
from .services.maintenance import run_maintenance

ROOT = BACKEND_ROOT
log = logging.getLogger(__name__)


def create_app(directory=None, clock=time.time) -> FastAPI:
    settings = Settings.from_env(directory)
    store = Store(settings.data_dir)
    ctx = AppContext(
        store=store,
        settings=settings,
        clock=clock,
        dummy_hash=hash_password(new_token()),
        import_secret=new_secret_bytes(32),
    )

    @asynccontextmanager
    async def lifespan(_):
        store.initialize(settings.timezone)
        await asyncio.to_thread(run_maintenance, store, ctx.now())

        async def tick():
            while True:
                await asyncio.sleep(settings.maintenance_interval)
                try:
                    await asyncio.to_thread(run_maintenance, store, ctx.now())
                except Exception:
                    log.exception('定时维护失败')

        worker = asyncio.create_task(tick())
        try:
            yield
        finally:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker

    app = FastAPI(title='拾刻学习', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.ctx = ctx
    app.state.store = store

    register_middlewares(app, settings)
    register_exception_handlers(app)
    register_routers(app, settings)
    return app


app = create_app()
