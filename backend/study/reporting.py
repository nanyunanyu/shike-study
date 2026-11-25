import json
from datetime import date, timedelta

from fastapi import HTTPException

from .extensions import compute_achievements, has_review_content, list_milestones
from .seed import BUILTINS
from .store import encode, normalize_preferences, normalize_review, normalize_task, unpack_focus, unpack_plan


def statistics(db, uid, today):
    user = db.execute('SELECT preferences FROM users WHERE id=?', (uid,)).fetchone()
    prefs = normalize_preferences(json.loads(user['preferences']) if user else {})
    first = (date.fromisoformat(today) - timedelta(days=364)).isoformat()
    recent = (date.fromisoformat(today) - timedelta(days=29)).isoformat()
    series, categories, checkins = {}, {}, set()
    perfect_days = 0
    reviews_count = 0

    def bucket(item):
        return categories.setdefault(
            item['category'],
            dict(id=item['category'], name=item['category_name'], completed=0, total=0, seconds=0, named_on=''),
        )

    for row in db.execute('SELECT * FROM days WHERE user_id=? AND date<=? ORDER BY date', (uid, today)):
        day = row['date']
        tasks = [normalize_task(t) for t in json.loads(row['tasks'])]
        review = normalize_review(json.loads(row['review']))
        completed = sum(1 for t in tasks if t['done'])
        checked = row['checked_at'] is not None
        if checked:
            checkins.add(day)
            if tasks and completed == len(tasks):
                perfect_days += 1
        if has_review_content(review):
            reviews_count += 1
        if day < first:
            continue
        series[day] = dict(
            date=day,
            completed=completed,
            total=len(tasks),
            rate=completed / len(tasks) if tasks else None,
            seconds=0,
            checked=checked,
        )
        if day >= recent:
            for item in tasks:
                group = bucket(item)
                group['name'], group['named_on'] = item['category_name'], day
                group['completed'] += int(item['done'])
                group['total'] += 1

    seconds = 0
    sessions_count = 0
    today_focus_seconds = 0
    daily_focus = {}
    for row in db.execute('SELECT * FROM focus WHERE user_id=? AND date<=? ORDER BY date,ended_at', (uid, today)):
        day = row['date']
        seconds += row['seconds']
        sessions_count += 1
        daily_focus[day] = daily_focus.get(day, 0) + row['seconds']
        if day == today:
            today_focus_seconds += row['seconds']
        if day in series:
            series[day]['seconds'] += row['seconds']
        if day >= recent:
            item = json.loads(row['task']) if row['task'] else dict(category='@unbound', category_name='未绑定任务')
            group = bucket(item)
            if day > group['named_on']:
                group['name'], group['named_on'] = item['category_name'], day
            group['seconds'] += row['seconds']

    goal_threshold = prefs['daily_focus_goal_minutes'] * 60
    goal_days = sum(1 for total in daily_focus.values() if total >= goal_threshold)

    end = date.fromisoformat(today)
    cursor = end if today in checkins else end - timedelta(days=1)
    streak = 0
    while cursor.isoformat() in checkins:
        streak += 1
        if cursor == date.min:
            break
        cursor -= timedelta(days=1)

    longest_streak = 0
    run = 0
    prev_date = None
    for iso in sorted(checkins):
        curr = date.fromisoformat(iso)
        if prev_date is not None and (curr - prev_date).days == 1:
            run += 1
        else:
            run = 1
        if run > longest_streak:
            longest_streak = run
        prev_date = curr

    calendar = []
    for offset in range(364, -1, -1):
        day = (end - timedelta(days=offset)).isoformat()
        calendar.append(
            series.get(day, dict(date=day, completed=None, total=None, rate=None, seconds=None, checked=False))
        )
    for group in categories.values():
        group.pop('named_on')
        group['rate'] = group['completed'] / group['total'] if group['total'] else None

    milestones = list_milestones(db, uid, today)
    completed_milestones = sum(1 for item in milestones if item['completed'])
    achievements = compute_achievements(
        checkins=len(checkins),
        streak=streak,
        longest_streak=longest_streak,
        total_seconds=seconds,
        perfect_days=perfect_days,
        reviews_count=reviews_count,
        sessions_count=sessions_count,
        goal_days=goal_days,
        completed_milestones=completed_milestones,
    )

    return dict(
        today=today,
        streak=streak,
        longest_streak=longest_streak,
        checkins=len(checkins),
        seconds=seconds,
        today_focus_seconds=today_focus_seconds,
        daily_focus_goal_minutes=prefs['daily_focus_goal_minutes'],
        reviews_count=reviews_count,
        calendar=calendar,
        categories=sorted(categories.values(), key=lambda row: (-row['total'], -row['seconds'], row['name'])),
        achievements=achievements,
        pinned_milestones=[item for item in milestones if item['pinned'] and not item['completed']][:3],
    )


def export_backup(db, user):
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
        for row in db.execute('SELECT * FROM milestones WHERE user_id=? ORDER BY created_at, id', (uid,))
    ]
    return dict(
        version=2,
        preferences=normalize_preferences(json.loads(user['preferences'])),
        categories=json.loads(user['categories']),
        plans=[
            unpack_plan(row)
            for row in db.execute('SELECT * FROM plans WHERE user_id=? ORDER BY date,created_at,rowid', (uid,))
        ],
        days=[
            dict(
                date=row['date'],
                tasks=[normalize_task(t) for t in json.loads(row['tasks'])],
                review=normalize_review(json.loads(row['review'])),
                checked_at=row['checked_at'],
            )
            for row in db.execute('SELECT * FROM days WHERE user_id=? ORDER BY date', (uid,))
        ],
        focus=[
            unpack_focus(row)
            for row in db.execute('SELECT * FROM focus WHERE user_id=? ORDER BY started_at,id', (uid,))
        ],
        milestones=milestones,
    )


def validate_backup(backup, store, today):
    def invalid(message):
        raise HTTPException(422, message)

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


def replace_backup(db, uid, backup):
    db.execute('DELETE FROM plans WHERE user_id=?', (uid,))
    db.execute('DELETE FROM days WHERE user_id=?', (uid,))
    db.execute('DELETE FROM milestones WHERE user_id=?', (uid,))
    db.execute(
        'UPDATE users SET preferences=?,categories=? WHERE id=?',
        (encode(backup.preferences.model_dump()), encode([c.model_dump() for c in backup.categories]), uid),
    )
    db.executemany(
        'INSERT INTO plans VALUES (?,?,?,?,?)',
        (
            (uid, p.id, p.date.isoformat(), p.created_at, encode([t.model_dump() for t in p.tasks]))
            for p in backup.plans
        ),
    )
    db.executemany(
        'INSERT INTO days VALUES (?,?,?,?,?)',
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
    db.executemany(
        'INSERT INTO focus VALUES (?,?,?,?,?,?,?,?)',
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
    if backup.milestones:
        db.executemany(
            'INSERT INTO milestones VALUES (?,?,?,?,?,?,?,?,?)',
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
