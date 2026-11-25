import json
from datetime import date, timedelta

from ..core.exceptions import ValidationDomainError
from ..db.codec import normalize_preferences, normalize_review, normalize_task
from ..db.repositories import days as days_repo, focus as focus_repo, users as users_repo
from .achievements import compute_achievements
from .milestones import list_milestones
from .reviews import has_review_content

MAX_RANGE_DAYS = 1095


def get_statistics(db, uid: int, today: str, start_date: date | None = None, end_date: date | None = None) -> dict:
    user = users_repo.get_preferences(db, uid)
    prefs = normalize_preferences(json.loads(user['preferences']) if user else {})
    end = date.fromisoformat(today)
    first = (end - timedelta(days=364)).isoformat()

    if (start_date is None) != (end_date is None):
        raise ValidationDomainError('请同时提供开始和结束日期')
    custom_span = 0
    if start_date is not None and end_date is not None:
        if start_date.year < 1970:
            raise ValidationDomainError('开始日期不能早于 1970 年')
        if start_date > end_date:
            raise ValidationDomainError('结束日期不能早于开始日期')
        if end_date > end:
            raise ValidationDomainError('结束日期不能晚于今天')
        custom_span = (end_date - start_date).days + 1
        if custom_span > MAX_RANGE_DAYS:
            raise ValidationDomainError(f'自定义日期范围最多支持 {MAX_RANGE_DAYS} 天')
        cat_start, cat_end = start_date.isoformat(), end_date.isoformat()
        prev_start = (start_date - timedelta(days=custom_span)).isoformat()
        prev_end = (start_date - timedelta(days=1)).isoformat()
    else:
        cat_start = (end - timedelta(days=29)).isoformat()
        cat_end = today
        prev_start = prev_end = None

    series: dict[str, dict] = {}
    custom_series: dict[str, dict] = {}
    categories: dict[str, dict] = {}
    checkins: set[str] = set()
    perfect_days = 0
    reviews_count = 0
    prev_seconds = 0
    has_previous = False

    def bucket(item):
        return categories.setdefault(
            item['category'],
            dict(id=item['category'], name=item['category_name'], completed=0, total=0, seconds=0, named_on=''),
        )

    for row in days_repo.list_up_to(db, uid, today):
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
        entry = dict(
            date=day,
            completed=completed,
            total=len(tasks),
            rate=completed / len(tasks) if tasks else None,
            seconds=0,
            checked=checked,
        )
        if day >= first:
            series[day] = dict(entry)
        if start_date is not None and cat_start <= day <= cat_end:
            custom_series[day] = dict(entry)
        if prev_start is not None and prev_start <= day <= prev_end:
            has_previous = True
        if cat_start <= day <= cat_end:
            for item in tasks:
                group = bucket(item)
                group['name'], group['named_on'] = item['category_name'], day
                group['completed'] += int(item['done'])
                group['total'] += 1

    seconds = 0
    sessions_count = 0
    today_focus_seconds = 0
    daily_focus: dict[str, int] = {}
    for row in focus_repo.list_up_to(db, uid, today):
        day = row['date']
        seconds += row['seconds']
        sessions_count += 1
        daily_focus[day] = daily_focus.get(day, 0) + row['seconds']
        if day == today:
            today_focus_seconds += row['seconds']
        if day in series:
            series[day]['seconds'] += row['seconds']
        if day in custom_series:
            custom_series[day]['seconds'] += row['seconds']
        if prev_start is not None and prev_start <= day <= prev_end:
            prev_seconds += row['seconds']
            has_previous = True
        if cat_start <= day <= cat_end:
            item = json.loads(row['task']) if row['task'] else dict(category='@unbound', category_name='未绑定任务')
            group = bucket(item)
            if day > group['named_on']:
                group['name'], group['named_on'] = item['category_name'], day
            group['seconds'] += row['seconds']

    goal_threshold = prefs['daily_focus_goal_minutes'] * 60
    goal_days = sum(1 for total in daily_focus.values() if total >= goal_threshold)

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

    custom_range = None
    if start_date is not None and end_date is not None:
        range_days = [
            custom_series.get(
                (start_date + timedelta(days=offset)).isoformat(),
                dict(
                    date=(start_date + timedelta(days=offset)).isoformat(),
                    completed=None,
                    total=None,
                    rate=None,
                    seconds=None,
                    checked=False,
                ),
            )
            for offset in range(custom_span)
        ]
        custom_range = dict(
            start=cat_start,
            end=cat_end,
            days=range_days,
            previous_seconds=prev_seconds,
            has_previous=has_previous,
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

    result = dict(
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
    if custom_range is not None:
        result['custom_range'] = custom_range
    return result
