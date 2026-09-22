from __future__ import annotations

import re

from services.messages.header import Header


class RequestLine(Header):
    """
    Unlike other Header subclasses, RequestLine isn't built from one raw
    string - pyshark gives method/host/user as separate fields. parse()
    takes them as explicit kwargs instead of the usual single `raw`.

    `uri` is the full Request-URI extracted straight from the raw line,
    so it stays correct for URIs that aren't a plain sip:user@host
    - e.g. urn:service:sos, tel: URIs, or an r-uri.
    """

    _NAME = "Request-Line"

    method: str
    user: str | None
    host: str
    uri: str
    sip_version: str

    _VERSION_RE = re.compile(r"(SIP/\d\.\d)\s*$")
    _LINE_RE = re.compile(r"^\s*\S+\s+(?P<uri>\S+)\s+SIP/\d\.\d\s*$")

    @classmethod
    def parse(  # type: ignore[override]
        cls, raw: str, *, method: str, user: str | None, host: str
    ) -> RequestLine:
        version_match = cls._VERSION_RE.search(raw)
        line_match = cls._LINE_RE.match(raw)

        return cls(
            raw=raw,
            method=method,
            user=user,
            host=host,
            uri=line_match.group("uri") if line_match else "",
            sip_version=version_match.group(1) if version_match else "",
        )
