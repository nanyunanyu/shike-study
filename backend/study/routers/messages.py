from typing import Annotated

from fastapi import APIRouter, Query

from ..core.config import MAX_SAFE_ID
from ..core.deps import DeliveryCtx, MessageID, MutateCtx
from ..services import messages as messages_service

router = APIRouter(prefix='/api/messages')


@router.get('/status')
def message_status(auth: DeliveryCtx):
    return messages_service.status(auth.db, auth.user['id'], auth.ctx.now())


@router.get('')
def message_inbox(
    auth: DeliveryCtx,
    before: Annotated[int | None, Query(gt=0, le=MAX_SAFE_ID)] = None,
):
    return messages_service.inbox(auth.db, auth.user['id'], auth.ctx.now(), before)


@router.post('/preview')
def message_preview(auth: MutateCtx):
    return messages_service.claim_preview(auth.db, auth.user['id'], auth.ctx.now())


@router.put('/{message_id}/read')
def read_message(message_id: MessageID, auth: MutateCtx):
    return messages_service.read(auth.db, auth.user['id'], message_id, auth.ctx.now())


@router.delete('/{message_id}')
def delete_message(message_id: MessageID, auth: MutateCtx):
    messages_service.delete_from_inbox(auth.db, auth.user['id'], message_id, auth.ctx.now())
    return {'ok': True}
