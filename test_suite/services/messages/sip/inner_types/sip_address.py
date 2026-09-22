from __future__ import annotations

import re

from services.messages.header import Header
from services.messages.utils import parse_params


class SipAddress(Header):
    """
    Shared by several real headers (From/To/Contact/Route/Record-Route) - the
    actual name is passed in at parse() time, not fixed here. The full
    original line (e.g. '"Alice" <sip:alice@example.com>;tag=abc123') is
    available via the inherited `raw` attribute.
    """

    _NAME = "SipAddress"

    uri: str
    user: str | None
    host: str | None
    port: int | None
    tag: str | None

    _SIP_ADDR_RE = re.compile(r"<?(?P<uri>sips?:[^>;]+)>?")
    _SIP_URI_RE = re.compile(
        r"sips?:(?P<user>[^@:;]+)?@?(?P<host>[^:;>]+)?(:(?P<port>\d+))?"
    )

    @classmethod
    def parse(cls, raw: str, *, name: str | None = None) -> SipAddress:
        params = parse_params(raw)
        addr_match = cls._SIP_ADDR_RE.search(raw)
        uri = addr_match.group("uri").strip() if addr_match else raw
        uri_match = cls._SIP_URI_RE.search(uri)
        return cls(
            raw=raw,
            name=name,
            uri=uri,
            user=uri_match.group("user") if uri_match else None,
            host=uri_match.group("host") if uri_match else None,
            port=(
                int(uri_match.group("port"))
                if uri_match and uri_match.group("port")
                else None
            ),
            tag=params.get("tag"),
        )
