from __future__ import annotations

from services.messages.header import Header


class CallId(Header):
    _NAME = "Call-ID"

    local_part: str
    host_part: str | None

    @classmethod
    def parse(cls, raw: str) -> CallId:
        local_part, _, host_part = raw.partition("@")
        return cls(
            raw=raw, local_part=local_part.strip(), host_part=host_part.strip() or None
        )
