from fastapi import APIRouter, Request, Response

from ..core.deps import AppCtx, AuthReadCtx, AuthWriteCtx, MutateCtx
from ..schemas.auth import ChangePassword, Login, Preferences
from ..services import auth as auth_service

router = APIRouter()


@router.get('/api/status')
def status(ctx: AppCtx):
    return dict(initialized=auth_service.is_initialized(ctx.store))


@router.post('/api/auth/login')
def login(payload: Login, request: Request, response: Response, ctx: AppCtx):
    old_cookie = request.cookies.get(ctx.settings.cookie_name)
    token, body = auth_service.login(ctx, payload, old_cookie)
    response.set_cookie(
        ctx.settings.cookie_name,
        token,
        max_age=ctx.settings.session_age,
        httponly=True,
        samesite='strict',
        secure=request.url.scheme == 'https',
    )
    return body


@router.get('/api/auth/me')
def me(auth: AuthReadCtx):
    return auth_service.build_bootstrap(auth.user, auth.user['csrf'], auth.ctx.today(), auth.ctx.store.zone.key)


@router.post('/api/auth/logout')
def logout(response: Response, auth: AuthWriteCtx):
    auth_service.logout(auth.db, auth.user)
    response.delete_cookie(auth.ctx.settings.cookie_name, httponly=True, samesite='strict')
    return {'ok': True}


@router.post('/api/auth/password')
def change_password(payload: ChangePassword, auth: AuthWriteCtx):
    return auth_service.change_password(auth.db, auth.user, payload, auth.ctx.today(), auth.ctx.store.zone.key)


@router.put('/api/preferences')
def update_preferences(payload: Preferences, auth: MutateCtx):
    return auth_service.update_preferences(auth.db, auth.user['id'], payload)
