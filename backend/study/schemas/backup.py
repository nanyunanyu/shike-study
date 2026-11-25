from datetime import date
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator

from .auth import Preferences
from .common import Key, Mode, Model, Name, unique_rows
from .days import DayTask, Review, TaskSnapshot
from .milestones import Milestone
from .plan import Category


class FocusTask(Model):
    id: Key
    title: Name
    category: Key
    category_name: Name


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
