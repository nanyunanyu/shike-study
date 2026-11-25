from pydantic import Field, field_validator

from .common import Key, Model, Name, unique_rows
from .days import Task


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
