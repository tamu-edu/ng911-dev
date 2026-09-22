from __future__ import annotations

import re

from services.messages.header import Header
from services.messages.utils import parse_params


class Geolocation(Header):
    """
    RFC 6442 Geolocation header - a *reference* to a location object (e.g. a
    PIDF-LO body part), not the location itself. Typical form:
        Geolocation: <cid:target123@atlanta.example.com>;inserted-by="atlanta.example.com"
    """

    _NAME = "Geolocation"

    uri: str
    scheme: str | None
    inserted_by: str | None
    params: dict[str, str]

    _URI_RE = re.compile(r"<([^>]+)>")
    _SCHEME_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*):")

    @classmethod
    def parse(cls, raw: str) -> Geolocation:
        uri_match = cls._URI_RE.search(raw)
        if uri_match:
            uri = uri_match.group(1).strip()
            # Only the text after the closing '>' is a real header param - the
            # URI itself may contain its own ';' params (e.g. SIP's ';lr'),
            # which must NOT be picked up as Geolocation-header params.
            header_params_raw = raw[uri_match.end() :]
        else:
            uri = raw.split(";", 1)[0].strip()
            header_params_raw = raw
        scheme_match = cls._SCHEME_RE.match(uri)
        params = parse_params(header_params_raw)
        return cls(
            raw=raw,
            uri=uri,
            scheme=scheme_match.group(1).lower() if scheme_match else None,
            inserted_by=params.get("inserted-by"),
            params=params,
        )
