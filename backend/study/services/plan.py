import json

from ..core.exceptions import ConflictError, NotFoundError, ValidationDomainError
from ..core.security import new_key
from ..db.codec import encode, unpack_plan
from ..db.repositories import days as days_repo, plans as plans_repo, users as users_repo
from ..schemas.plan import CategoriesInput, PlanInput
from .days import merge_day_tasks
from .seed import BUILTINS, default_tasks


def get_plan(db, user, current: str) -> dict:
    return dict(
        current=unpack_plan(plans_repo.get_effective(db, user['id'], current)),
        categories=json.loads(user['categories']),
        defaults=default_tasks(),
        history=[dict(row) for row in plans_repo.list_history(db, user['id'])],
    )


def get_plan_version(db, uid: int, version: str) -> dict:
    row = plans_repo.get_by_id(db, uid, version)
    if not row:
        raise NotFoundError('计划版本不存在')
    return unpack_plan(row)


def save_plan(db, user, payload: PlanInput, timestamp: int, current: str) -> dict:
    uid = user['id']
    old = plans_repo.get_effective(db, uid, current)
    if old['id'] != payload.base:
        raise ConflictError('计划已在其他页面更新，请刷新后重试')
    names = {c['id']: c['name'] for c in json.loads(user['categories']) if not c['archived']}
    if any(t.category not in names for t in payload.tasks):
        raise ValidationDomainError('请为每个任务选择未归档的分类')
    tasks = [dict(t.model_dump(), category_name=names[t.category]) for t in payload.tasks]
    if json.loads(old['tasks']) != tasks:
        plans_repo.insert(db, uid, new_key(), current, timestamp, encode(tasks))
        row = days_repo.get(db, uid, current)
        if row:
            days_repo.update_tasks(db, uid, current, encode(merge_day_tasks(tasks, json.loads(row['tasks']))))
    return get_plan(db, user, current)


def save_categories(db, user, payload: CategoriesInput, current: str) -> list[dict]:
    old = {c['id']: c for c in json.loads(user['categories'])}
    cats = {c.id: c.model_dump() for c in payload.categories}
    builtin_ids = {c['id'] for c in BUILTINS}
    if any(cats.get(c['id']) != c for c in BUILTINS) or any(
        c['builtin'] != (c['id'] in builtin_ids) for c in cats.values()
    ):
        raise ValidationDomainError('不能修改内置分类')
    if not old.keys() <= cats.keys():
        raise ValidationDomainError('分类只能归档，不能删除')
    live = [c['name'].casefold() for c in cats.values() if not c['archived']]
    if len(live) != len(set(live)):
        raise ValidationDomainError('分类名称不能重复')
    if any(cats[t['category']]['archived'] for t in json.loads(plans_repo.get_effective(db, user['id'], current)['tasks'])):
        raise ConflictError('请先在当前计划中迁移该分类下的任务')
    result = list(cats.values())
    users_repo.update_categories(db, user['id'], encode(result))
    return result
