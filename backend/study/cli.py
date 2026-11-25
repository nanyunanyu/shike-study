import argparse
import getpass
import sqlite3
import time

import uvicorn
from pydantic import ValidationError

from .core.config import Settings
from .db.connection import Store
from .db.repositories import users as users_repo
from .schemas.admin import NewUser
from .schemas.common import MIN_PASSWORD_LENGTH
from .services.demo import seed_demo_data
from .services.seed import create_user


def main():
    parser = argparse.ArgumentParser(prog='python -m study.cli')
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('init-admin', help='交互式创建超级管理员')
    server = subs.add_parser('serve', help='启动仅本机可访问的服务')
    server.add_argument('--port', type=int, default=8765)
    demo = subs.add_parser('seed-demo', help='初始化含示例数据的本地演示库并可选启动服务')
    demo.add_argument('--port', type=int, default=0, help='若大于 0 则初始化后立即启动服务')
    args = parser.parse_args()
    if args.command == 'serve':
        uvicorn.run('study.main:app', host='127.0.0.1', port=args.port, proxy_headers=False)
        return
    settings = Settings.from_env()
    if args.command == 'seed-demo':
        store = Store(settings.data_dir)
        store.initialize(settings.timezone)
        created = seed_demo_data(store)
        if created:
            print('演示数据已初始化：管理员 admin / Password123，学习账号 linxi / Password123')
        else:
            print('数据库已有管理员账号，跳过演示数据填充。')
        if args.port > 0:
            uvicorn.run('study.main:app', host='127.0.0.1', port=args.port, proxy_headers=False)
        return

    store = Store(settings.data_dir)
    store.initialize(settings.timezone)
    with store.transaction(read=True) as db:
        if users_repo.has_admin(db):
            parser.exit(1, '超级管理员已经存在。\n')
    username = input('超级管理员用户名（3–32 位字母、数字、点、下划线或连字符）: ')
    password = getpass.getpass(f'密码（至少 {MIN_PASSWORD_LENGTH} 位）: ')
    if password != getpass.getpass('确认密码: '):
        parser.exit(1, '两次密码输入不一致。\n')
    try:
        user = NewUser(username=username, password=password)
        now = int(time.time())
        with store.transaction(write=True) as db:
            create_user(
                db,
                username=user.username,
                password=user.password,
                role='admin',
                must_change=False,
                today=store.date(now).isoformat(),
                now=now,
            )
    except (ValidationError, sqlite3.IntegrityError):
        parser.exit(1, '用户名或密码无效，或超级管理员已存在。\n')
    print('超级管理员已创建。')


if __name__ == '__main__':
    main()
