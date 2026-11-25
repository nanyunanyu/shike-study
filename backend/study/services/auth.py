import json

from ..core.config import LOCKOUT_SECONDS, LOCKOUT_THRESHOLD
from ..core.context import AppContext
from ..core.exceptions import (
    BadRequestError,
    DomainError,
    ForbiddenError,
    RateLimitError,
    UnauthorizedError,
    ValidationDomainError,
)
from ..core.security import constant_time_equals, digest, hash_password, new_token, verify_password
from ..db.codec import encode, normalize_preferences
from ..db.repositories import sessions as sessions_repo, users as users_repo
from ..schemas.auth import ChangePassword, Login, Preferences


def public_user(user) -> dict:
    return dict(
        id=user['id'],
        username=user['username'],
        role=user['role'],
        active=bool(user['active']),
        must_change=bool(user['must_change']),
    )


def build_bootstrap(user, csrf: str, today: str, timezone: str) -> dict:
    return dict(
        user=public_user(user),
        csrf=csrf,
        today=today,
        timezone=timezone,
        preferences=normalize_preferences(json.loads(user['preferences'])),
    )


def is_initialized(store) -> bool:
    with store.transaction(read=True) as db:
        return users_repo.has_admin(db)


def authenticate_session(
    db,
    *,
    token: str,
    method: str,
    csrf_header: str,
    now: int,
    allow_change: bool = False,
    admin: bool = False,
):
    if len(token) != 43:
        raise UnauthorizedError('请先登录')
    row = sessions_repo.get_active_user_session(db, digest(token), now)
    if not row:
        raise UnauthorizedError('登录已失效')
    if method not in {'GET', 'HEAD', 'OPTIONS'} and not constant_time_equals(row['csrf'], csrf_header):
        raise ForbiddenError('请求验证失败，请刷新页面')
    if row['must_change'] and not allow_change:
        raise ForbiddenError('请先修改初始密码')
    if admin and row['role'] != 'admin':
        raise ForbiddenError('仅超级管理员可访问')
    return row


def login(ctx: AppContext, payload: Login, old_cookie: str | None) -> tuple[str, dict]:
    error: DomainError | None = None
    result: tuple[str, dict] | None = None
    with ctx.store.transaction(write=True) as db:
        user = users_repo.get_by_username(db, payload.username)
        timestamp = ctx.now()
        valid = verify_password(user['password'] if user and user['active'] else ctx.dummy_hash, payload.password)
        if user and user['active'] and user['lock_until'] > timestamp:
            error = RateLimitError('登录失败次数过多，请稍后再试', retry_after=user['lock_until'] - timestamp)
        elif not user or not user['active'] or not valid:
            if user and user['active']:
                failures = (0 if user['lock_until'] else user['failures']) + 1
                until = timestamp + LOCKOUT_SECONDS if failures >= LOCKOUT_THRESHOLD else 0
                users_repo.update_login_failures(db, user['id'], failures, until)
                if until:
                    error = RateLimitError('登录失败次数过多，账号已暂时锁定', retry_after=LOCKOUT_SECONDS)
            if error is None:
                error = UnauthorizedError('用户名或密码不正确，或账号已停用')
        else:
            token, csrf = new_token(), new_token()
            users_repo.reset_login_failures(db, user['id'])
            if old_cookie and len(old_cookie) == 43:
                sessions_repo.delete_by_token_and_user(db, digest(old_cookie), user['id'])
            sessions_repo.insert(db, digest(token), user['id'], csrf, timestamp + ctx.settings.session_age)
            today = ctx.store.date(timestamp).isoformat()
            result = (token, build_bootstrap(user, csrf, today, ctx.store.zone.key))
    if error is not None:
        raise error
    assert result is not None
    return result


def logout(db, user) -> None:
    sessions_repo.delete_by_token(db, user['token_hash'])


def change_password(db, user, payload: ChangePassword, today: str, timezone: str) -> dict:
    if not verify_password(user['password'], payload.current):
        raise BadRequestError('原密码不正确')
    if payload.current == payload.password:
        raise ValidationDomainError('新密码不能与原密码相同')
    users_repo.update_password(db, user['id'], hash_password(payload.password), must_change=False)
    sessions_repo.delete_other_sessions(db, user['id'], user['token_hash'])
    refreshed = users_repo.get_by_id(db, user['id'])
    return build_bootstrap(refreshed, user['csrf'], today, timezone)


def update_preferences(db, user_id: int, payload: Preferences) -> Preferences:
    users_repo.update_preferences(db, user_id, encode(payload.model_dump()))
    return payload
