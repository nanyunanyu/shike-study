from datetime import date

from ..core.exceptions import NotFoundError, ValidationDomainError
from ..core.security import new_key
from ..db.repositories import milestones as milestones_repo
from ..schemas.milestones import MilestoneInput, MilestoneUpdate


def serialize_milestone(row, today: str) -> dict:
    today_date = date.fromisoformat(today)
    target = date.fromisoformat(row['target_date'])
    return dict(
        id=row['id'],
        title=row['title'],
        target_date=row['target_date'],
        note=row['note'],
        color=row['color'],
        pinned=bool(row['pinned']),
        completed=bool(row['completed']),
        created_at=row['created_at'],
        days_left=(target - today_date).days,
    )


def list_milestones(db, uid: int, today: str) -> list[dict]:
    return [serialize_milestone(row, today) for row in milestones_repo.list_ordered(db, uid)]


def create_milestone(db, uid: int, payload: MilestoneInput, timestamp: int, today: str) -> dict:
    if milestones_repo.count(db, uid) >= 200:
        raise ValidationDomainError('里程碑数量已达上限（200 项）')
    milestone_id = new_key()
    milestones_repo.insert(
        db,
        uid,
        milestone_id,
        payload.title,
        payload.target_date.isoformat(),
        payload.note,
        payload.color,
        int(payload.pinned),
        0,
        timestamp,
    )
    row = milestones_repo.get(db, uid, milestone_id)
    return serialize_milestone(row, today)


def update_milestone(db, uid: int, milestone_id: str, payload: MilestoneUpdate, today: str) -> dict:
    updated = milestones_repo.update(
        db,
        uid,
        milestone_id,
        payload.title,
        payload.target_date.isoformat(),
        payload.note,
        payload.color,
        int(payload.pinned),
        int(payload.completed),
    )
    if not updated:
        raise NotFoundError('里程碑不存在')
    row = milestones_repo.get(db, uid, milestone_id)
    return serialize_milestone(row, today)


def delete_milestone(db, uid: int, milestone_id: str) -> None:
    if not milestones_repo.delete(db, uid, milestone_id):
        raise NotFoundError('里程碑不存在')
