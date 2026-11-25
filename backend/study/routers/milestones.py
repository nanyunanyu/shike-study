from fastapi import APIRouter

from ..core.deps import MutateCtx, ViewCtx
from ..schemas.common import Key
from ..schemas.milestones import MilestoneInput, MilestoneUpdate
from ..services import milestones as milestones_service

router = APIRouter(prefix='/api/milestones')


@router.get('')
def list_milestones(auth: ViewCtx):
    return milestones_service.list_milestones(auth.db, auth.user['id'], auth.ctx.today())


@router.post('', status_code=201)
def create_milestone(payload: MilestoneInput, auth: MutateCtx):
    timestamp = auth.ctx.now()
    current = auth.ctx.store.date(timestamp).isoformat()
    return milestones_service.create_milestone(auth.db, auth.user['id'], payload, timestamp, current)


@router.put('/{milestone_id}')
def update_milestone(milestone_id: Key, payload: MilestoneUpdate, auth: MutateCtx):
    return milestones_service.update_milestone(auth.db, auth.user['id'], milestone_id, payload, auth.ctx.today())


@router.delete('/{milestone_id}')
def delete_milestone(milestone_id: Key, auth: MutateCtx):
    milestones_service.delete_milestone(auth.db, auth.user['id'], milestone_id)
    return {'ok': True}
