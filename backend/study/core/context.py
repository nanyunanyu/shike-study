from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import Settings

if TYPE_CHECKING:
    from ..db.connection import Store


@dataclass
class AppContext:
    store: 'Store'
    settings: Settings
    clock: Callable[[], float]
    dummy_hash: str
    import_secret: bytes

    def now(self) -> int:
        return int(self.clock())

    def today(self) -> str:
        return self.store.date(self.now()).isoformat()
