from __future__ import annotations

from services.messages.sip.inner_types.uri import Uri


class ReferredBy(Uri):
    """
    RFC 3892 Referred-By header - identifies who initiated a REFER, e.g.:
        Referred-By: <sip:chfe@172.16.0.100:5060>
    RFC 3892 explicitly limits a REFER request to at most one Referred-By
    value, so this is a single header.
    """

    _NAME = "Referred-By"

    @property
    def cid(self) -> str | None:
        return self.params.get("cid")
