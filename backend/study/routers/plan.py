from fastapi import APIRouter

from ..core.deps import MutateCtx, ViewCtx
from ..schemas.common import Key
from ..schemas.plan import CategoriesInput, PlanInput
from ..services import plan as plan_service

router = APIRouter()


@router.get('/api/plan')
def get_plan(auth: ViewCtx):
    return plan_service.get_plan(auth.db, auth.user, auth.ctx.today())


@router.get('/api/plan/versions/{version}')
def get_plan_version(version: Key, auth: ViewCtx):
    return plan_service.get_plan_version(auth.db, auth.user['id'], version)


@router.put('/api/plan')
def save_plan(payload: PlanInput, auth: MutateCtx):
    timestamp = auth.ctx.now()
    current = auth.ctx.store.date(timestamp).isoformat()
    return plan_service.save_plan(auth.db, auth.user, payload, timestamp, current)


@router.put('/api/categories')
def save_categories(payload: CategoriesInput, auth: MutateCtx):
    return plan_service.save_categories(auth.db, auth.user, payload, auth.ctx.today())
