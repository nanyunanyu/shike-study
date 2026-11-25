from datetime import datetime

from ..core.exceptions import ConflictError, NotFoundError, ValidationDomainError
from ..db.repositories import messages as messages_repo
from ..schemas.messages import NewMessage


def due_time(value: str | None, zone, now: int) -> int:
    if value is None:
        return now
    try:
        local = datetime.fromisoformat(value)
        candidates = set()
        for fold in (0, 1):
            instant = int(local.replace(tzinfo=zone, fold=fold).timestamp())
            if datetime.fromtimestamp(instant, zone).replace(tzinfo=None) == local:
                candidates.add(instant)
    except (ValueError, OverflowError, OSError) as error:
        raise ValidationDomainError('定时日期无效') from error
    if len(candidates) != 1:
        raise ValidationDomainError('该时间在学习系统时区不存在或重复，请选择其他时间')
    due = candidates.pop()
    if due <= now:
        raise ValidationDomainError('定时发送时间须晚于当前时间')
    return due


def serialize(row, *, recipient: bool = True) -> dict:
    keys = ['id', 'sender', 'kind', 'body', 'created_at', 'due_at']
    if recipient:
        keys.append('read_at')
    return {key: row[key] for key in keys}


def status(db, uid: int, now: int) -> dict:
    unread, pending_count = messages_repo.get_unread_and_preview_counts(db, uid, now)
    return dict(unread=unread, pending=bool(pending_count))


def read(db, uid: int, message_id: int, now: int) -> dict:
    if not messages_repo.mark_read(db, uid, message_id, now):
        raise NotFoundError('消息不存在')
    return serialize(messages_repo.get_with_sender(db, message_id))


def delete_from_inbox(db, uid: int, message_id: int, now: int) -> None:
    if not messages_repo.soft_delete_inbox(db, uid, message_id, now):
        raise NotFoundError('消息不存在')


def _format_page(rows, *, recipient: bool) -> dict:
    if rows is None:
        raise NotFoundError('消息不存在')
    return dict(
        items=[serialize(row, recipient=recipient) for row in rows[:20]],
        next_before=rows[19]['id'] if len(rows) > 20 else None,
    )


def inbox(db, uid: int, now: int, before: int | None) -> dict:
    rows = messages_repo.list_inbox_page(db, uid, now, before)
    return _format_page(rows, recipient=True)


def sent(db, sender_id: int, uid: int, now: int, before: int | None) -> dict:
    rows = messages_repo.list_sent_page(db, sender_id, uid, now, before)
    return _format_page(rows, recipient=False)


def pending(db, sender_id: int, uid: int, now: int) -> list[dict]:
    return [serialize(row, recipient=False) for row in messages_repo.list_pending_for_recipient(db, sender_id, uid, now)]


def claim_preview(db, uid: int, now: int) -> dict | None:
    latest, count = messages_repo.claim_preview(db, uid, now)
    if not latest:
        return None
    return dict(message=serialize(latest), more=count - 1)


def send_single(db, sender_id: int, uid: int, payload: NewMessage, zone, timestamp: int) -> dict:
    due = due_time(payload.scheduled_for, zone, timestamp)
    message_id = messages_repo.insert_single(db, sender_id, uid, payload.kind, payload.body, timestamp, due)
    return serialize(messages_repo.get_with_sender(db, message_id), recipient=False)


def send_batch(db, sender_id: int, recipient_ids: list[int], payload: NewMessage, timestamp: int, due: int, dispatch_id: int) -> None:
    messages_repo.insert_batch(db, sender_id, recipient_ids, payload.kind, payload.body, timestamp, due, dispatch_id)


def cancel_single(db, sender_id: int, uid: int, message_id: int, timestamp: int) -> None:
    row = messages_repo.get_with_sender(db, message_id)
    if not row or row['sender_id'] != sender_id or row['recipient_id'] != uid or row['canceled_at'] is not None:
        raise NotFoundError('消息不存在')
    if row['due_at'] <= timestamp:
        raise ConflictError('定时消息已到点，无法取消')
    messages_repo.cancel_single(db, message_id, timestamp)
