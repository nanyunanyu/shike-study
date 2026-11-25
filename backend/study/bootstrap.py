"""初始化托管数据库，并按环境变量创建初始账号。"""

import os
import time
from pathlib import Path

from pydantic import ValidationError

from .core.config import BACKEND_ROOT, Settings
from .db.connection import Store
from .db.repositories import users as users_repo
from .schemas.admin import NewUser
from .services.seed import create_user

ROOT = BACKEND_ROOT


def configured_user(prefix: str):
    username = os.environ.get(f'{prefix}_USERNAME')
    password = os.environ.get(f'{prefix}_PASSWORD')
    if username is None and password is None:
        return None
    try:
        return NewUser(username=username, password=password)
    except ValidationError:
        raise RuntimeError(f'{prefix}_USERNAME / {prefix}_PASSWORD 配置无效') from None


def prepare(directory=None) -> Path:
    settings = Settings.from_env(directory)
    admin = configured_user('STUDY_ADMIN')
    member = configured_user('STUDY_MEMBER')
    if admin and member and admin.username == member.username:
        raise RuntimeError('初始管理员和学习账号必须使用不同的用户名')
    store = Store(settings.data_dir)
    store.initialize(settings.timezone)
    now = int(time.time())
    today = store.date(now).isoformat()
    with store.transaction(write=True) as db:
        if admin and not users_repo.has_admin(db):
            create_user(
                db,
                username=admin.username,
                password=admin.password,
                role='admin',
                must_change=False,
                today=today,
                now=now,
            )
        if member and not users_repo.get_by_username(db, member.username):
            create_user(
                db,
                username=member.username,
                password=member.password,
                role='user',
                must_change=True,
                today=today,
                now=now,
            )
    return settings.data_dir


if __name__ == '__main__':
    print(f'数据目录：{prepare()}')
