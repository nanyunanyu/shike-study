from ..core.security import hash_password, new_key
from ..db.codec import encode
from ..db.repositories import plans as plans_repo, users as users_repo
from ..schemas.auth import Preferences

BUILTINS = [
    dict(id=key, name=name, builtin=True, archived=False)
    for key, name in [
        ('lecture', '网课'),
        ('memory', '背诵'),
        ('practice', '练习'),
        ('review', '整理复盘'),
        ('routine', '生活休息'),
    ]
]

ROWS = [
    ('07:10', '07:40', 'routine', '起床+早餐，听英语音频磨耳朵'),
    ('07:40', '08:25', 'memory', '晨背（古诗文 / 英语单词，隔天轮换）'),
    ('08:25', '08:35', 'routine', '缓冲：整理资料、调试平板'),
    ('08:35', '09:40', 'lecture', '网课1（跟随学校课表）'),
    ('09:40', '09:50', 'routine', '休息：喝水、远眺、活动手腕'),
    ('09:50', '10:55', 'lecture', '网课2（跟随学校课表）'),
    ('10:55', '11:05', 'routine', '休息：简单整理课堂笔记'),
    ('11:05', '11:50', 'lecture', '网课3 / 空余刷题、预习'),
    ('11:50', '12:00', 'routine', '收拾书包，离馆回寝室'),
    ('12:00', '14:00', 'routine', '寝室：吃饭+午休（40–60分钟）'),
    ('14:00', '14:20', 'routine', '路上+到馆就位，摆放资料'),
    ('14:20', '15:10', 'practice', '配套练习（网课对应内容，PDF手写）'),
    ('15:10', '15:20', 'routine', '短暂休息'),
    ('15:20', '16:10', 'practice', '补齐另一科专项'),
    ('16:10', '16:20', 'review', '间隙：整理错题'),
    ('16:20', '17:10', 'review', '当日复盘：重点、错题、难背内容'),
    ('17:10', '18:10', 'routine', '晚饭+散步放松'),
    ('18:10', '19:00', 'review', '笔记补全、整理答题模板'),
    ('19:00', '19:10', 'routine', '休息'),
    ('19:10', '20:00', 'memory', '滚动背诵（晨背+白天所学）'),
    ('20:00', '20:10', 'routine', '休息'),
    ('20:10', '20:50', 'practice', '弹性任务：补习题 / 预习 / 攻克薄弱点'),
    ('20:50', '21:00', 'routine', '收拾物品，核对今日任务'),
    ('21:00', None, 'routine', '离开图书馆回宿舍'),
]


def minutes(value: str) -> int:
    hour, minute = map(int, value.split(':'))
    return hour * 60 + minute


def default_tasks() -> list[dict]:
    names = {c['id']: c['name'] for c in BUILTINS}
    return [
        dict(
            id=f'default-{i:02d}',
            start=start,
            end=end,
            category=category,
            category_name=names[category],
            title=title,
            note='',
            estimate=minutes(end) - minutes(start) if end and category != 'routine' else None,
        )
        for i, (start, end, category, title) in enumerate(ROWS, 1)
    ]


def create_user(db, *, username: str, password: str, role: str, must_change: bool, today: str, now: int) -> int:
    user_id = users_repo.insert(
        db,
        username=username,
        password_hash=hash_password(password),
        role=role,
        must_change=must_change,
        preferences_json=encode(Preferences().model_dump()),
        categories_json=encode(BUILTINS),
    )
    plans_repo.insert(db, user_id, new_key(), today, now, encode(default_tasks()))
    return user_id
