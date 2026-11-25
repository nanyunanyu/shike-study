from datetime import date
from typing import Literal

from pydantic import Field

from .common import Key, Mode, Model


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
