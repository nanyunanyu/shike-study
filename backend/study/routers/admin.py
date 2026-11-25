from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Query

from ..core.config import MAX_SAFE_ID
from ..core.deps import AdminMutateCtx, AdminViewCtx, MessageID
from ..schemas.admin import NewUser, ResetPassword, UserActive
from ..schemas.messages import NewDispatch, NewMessage
from ..services import admin as admin_service

router = APIRouter(prefix='/api/admin')


@router.get('/overview')
def admin_overview(auth: AdminViewCtx):
    timestamp = auth.ctx.now()
    return admin_service.overview(auth.db, auth.user['id'], auth.ctx.store.date(timestamp), timestamp)


@router.get('/dispatches')
def admin_dispatches(
    auth: AdminViewCtx,
    status: Literal['pending', 'sent', 'canceled'] = 'pending',
    kind: Literal['reminder', 'encouragement'] | None = None,
    recipient_id: Annotated[int | None, Query(gt=0, le=MAX_SAFE_ID)] = None,
    cursor: Annotated[str | None, Query(max_length=64)] = None,
):
    return admin_service.dispatches(auth.db, auth.user['id'], auth.ctx.now(), status, kind, recipient_id, cursor)


@router.post('/dispatches', status_code=201)
def admin_send(payload: NewDispatch, auth: AdminMutateCtx):
    return admin_service.send_dispatch(auth.db, auth.user['id'], payload, auth.ctx.store.zone, auth.ctx.now())


@router.get('/dispatches/{key}')
def admin_dispatch(key: str, auth: AdminViewCtx):
    return admin_service.dispatch_detail(auth.db, auth.user['id'], key, auth.ctx.now())


@router.delete('/dispatches/{key}')
def admin_cancel_dispatch(key: str, auth: AdminMutateCtx):
    return admin_service.cancel_dispatch(auth.db, auth.user['id'], key, auth.ctx.now())


@router.get('/users')
def list_users(auth: AdminViewCtx):
    return admin_service.list_users(auth.db)


@router.post('/users', status_code=201)
def create_user(payload: NewUser, auth: AdminMutateCtx):
    timestamp = auth.ctx.now()
    return admin_service.create_student(auth.db, payload, auth.ctx.store.date(timestamp).isoformat(), timestamp)


@router.put('/users/{uid}/active')
def update_user_active(uid: int, payload: UserActive, auth: AdminMutateCtx):
    return admin_service.set_user_active(auth.db, uid, payload)


@router.put('/users/{uid}/password')
def reset_user_password(uid: int, payload: ResetPassword, auth: AdminMutateCtx):
    return admin_service.reset_user_password(auth.db, uid, payload)


@router.delete('/users/{uid}')
def delete_user(uid: int, auth: AdminMutateCtx):
    admin_service.delete_user(auth.db, uid)
    return {'ok': True}


@router.get('/users/{uid}/day/{day}')
def admin_user_day(uid: int, day: date, auth: AdminViewCtx):
    return admin_service.get_user_day(auth.db, uid, day, auth.ctx.today())


@router.get('/users/{uid}/plan')
def admin_user_plan(uid: int, auth: AdminViewCtx):
    return admin_service.get_user_plan(auth.db, uid, auth.ctx.today())


@router.get('/users/{uid}/statistics')
def admin_user_statistics(uid: int, auth: AdminViewCtx, start: date | None = None, end: date | None = None):
    return admin_service.get_user_statistics(auth.db, uid, auth.ctx.today(), start, end)


@router.get('/users/{uid}/messages/sent')
def sent_messages(
    uid: int,
    auth: AdminViewCtx,
    before: Annotated[int | None, Query(gt=0, le=MAX_SAFE_ID)] = None,
):
    return admin_service.list_user_sent_messages(auth.db, auth.user['id'], uid, auth.ctx.now(), before)


@router.get('/users/{uid}/messages')
def pending_messages(uid: int, auth: AdminViewCtx):
    return admin_service.list_user_pending_messages(auth.db, auth.user['id'], uid, auth.ctx.now())


@router.post('/users/{uid}/messages', status_code=201)
def create_message(uid: int, payload: NewMessage, auth: AdminMutateCtx):
    return admin_service.send_user_message(auth.db, auth.user['id'], uid, payload, auth.ctx.store.zone, auth.ctx.now())


@router.delete('/users/{uid}/messages/{message_id}')
def cancel_message(uid: int, message_id: MessageID, auth: AdminMutateCtx):
    admin_service.cancel_user_message(auth.db, auth.user['id'], uid, message_id, auth.ctx.now())
    return {'ok': True}
