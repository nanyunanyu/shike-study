from dataclasses import dataclass
import sqlite3
from typing import Annotated

from fastapi import Depends, Path as PathParam, Request

from .config import MAX_SAFE_ID
from .context import AppContext
from ..services import auth as auth_service

MessageID = Annotated[int, PathParam(gt=0, le=MAX_SAFE_ID)]


@dataclass
class AuthContext:
    db: sqlite3.Connection
    user: sqlite3.Row
    ctx: AppContext


def get_app_context(request: Request) -> AppContext:
    return request.app.state.ctx


def _authenticate(db: sqlite3.Connection, request: Request, ctx: AppContext, *, allow_change: bool = False, admin: bool = False):
    return auth_service.authenticate_session(
        db,
        token=request.cookies.get(ctx.settings.cookie_name, ''),
        method=request.method,
        csrf_header=request.headers.get('x-csrf-token', ''),
        now=ctx.now(),
        allow_change=allow_change,
        admin=admin,
    )


def get_view_ctx(request: Request):
    ctx = get_app_context(request)
    with ctx.store.transaction(read=True) as db:
        yield AuthContext(db=db, user=_authenticate(db, request, ctx), ctx=ctx)


def get_mutate_ctx(request: Request):
    ctx = get_app_context(request)
    with ctx.store.transaction(write=True) as db:
        yield AuthContext(db=db, user=_authenticate(db, request, ctx), ctx=ctx)


def get_delivery_ctx(request: Request):
    ctx = get_app_context(request)
    with ctx.store.transaction(write=True) as db:
        yield AuthContext(db=db, user=_authenticate(db, request, ctx), ctx=ctx)


def get_admin_view_ctx(request: Request):
    ctx = get_app_context(request)
    with ctx.store.transaction(read=True) as db:
        yield AuthContext(db=db, user=_authenticate(db, request, ctx, admin=True), ctx=ctx)


def get_admin_mutate_ctx(request: Request):
    ctx = get_app_context(request)
    with ctx.store.transaction(write=True) as db:
        yield AuthContext(db=db, user=_authenticate(db, request, ctx, admin=True), ctx=ctx)


def get_auth_read_ctx(request: Request):
    ctx = get_app_context(request)
    with ctx.store.transaction(read=True) as db:
        yield AuthContext(db=db, user=_authenticate(db, request, ctx, allow_change=True), ctx=ctx)


def get_auth_write_ctx(request: Request):
    ctx = get_app_context(request)
    with ctx.store.transaction(write=True) as db:
        yield AuthContext(db=db, user=_authenticate(db, request, ctx, allow_change=True), ctx=ctx)


AppCtx = Annotated[AppContext, Depends(get_app_context)]
ViewCtx = Annotated[AuthContext, Depends(get_view_ctx, scope='function')]
MutateCtx = Annotated[AuthContext, Depends(get_mutate_ctx, scope='function')]
DeliveryCtx = Annotated[AuthContext, Depends(get_delivery_ctx, scope='function')]
AdminViewCtx = Annotated[AuthContext, Depends(get_admin_view_ctx, scope='function')]
AdminMutateCtx = Annotated[AuthContext, Depends(get_admin_mutate_ctx, scope='function')]
AuthReadCtx = Annotated[AuthContext, Depends(get_auth_read_ctx, scope='function')]
AuthWriteCtx = Annotated[AuthContext, Depends(get_auth_write_ctx, scope='function')]
