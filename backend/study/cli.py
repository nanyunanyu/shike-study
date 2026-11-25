import argparse
import getpass
import json
import os
import sqlite3
import time
from datetime import date, timedelta

import uvicorn
from pydantic import ValidationError

from .main import ROOT
from .models import MIN_PASSWORD_LENGTH, NewUser
from .seed import default_tasks
from .store import Store, create_user, day_tasks, encode, key


def seed_demo_data(store: Store):
    now = int(time.time())
    today_date = store.date(now)
    today = today_date.isoformat()
    with store.transaction(write=True) as db:
        if db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
            return False
        admin_id = create_user(
            db, username='admin', password='Password123', role='admin', must_change=False, today=today, now=now
        )
        student_id = create_user(
            db, username='linxi', password='Password123', role='user', must_change=False, today=today, now=now
        )
        # Seed 14 days of realistic history for linxi
        base_tasks = default_tasks()
        moods = ['great', 'good', 'good', 'neutral', 'great', 'tired', 'good', 'great', 'good', 'great']
        reflections = [
            '上午网课吸收很顺畅，下午用番茄钟拆解了 20 道高数积分题，心流状态很稳。',
            '晨背效率比前几天高，晚间滚动复习把昨天模糊的知识点串起来了。',
            '午后略微困倦，调整成 25 分钟短周期后重新找回节奏，错题本补齐了两页。',
            '完成了整套专项练习并复盘错因，明天继续巩固薄弱题型。',
            '节奏张弛有度，休息时远眺和喝水让晚间背诵依然清醒。',
        ]
        issues_pool = [['走神'], ['错题未消化'], [], ['背诵不牢'], ['拖延', '走神'], []]

        for offset in range(13, 0, -1):
            d = (today_date - timedelta(days=offset)).isoformat()
            ts = now - offset * 86400
            done_ratio = 0.65 + (offset % 4) * 0.1
            cutoff = min(len(base_tasks), max(8, int(len(base_tasks) * done_ratio)))
            if offset == 4:
                cutoff = len(base_tasks)  # one perfect day
            tasks = day_tasks(base_tasks)
            for idx, item in enumerate(tasks):
                item['done'] = idx < cutoff
            review = dict(
                effective=['核心知识点框架整理完成', '番茄专注完成专项错题消化'],
                issues=issues_pool[offset % len(issues_pool)],
                other='',
                priorities=['复盘昨日错题本', '完成下一章节网课与习题', '晚间单词滚动记忆'],
                adjustment='下午第一轮专注提前 10 分钟进入状态。',
                mood=moods[offset % len(moods)],
                focus_score=4 if offset % 3 else 5,
                reflection=reflections[offset % len(reflections)],
            )
            checked_at = ts if offset != 9 else None
            db.execute(
                'INSERT OR REPLACE INTO days VALUES (?,?,?,?,?)',
                (student_id, d, encode(tasks), encode(review), checked_at),
            )
            # Focus sessions
            sessions = [
                (2700, 'pomodoro', base_tasks[3]),
                (3000, 'pomodoro', base_tasks[11]),
                (1800, 'countdown', base_tasks[19]),
            ]
            for s_idx, (secs, mode, t) in enumerate(sessions):
                if offset == 9 and s_idx > 0:
                    continue
                task_snap = {k: t[k] for k in ('id', 'title', 'category', 'category_name')}
                db.execute(
                    'INSERT OR IGNORE INTO focus VALUES (?,?,?,?,?,?,?,?)',
                    (student_id, f'demo-{offset}-{s_idx}', d, ts - 7200 + s_idx * 3600, ts - 7200 + s_idx * 3600 + secs, secs, mode, encode(task_snap)),
                )

        # Seed today partial progress + 1 ad-hoc task
        today_list = day_tasks(base_tasks)
        for idx in range(7):
            today_list[idx]['done'] = True
        today_list.insert(
            7,
            dict(
                id='adhoc-demo-1',
                start='10:50',
                end='11:20',
                title='整理本周英语作文高分句型卡片',
                category='review',
                category_name='整理复盘',
                note='今日临时加餐：整理 10 组过渡句',
                estimate=30,
                done=False,
                override=None,
                adhoc=True,
            ),
        )
        today_review = dict(
            effective=['清晨古诗文背诵一遍过', '网课前两节笔记结构清晰'],
            issues=['错题未消化'],
            other='',
            priorities=['下午完成概率论专题练习', '整理 10 组作文句型', '20:00 滚动背诵'],
            adjustment='下午开启雨声白噪音进入 45 分钟深度专注。',
            mood='great',
            focus_score=5,
            reflection='今天进入状态很快，节奏轻盈且专注。',
        )
        db.execute(
            'INSERT OR REPLACE INTO days VALUES (?,?,?,?,?)',
            (student_id, today, encode(today_list), encode(today_review), None),
        )
        for idx, (secs, t) in enumerate([(2700, base_tasks[1]), (3900, base_tasks[3])]):
            task_snap = {k: t[k] for k in ('id', 'title', 'category', 'category_name')}
            db.execute(
                'INSERT OR IGNORE INTO focus VALUES (?,?,?,?,?,?,?,?)',
                (student_id, f'demo-today-{idx}', today, now - 7200 + idx * 3600, now - 7200 + idx * 3600 + secs, secs, 'pomodoro', encode(task_snap)),
            )

        # Milestones
        milestones = [
            ('考研初试倒计时', (today_date + timedelta(days=28)).isoformat(), '保持每日 3 小时深度专注，稳扎稳打。', 'blue', 1, 0),
            ('英语六级冲刺模拟', (today_date + timedelta(days=14)).isoformat(), '完成近 5 年真题精翻与听力复盘。', 'mint', 1, 0),
            ('专业课二轮背诵通关', (today_date + timedelta(days=45)).isoformat(), '梳理核心大题答题框架。', 'lilac', 0, 0),
            ('第一轮基础课全勤收官', (today_date - timedelta(days=5)).isoformat(), '已顺利达成！', 'amber', 0, 1),
        ]
        for title, target_date, note, color, pinned, completed in milestones:
            db.execute(
                'INSERT INTO milestones VALUES (?,?,?,?,?,?,?,?,?)',
                (student_id, key(), title, target_date, note, color, pinned, completed, now),
            )

        # Welcome encouragement message from admin
        db.execute(
            'INSERT INTO messages (sender_id,recipient_id,kind,body,created_at,due_at) VALUES (?,?,?,?,?,?)',
            (admin_id, student_id, 'encouragement', '欢迎来到全新「拾刻学习」，保持稳定节奏，今天也一起加油！', now - 1800, now - 1800),
        )
    return True


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
    if args.command == 'seed-demo':
        store = Store(os.environ.get('STUDY_DATA_DIR', ROOT / 'data'))
        store.initialize(os.environ.get('STUDY_TIMEZONE', 'Asia/Shanghai'))
        created = seed_demo_data(store)
        if created:
            print('演示数据已初始化：管理员 admin / Password123，学习账号 linxi / Password123')
        else:
            print('数据库已有管理员账号，跳过演示数据填充。')
        if args.port > 0:
            uvicorn.run('study.main:app', host='127.0.0.1', port=args.port, proxy_headers=False)
        return

    store = Store(os.environ.get('STUDY_DATA_DIR', ROOT / 'data'))
    store.initialize(os.environ.get('STUDY_TIMEZONE', 'Asia/Shanghai'))
    with store.transaction(read=True) as db:
        if db.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
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
