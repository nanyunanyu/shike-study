from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Key = Annotated[str, StringConstraints(pattern=r'^[a-zA-Z0-9_-]{1,64}$')]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
HHMM = Annotated[str, StringConstraints(pattern=r'^(?:[01]\d|2[0-3]):[0-5]\d$')]
Text = Annotated[str, StringConstraints(max_length=2000)]
Username = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]{2,31}$')]
MIN_PASSWORD_LENGTH = 6
Password = Annotated[str, StringConstraints(min_length=MIN_PASSWORD_LENGTH, max_length=256)]
Mode = Literal['pomodoro', 'stopwatch', 'countdown']
Issue = Literal['走神', '网课吸收不足', '错题未消化', '背诵不牢', '拖延', '其他']
Mood = Literal['great', 'good', 'neutral', 'tired', 'stressed']
Palette = Literal['mint', 'blue', 'lilac', 'amber', 'rose']


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Times(Model):
    start: HHMM
    end: HHMM | None = None

    @model_validator(mode='after')
    def chronological(self):
        if self.end and self.end <= self.start:
            raise ValueError('结束时间须晚于开始时间')
        return self


class Task(Times):
    id: Key
    title: Name
    category: Key
    note: Text = ''
    estimate: int | None = Field(default=None, ge=1, le=1440)


class AdhocTaskInput(Times):
    title: Name
    category: Key
    note: Text = ''
    estimate: int | None = Field(default=None, ge=1, le=1440)


class TaskSnapshot(Task):
    category_name: Name


class DayTask(TaskSnapshot):
    done: bool = False
    override: Times | None = None
    adhoc: bool = False


def unique_rows(rows):
    if len({row.id for row in rows}) != len(rows):
        raise ValueError('存在重复 ID')
    return rows


class PlanInput(Model):
    tasks: list[Task] = Field(max_length=200)
    base: Key

    _unique = field_validator('tasks')(unique_rows)


class Category(Model):
    id: Key
    name: Name
    archived: bool = False
    builtin: bool = False


class CategoriesInput(Model):
    categories: list[Category] = Field(max_length=100)

    _unique = field_validator('categories')(unique_rows)


class Review(Model):
    effective: list[Text] = Field(default_factory=lambda: ['', ''], max_length=50)
    issues: list[Issue] = Field(default_factory=list, max_length=6)
    other: Text = ''
    priorities: list[Text] = Field(default_factory=lambda: ['', '', ''], max_length=50)
    adjustment: Text = ''
    mood: Mood | None = None
    focus_score: int | None = Field(default=None, ge=1, le=5)
    reflection: Text = ''


class Preferences(Model):
    focus_minutes: int = Field(default=25, ge=1, le=180)
    break_minutes: int = Field(default=5, ge=1, le=120)
    countdown_minutes: int = Field(default=30, ge=1, le=720)
    auto_break: bool = False
    daily_focus_goal_minutes: int = Field(default=180, ge=15, le=1440)
    appearance: Literal['light', 'dark', 'system'] = 'light'
    palette: Palette = 'blue'


class Toggle(Model):
    done: bool


class Login(Model):
    username: Annotated[str, StringConstraints(strip_whitespace=True, max_length=64)]
    password: Annotated[str, StringConstraints(max_length=256)]


class NewUser(Model):
    username: Username
    password: Password
    must_change: bool = True


class ResetPassword(Model):
    password: Password
    must_change: bool = True


class ChangePassword(Model):
    current: Annotated[str, StringConstraints(max_length=256)]
    password: Password


class UserActive(Model):
    active: bool


class NewMessage(Model):
    kind: Literal['reminder', 'encouragement']
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    scheduled_for: Annotated[str, StringConstraints(pattern=r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}$')] | None = None

    @field_validator('body')
    @classmethod
    def text_only(cls, value):
        if '\x00' in value or any('\ud800' <= char <= '\udfff' for char in value):
            raise ValueError('消息正文包含无效字符')
        return value


class NewDispatch(NewMessage):
    request_id: Annotated[str, StringConstraints(pattern=r'^[a-f0-9]{32}$')]
    all_active: bool = False
    recipient_ids: list[Annotated[int, Field(strict=True, gt=0, le=2**53 - 1)]] = Field(min_length=1)

    @field_validator('recipient_ids')
    @classmethod
    def unique_recipients(cls, value):
        if len(set(value)) != len(value):
            raise ValueError('收件人不能重复')
        return value


class TimerStart(Model):
    id: Key
    date: date
    mode: Mode
    task_id: Key | None = None
    minutes: int | None = Field(default=None, ge=1, le=720)


class TimerAction(Model):
    id: Key
    revision: int = Field(ge=0)
    action: Literal['pause', 'resume', 'finish', 'start_break', 'dismiss']


class MilestoneInput(Model):
    title: Name
    target_date: date
    note: Text = ''
    color: Palette = 'blue'
    pinned: bool = False


class MilestoneUpdate(MilestoneInput):
    completed: bool = False


class Milestone(MilestoneUpdate):
    id: Key
    created_at: int = Field(ge=0, le=253402300799)


class BackupPlan(Model):
    id: Key
    date: date
    created_at: int = Field(ge=0, le=253402300799)
    tasks: list[TaskSnapshot] = Field(max_length=200)

    _unique = field_validator('tasks')(unique_rows)


class BackupDay(Model):
    date: date
    tasks: list[DayTask] = Field(max_length=200)
    review: Review
    checked_at: int | None = Field(default=None, ge=0, le=253402300799)

    _unique = field_validator('tasks')(unique_rows)


class FocusTask(Model):
    id: Key
    title: Name
    category: Key
    category_name: Name


class BackupFocus(Model):
    id: Key
    date: date
    started_at: int = Field(ge=0, le=253402300799)
    ended_at: int = Field(ge=0, le=253402300799)
    seconds: int = Field(gt=0)
    mode: Mode
    task: FocusTask | None = None

    @model_validator(mode='after')
    def duration(self):
        if self.ended_at - self.started_at < self.seconds:
            raise ValueError('专注时长超过会话时段')
        return self


class Backup(Model):
    version: Literal[1, 2]
    preferences: Preferences
    categories: list[Category] = Field(max_length=100)
    plans: list[BackupPlan] = Field(min_length=1, max_length=10000)
    days: list[BackupDay] = Field(max_length=10000)
    focus: list[BackupFocus] = Field(max_length=100000)
    milestones: list[Milestone] = Field(default_factory=list, max_length=200)

    _unique = field_validator('categories', 'plans', 'focus', 'milestones')(unique_rows)


class ImportCommit(Model):
    token: Annotated[str, StringConstraints(pattern=r'^[a-f0-9]{64}$')]
    backup: Backup
