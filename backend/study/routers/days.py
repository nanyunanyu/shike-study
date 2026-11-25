from datetime import date

from fastapi import APIRouter

from ..core.deps import MutateCtx, ViewCtx
from ..schemas.common import Key, Times
from ..schemas.days import AdhocTaskInput, Review, Toggle
from ..services import days as days_service

router = APIRouter(prefix='/api/days')


@router.get('/{day}')
def day_get(day: date, auth: ViewCtx):
    return days_service.get_day_for_date(auth.db, auth.user['id'], day, auth.ctx.today())


@router.post('/{day}/tasks', status_code=201)
def add_adhoc_task(day: date, payload: AdhocTaskInput, auth: MutateCtx):
    return days_service.add_adhoc_task(auth.db, auth.user, day, payload, auth.ctx.today())


@router.put('/{day}/tasks/{task_id}')
def edit_adhoc_task(day: date, task_id: Key, payload: AdhocTaskInput, auth: MutateCtx):
    return days_service.edit_adhoc_task(auth.db, auth.user, day, task_id, payload, auth.ctx.today())


@router.delete('/{day}/tasks/{task_id}')
def delete_adhoc_task(day: date, task_id: Key, auth: MutateCtx):
    return days_service.delete_adhoc_task(auth.db, auth.user['id'], day, task_id, auth.ctx.today())


@router.put('/{day}/tasks/{task_id}/done')
def toggle_done(day: date, task_id: Key, payload: Toggle, auth: MutateCtx):
    return days_service.toggle_task_done(auth.db, auth.user['id'], day, task_id, payload.done, auth.ctx.today())


@router.put('/{day}/tasks/{task_id}/times')
def override_times(day: date, task_id: Key, auth: MutateCtx, payload: Times | None = None):
    return days_service.override_task_times(auth.db, auth.user['id'], day, task_id, payload, auth.ctx.today())


@router.put('/{day}/review')
def save_review(day: date, payload: Review, auth: MutateCtx):
    return days_service.save_review(auth.db, auth.user['id'], day, payload, auth.ctx.today())


@router.post('/{day}/check-in')
def check_in(day: date, auth: MutateCtx):
    timestamp = auth.ctx.now()
    current = auth.ctx.store.date(timestamp).isoformat()
    return days_service.check_in(auth.db, auth.user['id'], day, timestamp, current)


@router.delete('/{day}/check-in')
def undo_check_in(day: date, auth: MutateCtx):
    return days_service.undo_check_in(auth.db, auth.user['id'], day, auth.ctx.today())
