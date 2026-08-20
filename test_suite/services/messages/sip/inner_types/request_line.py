from __future__ import annotations

import re

from services.messages.header import Header


class RequestLine(Header):
    """
    Unlike other Header subclasses, RequestLine isn't built from one raw
    string - pyshark gives method/host/user as separate fields. parse()
    takes them as explicit kwargs instead of the usual single `raw`.
    """

    _NAME = "Request-Line"

    method: str
    user: str | None
    host: str
    sip_version: str

    _VERSION_RE = re.compile(r"(SIP/\d\.\d)\s*$")

    @classmethod
    def parse(  # type: ignore[override]
        cls, raw: str, *, method: str, user: str | None, host: str
    ) -> RequestLine:
        version_match = cls._VERSION_RE.search(raw)
        return cls(
            raw=raw,
            method=method,
            user=user,
            host=host,
            sip_version=version_match.group(1) if version_match else "",
        )
