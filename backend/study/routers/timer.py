from fastapi import APIRouter

from ..core.deps import MutateCtx
from ..schemas.timer import TimerAction, TimerStart
from ..services import timer as timer_service

router = APIRouter(prefix='/api/timer')


@router.get('')
def get_timer(auth: MutateCtx):
    timestamp = auth.ctx.now()
    today = auth.ctx.store.date(timestamp).isoformat()
    state = timer_service.current_state(auth.db, auth.user['id'], timestamp)
    return timer_service.timer_response(state, timestamp, today)


@router.post('/start')
def start_timer(payload: TimerStart, auth: MutateCtx):
    timestamp = auth.ctx.now()
    today = auth.ctx.store.date(timestamp).isoformat()
    state = timer_service.start(auth.db, auth.user, payload, timestamp, today)
    return timer_service.timer_response(state, timestamp, today)


@router.post('/action')
def act_timer(payload: TimerAction, auth: MutateCtx):
    timestamp = auth.ctx.now()
    today = auth.ctx.store.date(timestamp).isoformat()
    state = timer_service.act(auth.db, auth.user['id'], payload, timestamp)
    return timer_service.timer_response(state, timestamp, today)
