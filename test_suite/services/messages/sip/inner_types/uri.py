from __future__ import annotations

import re
from typing import Self

from services.messages.header import Header


class Uri(Header):
    uri: str
    user: str | None
    host: str | None
    port: int | None
    params: dict[str, str]

    _URI_PATTERN = re.compile(r"<([^>]+)>")
    _PARAM_PATTERN = re.compile(r';([a-zA-Z0-9_\-.!%*+`\'~]+)(?:=("[^"]*"|[^;]*))?')
    _SIP_URI_PARTS_PATTERN = re.compile(
        r"^sips?:"
        r"(?:(?P<user>[^@;?]+)@)?"
        r"(?P<host>[^:;?]+)"
        r"(?::(?P<port>\d+))?"
    )

    @classmethod
    def parse(cls, raw: str) -> Self:
        """
        Parses a `<uri>;param=value;...` (or bare `uri;param=value;...`) header
        value into its URI (and, for sip:/sips:-shaped URIs, user/host/port)
        plus a dict of header params.
        """
        raw = raw or ""

        uri_match = cls._URI_PATTERN.search(raw)
        if uri_match:
            uri = uri_match.group(1)
            remainder = raw[uri_match.end() :]
        else:
            uri, _, rest = raw.partition(";")
            uri = uri.strip()
            remainder = ";" + rest if rest else ""

        params: dict[str, str] = {}
        for name, value in cls._PARAM_PATTERN.findall(remainder):
            value = value.strip()
            if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            params[name.lower()] = value

        m = cls._SIP_URI_PARTS_PATTERN.match(uri)
        return cls(
            raw=raw,
            uri=uri,
            user=m.group("user") if m else None,
            host=m.group("host") if m else None,
            port=int(m.group("port")) if m and m.group("port") else None,
            params=params,
        )
