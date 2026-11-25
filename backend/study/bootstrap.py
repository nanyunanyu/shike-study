"""初始化托管数据库，并按环境变量创建初始账号。"""

import os
import time
from pathlib import Path

from pydantic import ValidationError

from .models import NewUser
from .store import Store, create_user

ROOT = Path(__file__).resolve().parent.parent


def configured_user(prefix):
    username = os.environ.get(f'{prefix}_USERNAME')
    password = os.environ.get(f'{prefix}_PASSWORD')
    if username is None and password is None:
        return None
    try:
        return NewUser(username=username, password=password)
    except ValidationError:
        raise RuntimeError(f'{prefix}_USERNAME / {prefix}_PASSWORD 配置无效') from None


def prepare(directory=None):
    directory = Path(directory or os.environ.get('STUDY_DATA_DIR') or ROOT / 'data')
    admin = configured_user('STUDY_ADMIN')
    member = configured_user('STUDY_MEMBER')
    if admin and member and admin.username == member.username:
        raise RuntimeError('初始管理员和学习账号必须使用不同的用户名')
    store = Store(directory)
    store.initialize(os.environ.get('STUDY_TIMEZONE', 'Asia/Shanghai'))
    now = int(time.time())
    today = store.date(now).isoformat()
    with store.transaction(write=True) as db:
        if admin and not db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
            create_user(
                db,
                username=admin.username,
                password=admin.password,
                role='admin',
                must_change=False,
                today=today,
                now=now,
            )
        if member and not db.execute('SELECT 1 FROM users WHERE username=?', (member.username,)).fetchone():
            create_user(
                db,
                username=member.username,
                password=member.password,
                role='user',
                must_change=True,
                today=today,
                now=now,
            )
    return directory


if __name__ == '__main__':
    print(f'数据目录：{prepare()}')
