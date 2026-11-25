from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

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


def unique_rows(rows):
    if len({row.id for row in rows}) != len(rows):
        raise ValueError('存在重复 ID')
    return rows
