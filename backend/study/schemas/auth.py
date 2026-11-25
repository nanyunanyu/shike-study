from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from .common import Model, Palette, Password


class Login(Model):
    username: Annotated[str, StringConstraints(strip_whitespace=True, max_length=64)]
    password: Annotated[str, StringConstraints(max_length=256)]


class ChangePassword(Model):
    current: Annotated[str, StringConstraints(max_length=256)]
    password: Password


class Preferences(Model):
    focus_minutes: int = Field(default=25, ge=1, le=180)
    break_minutes: int = Field(default=5, ge=1, le=120)
    countdown_minutes: int = Field(default=30, ge=1, le=720)
    auto_break: bool = False
    daily_focus_goal_minutes: int = Field(default=180, ge=15, le=1440)
    appearance: Literal['light', 'dark', 'system'] = 'light'
    palette: Palette = 'blue'
