import json
from datetime import date

from fastapi import HTTPException

from .store import key, normalize_review


def has_review_content(review):
    if not isinstance(review, dict):
        return False
    if review.get('mood') is not None or review.get('focus_score') is not None:
        return True
    if any(str(item).strip() for item in review.get('effective', [])):
        return True
    if any(str(item).strip() for item in review.get('priorities', [])):
        return True
    if review.get('issues'):
        return True
    return any(str(review.get(field, '')).strip() for field in ('other', 'adjustment', 'reflection'))


def serialize_milestone(row, today):
    today_date = date.fromisoformat(today)
    target = date.fromisoformat(row['target_date'])
    return dict(
        id=row['id'],
        title=row['title'],
        target_date=row['target_date'],
        note=row['note'],
        color=row['color'],
        pinned=bool(row['pinned']),
        completed=bool(row['completed']),
        created_at=row['created_at'],
        days_left=(target - today_date).days,
    )


def list_milestones(db, uid, today):
    rows = db.execute(
        '''
        SELECT * FROM milestones WHERE user_id=?
        ORDER BY completed ASC, pinned DESC, target_date ASC, created_at DESC
        ''',
        (uid,),
    ).fetchall()
    return [serialize_milestone(row, today) for row in rows]


def create_milestone(db, uid, payload, timestamp, today):
    count = db.execute('SELECT count(*) FROM milestones WHERE user_id=?', (uid,)).fetchone()[0]
    if count >= 200:
        raise HTTPException(422, '里程碑数量已达上限（200 项）')
    milestone_id = key()
    db.execute(
        '''
        INSERT INTO milestones (user_id,id,title,target_date,note,color,pinned,completed,created_at)
        VALUES (?,?,?,?,?,?,?,0,?)
        ''',
        (uid, milestone_id, payload.title, payload.target_date.isoformat(), payload.note, payload.color, int(payload.pinned), timestamp),
    )
    row = db.execute('SELECT * FROM milestones WHERE user_id=? AND id=?', (uid, milestone_id)).fetchone()
    return serialize_milestone(row, today)


def update_milestone(db, uid, milestone_id, payload, today):
    result = db.execute(
        '''
        UPDATE milestones
        SET title=?, target_date=?, note=?, color=?, pinned=?, completed=?
        WHERE user_id=? AND id=?
        ''',
        (
            payload.title,
            payload.target_date.isoformat(),
            payload.note,
            payload.color,
            int(payload.pinned),
            int(payload.completed),
            uid,
            milestone_id,
        ),
    )
    if not result.rowcount:
        raise HTTPException(404, '里程碑不存在')
    row = db.execute('SELECT * FROM milestones WHERE user_id=? AND id=?', (uid, milestone_id)).fetchone()
    return serialize_milestone(row, today)


def delete_milestone(db, uid, milestone_id):
    result = db.execute('DELETE FROM milestones WHERE user_id=? AND id=?', (uid, milestone_id))
    if not result.rowcount:
        raise HTTPException(404, '里程碑不存在')


def list_reviews(db, uid, today, *, mood=None, issue=None, query=None, before=None, limit=20):
    focus_map = dict(
        db.execute(
            'SELECT date, sum(seconds) FROM focus WHERE user_id=? AND date<=? GROUP BY date',
            (uid, today),
        )
    )
    rows = db.execute(
        'SELECT date, tasks, review, checked_at FROM days WHERE user_id=? AND date<=? ORDER BY date DESC',
        (uid, today),
    ).fetchall()

    all_entries = []
    mood_counts = {}
    score_sum = 0
    score_count = 0

    for row in rows:
        review = normalize_review(json.loads(row['review']))
        if not has_review_content(review):
            continue
        if review['mood']:
            mood_counts[review['mood']] = mood_counts.get(review['mood'], 0) + 1
        if review['focus_score'] is not None:
            score_sum += review['focus_score']
            score_count += 1
        tasks = json.loads(row['tasks'])
        completed = sum(1 for t in tasks if t.get('done'))
        total = len(tasks)
        all_entries.append(
            dict(
                date=row['date'],
                checked_at=row['checked_at'],
                completed=completed,
                total=total,
                rate=completed / total if total else None,
                focus_seconds=focus_map.get(row['date'], 0),
                review=review,
            )
        )

    needle = (query or '').strip().lower()
    filtered = []
    for entry in all_entries:
        review = entry['review']
        if before and entry['date'] >= before:
            continue
        if mood and review['mood'] != mood:
            continue
        if issue and issue not in review['issues']:
            continue
        if needle:
            haystack = ' '.join(
                [
                    entry['date'],
                    *review['effective'],
                    *review['priorities'],
                    *review['issues'],
                    review['other'],
                    review['adjustment'],
                    review['reflection'],
                ]
            ).lower()
            if needle not in haystack:
                continue
        filtered.append(entry)

    page = filtered[:limit]
    next_before = page[-1]['date'] if len(filtered) > limit else None
    summary = dict(
        total_reviews=len(all_entries),
        avg_focus_score=round(score_sum / score_count, 1) if score_count else None,
        mood_counts=mood_counts,
    )
    return dict(items=page, next_before=next_before, summary=summary)


def compute_achievements(
    *,
    checkins,
    streak,
    longest_streak,
    total_seconds,
    perfect_days,
    reviews_count,
    sessions_count,
    goal_days,
    completed_milestones,
):
    hours = total_seconds // 3600
    best_streak = max(streak, longest_streak)
    definitions = [
        ('first_checkin', '初露锋芒', '完成首次学习打卡', 'sparkles', checkins, 1, '天'),
        ('streak_3', '三日成习', '连续打卡达到 3 天', 'flame', best_streak, 3, '天'),
        ('streak_7', '七日连胜', '连续打卡达到 7 天', 'zap', best_streak, 7, '天'),
        ('streak_21', '廿一养成', '连续打卡达到 21 天', 'crown', best_streak, 21, '天'),
        ('streak_100', '百日筑基', '连续打卡达到 100 天', 'medal', best_streak, 100, '天'),
        ('focus_1h', '心流初启', '累计专注满 1 小时', 'clock', hours, 1, '小时'),
        ('focus_10h', '十时耕耘', '累计专注满 10 小时', 'hourglass', hours, 10, '小时'),
        ('focus_50h', '五十时学者', '累计专注满 50 小时', 'book', hours, 50, '小时'),
        ('focus_100h', '百时大师', '累计专注满 100 小时', 'trophy', hours, 100, '小时'),
        ('sessions_30', '番茄达人', '累计完成 30 次有效专注', 'timer', sessions_count, 30, '次'),
        ('goal_days_7', '自律标杆', '累计 7 天达成每日专注目标', 'target', goal_days, 7, '天'),
        ('perfect_day', '完美一日', '单日任务全部完成并打卡', 'check-circle', perfect_days, 1, '次'),
        ('reviewer_7', '自省行者', '累计写下 7 篇每日复盘', 'pen', reviews_count, 7, '篇'),
        ('reviewer_30', '手账名家', '累计写下 30 篇每日复盘', 'feather', reviews_count, 30, '篇'),
        ('milestone_done', '旗开得胜', '完成首个学习目标里程碑', 'flag', completed_milestones, 1, '个'),
    ]
    return [
        dict(
            id=aid,
            title=title,
            description=desc,
            icon=icon,
            unlocked=progress >= target,
            progress=min(progress, target),
            target=target,
            unit=unit,
        )
        for aid, title, desc, icon, progress, target, unit in definitions
    ]
