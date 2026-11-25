from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from ..core.deps import ViewCtx
from ..schemas.common import Issue, Mood
from ..services import reviews as reviews_service

router = APIRouter()


@router.get('/api/reviews')
def reviews_timeline(
    auth: ViewCtx,
    mood: Mood | None = None,
    issue: Issue | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    before: date | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    return reviews_service.list_reviews(
        auth.db,
        auth.user['id'],
        auth.ctx.today(),
        mood=mood,
        issue=issue,
        query=q,
        before=before.isoformat() if before else None,
        limit=limit,
    )
