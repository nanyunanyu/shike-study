from pydantic import Field

from .common import Issue, Key, Model, Mood, Name, Text, Times


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


class Toggle(Model):
    done: bool


class Review(Model):
    effective: list[Text] = Field(default_factory=lambda: ['', ''], max_length=50)
    issues: list[Issue] = Field(default_factory=list, max_length=6)
    other: Text = ''
    priorities: list[Text] = Field(default_factory=lambda: ['', '', ''], max_length=50)
    adjustment: Text = ''
    mood: Mood | None = None
    focus_score: int | None = Field(default=None, ge=1, le=5)
    reflection: Text = ''
