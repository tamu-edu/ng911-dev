from __future__ import annotations

import re

from services.messages.header import Header
from services.messages.utils import parse_params


class CallInfo(Header):
    _NAME = "Call-Info"

    uri: str
    urn_prefix: str | None
    identifier: str | None
    domain: str | None
    purpose: str | None

    _CALL_INFO_URN_RE = re.compile(
        r"urn:emergency:uid:(?P<kind>callid|incidentid):(?P<identifier>[^:]+):(?P<domain>.+)"
    )

    @classmethod
    def parse(cls, raw: str) -> CallInfo:
        params = parse_params(raw)
        uri_match = re.search(r"<([^>]+)>", raw)
        # Not all Call-Info values are wrapped in <>: e.g. EmergencyCallData.ServiceInfo
        # URLs can appear bare, with params tacked on directly after a ';'.
        uri = uri_match.group(1) if uri_match else raw.split(";", 1)[0].strip()
        urn_match = cls._CALL_INFO_URN_RE.search(uri)
        return cls(
            raw=raw,
            uri=uri,
            urn_prefix=(
                f"urn:emergency:uid:{urn_match.group('kind')}" if urn_match else None
            ),
            identifier=urn_match.group("identifier") if urn_match else None,
            domain=urn_match.group("domain") if urn_match else None,
            purpose=params.get("purpose"),
        )
