def compute_achievements(
    *,
    checkins: int,
    streak: int,
    longest_streak: int,
    total_seconds: int,
    perfect_days: int,
    reviews_count: int,
    sessions_count: int,
    goal_days: int,
    completed_milestones: int,
) -> list[dict]:
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
