import json

from ..schemas.auth import Preferences
from ..schemas.days import Review


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def normalize_preferences(raw) -> dict:
    base = Preferences().model_dump()
    if isinstance(raw, dict):
        for field in base:
            if field in raw:
                base[field] = raw[field]
    return base


def normalize_review(raw) -> dict:
    base = Review().model_dump()
    if isinstance(raw, dict):
        for field in base:
            if field in raw:
                base[field] = raw[field]
    return base


def normalize_task(item) -> dict:
    result = dict(item)
    result.setdefault('done', False)
    result.setdefault('override', None)
    result.setdefault('adhoc', False)
    return result


def unpack_plan(row) -> dict:
    return dict(id=row['id'], date=row['date'], created_at=row['created_at'], tasks=json.loads(row['tasks']))


def unpack_focus(row) -> dict:
    return {
        k: json.loads(row[k]) if k == 'task' and row[k] else row[k]
        for k in ('id', 'date', 'started_at', 'ended_at', 'seconds', 'mode', 'task')
    }
