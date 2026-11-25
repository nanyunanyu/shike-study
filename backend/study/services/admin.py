import hashlib
import json
import re
import sqlite3
from datetime import date, timedelta

from ..core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationDomainError
from ..core.security import hash_password
from ..db.repositories import (
    days as days_repo,
    focus as focus_repo,
    messages as messages_repo,
    sessions as sessions_repo,
    users as users_repo,
)
from ..schemas.admin import NewUser, ResetPassword, UserActive
from ..schemas.messages import NewDispatch, NewMessage
from . import auth as auth_service, days as days_service, messages as messages_service, plan as plan_service, seed as seed_service, stats as stats_service


def find_user(db, uid: int, *, writable: bool = False):
    row = users_repo.get_by_id(db, uid)
    if not row:
        raise NotFoundError('账号不存在')
    if writable and row['role'] != 'user':
        raise ForbiddenError('不能在后台修改超级管理员账号')
    return row


def list_users(db) -> list[dict]:
    return [auth_service.public_user(row) for row in users_repo.list_all(db)]


def create_student(db, payload: NewUser, today: str, timestamp: int) -> dict:
    try:
        uid = seed_service.create_user(
            db,
            username=payload.username,
            password=payload.password,
            role='user',
            must_change=payload.must_change,
            today=today,
            now=timestamp,
        )
    except sqlite3.IntegrityError as error:
        raise ConflictError('用户名已存在') from error
    return auth_service.public_user(find_user(db, uid))


def set_user_active(db, uid: int, payload: UserActive) -> dict:
    find_user(db, uid, writable=True)
    users_repo.update_active(db, uid, payload.active)
    if not payload.active:
        sessions_repo.delete_all_for_user(db, uid)
    return auth_service.public_user(find_user(db, uid))


def reset_user_password(db, uid: int, payload: ResetPassword) -> dict:
    find_user(db, uid, writable=True)
    users_repo.update_password(
        db,
        uid,
        hash_password(payload.password),
        must_change=payload.must_change,
        reset_lock=True,
    )
    sessions_repo.delete_all_for_user(db, uid)
    return auth_service.public_user(find_user(db, uid))


def delete_user(db, uid: int) -> None:
    find_user(db, uid, writable=True)
    users_repo.delete(db, uid)


def get_user_day(db, uid: int, day: date, current: str) -> dict:
    find_user(db, uid)
    return days_service.get_day_for_date(db, uid, day, current, editable=False)


def get_user_plan(db, uid: int, current: str) -> dict:
    return plan_service.get_plan(db, find_user(db, uid), current)


def get_user_statistics(db, uid: int, current: str, start_date: date | None = None, end_date: date | None = None) -> dict:
    find_user(db, uid)
    return stats_service.get_statistics(db, uid, current, start_date, end_date)


def list_user_sent_messages(db, sender_id: int, uid: int, timestamp: int, before: int | None) -> dict:
    find_user(db, uid, writable=True)
    return messages_service.sent(db, sender_id, uid, timestamp, before)


def list_user_pending_messages(db, sender_id: int, uid: int, timestamp: int) -> list[dict]:
    find_user(db, uid, writable=True)
    return messages_service.pending(db, sender_id, uid, timestamp)


def send_user_message(db, sender_id: int, uid: int, payload: NewMessage, zone, timestamp: int) -> dict:
    if not find_user(db, uid, writable=True)['active']:
        raise ConflictError('账号已停用，不能发送新消息')
    return messages_service.send_single(db, sender_id, uid, payload, zone, timestamp)


def cancel_user_message(db, sender_id: int, uid: int, message_id: int, timestamp: int) -> None:
    messages_service.cancel_single(db, sender_id, uid, message_id, timestamp)


def overview(db, sender_id: int, current_date: date, timestamp: int) -> dict:
    today = current_date.isoformat()
    week = [(current_date - timedelta(days=offset)).isoformat() for offset in range(6, -1, -1)]
    accounts = [dict(row) for row in users_repo.list_with_last_checkin(db, today)]
    for row in accounts:
        row['active'] = bool(row['active'])
        row['must_change'] = bool(row['must_change'])
        row['checked_today'] = row['last_checkin_date'] == today

    checked = days_repo.count_active_checkins_by_date(db, week[0], today)
    focus = focus_repo.sum_active_users_by_date(db, week[0], today)
    pending = messages_repo.count_pending_groups(db, sender_id, timestamp)
    return dict(
        date=today,
        active_accounts=sum(row['active'] and row['role'] == 'user' for row in accounts),
        checked_today=checked.get(today, 0),
        focus_seconds=focus.get(today, 0),
        pending_dispatches=pending,
        trend=[dict(date=day, checked=checked.get(day, 0), focus_seconds=focus.get(day, 0)) for day in week],
        accounts=accounts,
    )


def send_dispatch(db, sender_id: int, payload: NewDispatch, zone, timestamp: int) -> dict:
    recipients = sorted(payload.recipient_ids)
    encoded = json.dumps([recipients, payload.kind, payload.body, payload.scheduled_for, payload.all_active])
    fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
    previous = messages_repo.find_dispatch_by_request(db, sender_id, payload.request_id)
    if previous:
        if previous['fingerprint'] != fingerprint:
            raise ConflictError('发送请求与原内容不一致')
        remaining = messages_repo.has_dispatch_messages(db, previous['id'])
        return {'key': f"batch-{previous['id']}" if remaining else None}

    valid = users_repo.count_valid_active_recipients(db, recipients)
    active_count = users_repo.count_active_students(db) if payload.all_active else valid
    if valid != len(recipients) or active_count != valid:
        raise ConflictError('收件名单已变化。请核对名单后再发送。')
    due = messages_service.due_time(payload.scheduled_for, zone, timestamp)
    batch = messages_repo.insert_dispatch(db, sender_id, payload.request_id, fingerprint, len(recipients))
    messages_service.send_batch(db, sender_id, recipients, payload, timestamp, due, batch)
    return {'key': f'batch-{batch}'}


def _summary(row) -> dict:
    signed_id = row['group_id']
    key = f'batch-{signed_id}' if signed_id > 0 else f'message-{-signed_id}'
    return dict(
        key=key,
        kind=row['kind'],
        body=row['body'],
        created_at=row['created_at'],
        due_at=row['due_at'],
        recipient_count=row['recipient_count'],
        pending=row['pending'],
        sent=row['sent'],
        canceled=row['canceled'],
        read=row['read'],
    )


def dispatches(
    db,
    sender_id: int,
    timestamp: int,
    status: str,
    kind: str | None,
    recipient_id: int | None,
    cursor: str | None,
) -> dict:
    boundary_due = boundary_group_id = None
    if cursor is not None:
        if not re.fullmatch(r'[0-9]{1,18}:-?[0-9]{1,18}', cursor):
            raise ValidationDomainError('消息分页参数无效')
        boundary_due, boundary_group_id = map(int, cursor.split(':'))
    rows = messages_repo.list_dispatch_groups(
        db,
        sender_id,
        timestamp,
        status,
        kind,
        recipient_id,
        boundary_due=boundary_due,
        boundary_group_id=boundary_group_id,
    )
    next_cursor = f"{rows[19]['due_at']}:{rows[19]['group_id']}" if len(rows) > 20 else None
    return dict(items=[_summary(row) for row in rows[:20]], next_cursor=next_cursor)


def _parse_key(key: str) -> tuple[bool, int]:
    match = re.fullmatch(r'(batch|message)-([1-9][0-9]{0,17})', key)
    if not match:
        raise NotFoundError('消息记录不存在')
    return match[1] == 'batch', int(match[2])


def dispatch_detail(db, sender_id: int, key: str, timestamp: int) -> dict:
    is_batch, target = _parse_key(key)
    summary = messages_repo.get_dispatch_group_summary(db, sender_id, timestamp, is_batch, target)
    if not summary:
        raise NotFoundError('消息记录不存在')
    recipients = [dict(row) for row in messages_repo.list_dispatch_recipients(db, sender_id, is_batch, target)]
    return dict(**_summary(summary), recipients=recipients)


def cancel_dispatch(db, sender_id: int, key: str, timestamp: int) -> dict:
    is_batch, target = _parse_key(key)
    record = dispatch_detail(db, sender_id, key, timestamp)
    if not record['pending']:
        raise ConflictError('没有可取消的待发消息')
    messages_repo.cancel_dispatch_group(db, sender_id, timestamp, is_batch, target)
    return dict(ok=True)
