from fastapi import APIRouter

from ..core.deps import MutateCtx, ViewCtx
from ..schemas.backup import Backup, ImportCommit
from ..services import backup as backup_service

router = APIRouter(prefix='/api/backup')


@router.get('')
def export_backup(auth: ViewCtx):
    return backup_service.export_backup(auth.db, auth.user)


@router.post('/preview')
def preview_backup(payload: Backup, auth: ViewCtx):
    return backup_service.preview_backup(payload, auth.user, auth.ctx.store, auth.ctx.today(), auth.ctx.import_secret)


@router.put('')
def import_backup(payload: ImportCommit, auth: MutateCtx):
    timestamp = auth.ctx.now()
    today = auth.ctx.store.date(timestamp).isoformat()
    return backup_service.commit_backup(
        auth.db,
        auth.user,
        payload,
        auth.ctx.store,
        timestamp,
        today,
        auth.ctx.import_secret,
    )
