from datetime import date

from fastapi import APIRouter

from ..core.deps import ViewCtx
from ..services import stats as stats_service

router = APIRouter()


@router.get('/api/statistics')
def get_statistics(auth: ViewCtx, start: date | None = None, end: date | None = None):
    return stats_service.get_statistics(auth.db, auth.user['id'], auth.ctx.today(), start, end)
