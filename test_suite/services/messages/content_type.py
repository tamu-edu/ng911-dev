from __future__ import annotations

from services.messages.header import Header
from services.messages.utils import parse_params


class ContentType(Header):
    """Shared by SIP and HTTP - both carry a body described by Content-Type."""

    _NAME = "Content-Type"

    media_type: str
    params: dict[str, str]

    @classmethod
    def parse(cls, raw: str) -> ContentType:
        media_type, _, _rest = raw.partition(";")
        return cls(raw=raw, media_type=media_type.strip(), params=parse_params(raw))
