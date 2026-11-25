import json

from ..core.exceptions import ConflictError, ValidationDomainError
from ..core.security import constant_time_equals, make_import_token, new_key
from ..db.codec import encode, normalize_preferences, normalize_review, normalize_task, unpack_focus, unpack_plan
from ..db.repositories import (
    days as days_repo,
    focus as focus_repo,
    milestones as milestones_repo,
    plans as plans_repo,
    users as users_repo,
)
from ..schemas.backup import Backup, ImportCommit
from . import timer as timer_service
from .seed import BUILTINS


def export_backup(db, user) -> dict:
    uid = user['id']
    milestones = [
        dict(
            id=row['id'],
            title=row['title'],
            target_date=row['target_date'],
            note=row['note'],
            color=row['color'],
            pinned=bool(row['pinned']),
            completed=bool(row['completed']),
            created_at=row['created_at'],
        )
        for row in milestones_repo.list_all(db, uid)
    ]
    return dict(
        version=2,
        preferences=normalize_preferences(json.loads(user['preferences'])),
        categories=json.loads(user['categories']),
        plans=[unpack_plan(row) for row in plans_repo.list_all(db, uid)],
        days=[
            dict(
                date=row['date'],
                tasks=[normalize_task(t) for t in json.loads(row['tasks'])],
                review=normalize_review(json.loads(row['review'])),
                checked_at=row['checked_at'],
            )
            for row in days_repo.list_all(db, uid)
        ],
        focus=[unpack_focus(row) for row in focus_repo.list_all(db, uid)],
        milestones=milestones,
    )


def validate_backup(backup: Backup, store, today: str) -> dict:
    def invalid(message: str):
        raise ValidationDomainError(message)

    day_ids = {day.date.isoformat() for day in backup.days}
    if len(day_ids) != len(backup.days):
        invalid('备份中存在重复日期')
    categories = {c.id: c for c in backup.categories}
    if len({c.name.casefold() for c in backup.categories if not c.archived}) != sum(
        not c.archived for c in backup.categories
    ):
        invalid('备份中存在同名分类')
    seeds = {c['id']: c for c in BUILTINS}
    for c in backup.categories:
        if c.builtin != (c.id in seeds) or (c.builtin and c.model_dump() != seeds[c.id]):
            invalid('内置分类不完整或已修改')
    if not seeds.keys() <= categories.keys():
        invalid('备份缺少内置分类')
    for row in (*backup.days, *backup.plans, *backup.focus):
        if row.date.isoformat() > today or row.date.year < 1970:
            invalid('备份包含无效日期或未来日期')

    latest = max(enumerate(backup.plans), key=lambda pair: (pair[1].date, pair[1].created_at, pair[0]))[1]
    if any(not categories.get(t.category) or categories[t.category].archived for t in latest.tasks):
        invalid('当前计划引用了缺失或归档的分类')
    for day in backup.days:
        if day.checked_at is not None and store.date(day.checked_at) != day.date:
            invalid('打卡时间与日期不一致')
    for item in backup.focus:
        if item.date.isoformat() not in day_ids or store.date(item.started_at) != item.date:
            invalid('专注记录未关联有效的开始日期')
    return dict(
        plans=len(backup.plans),
        days=len(backup.days),
        focus=len(backup.focus),
        categories=len(categories),
        milestones=len(backup.milestones),
    )


def _import_token(secret: bytes, user, payload: Backup) -> str:
    return make_import_token(secret, user['id'], user['token_hash'], encode(payload.model_dump(mode='json')))


def preview_backup(payload: Backup, user, store, today: str, import_secret: bytes) -> dict:
    return dict(
        counts=validate_backup(payload, store, today),
        token=_import_token(import_secret, user, payload),
    )


def replace_backup(db, uid: int, backup: Backup) -> None:
    users_repo.update_preferences_and_categories(
        db,
        uid,
        encode(backup.preferences.model_dump()),
        encode([c.model_dump() for c in backup.categories]),
    )
    plans_repo.replace_all(
        db,
        uid,
        (
            (uid, p.id, p.date.isoformat(), p.created_at, encode([t.model_dump() for t in p.tasks]))
            for p in backup.plans
        ),
    )
    days_repo.replace_all(
        db,
        uid,
        (
            (
                uid,
                d.date.isoformat(),
                encode([t.model_dump() for t in d.tasks]),
                encode(d.review.model_dump()),
                d.checked_at,
            )
            for d in backup.days
        ),
    )
    focus_repo.insert_many(
        db,
        (
            (
                uid,
                f.id,
                f.date.isoformat(),
                f.started_at,
                f.ended_at,
                f.seconds,
                f.mode,
                encode(f.task.model_dump()) if f.task else None,
            )
            for f in backup.focus
        ),
    )
    milestones_repo.replace_all(
        db,
        uid,
        (
            (
                uid,
                ms.id,
                ms.title,
                ms.target_date.isoformat(),
                ms.note,
                ms.color,
                int(ms.pinned),
                int(ms.completed),
                ms.created_at,
            )
            for ms in backup.milestones
        ),
    )


def commit_backup(db, user, payload: ImportCommit, store, now: int, today: str, import_secret: bytes) -> dict:
    counts = validate_backup(payload.backup, store, today)
    if not constant_time_equals(payload.token, _import_token(import_secret, user, payload.backup)):
        raise ConflictError('请重新预览要导入的备份')
    if timer_service.current_state(db, user['id'], now):
        raise ConflictError('请先结束计时器及休息阶段')
    name = f"{today}-account-{user['id']}-{new_key()}.json"
    store.write_private('rollback', name, encode(export_backup(db, user)).encode())
    replace_backup(db, user['id'], payload.backup)
    return dict(counts=counts, preferences=payload.backup.preferences)
