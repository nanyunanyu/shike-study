from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator

from .common import Model


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
