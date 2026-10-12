from __future__ import annotations

from services.messages.header import Header
from services.messages.utils import parse_params


class Event(Header):
    _NAME = "Event"

    package: str
    params: dict[str, str]

    @classmethod
    def parse(cls, raw: str) -> Event:
        return cls(raw=raw, package=raw.split(";")[0].strip(), params=parse_params(raw))
