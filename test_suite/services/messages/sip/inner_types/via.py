from __future__ import annotations

import re

from services.messages.header import Header
from services.messages.utils import parse_params


class Via(Header):
    _NAME = "Via"

    transport: str
    sent_by_host: str
    sent_by_port: int | None
    branch: str | None

    _VIA_RE = re.compile(
        r"^SIP/2\.0/(?P<transport>\S+)\s+(?P<host>[^:;\s]+)(:(?P<port>\d+))?"
    )

    @classmethod
    def parse(cls, raw: str) -> Via:
        m = cls._VIA_RE.match(raw.strip())
        params = parse_params(raw)
        return cls(
            raw=raw,
            transport=m.group("transport") if m else "",
            sent_by_host=m.group("host") if m else "",
            sent_by_port=int(m.group("port")) if m and m.group("port") else None,
            branch=params.get("branch"),
        )
