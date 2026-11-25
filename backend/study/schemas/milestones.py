from datetime import date

from pydantic import Field

from .common import Key, Model, Name, Palette, Text


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
