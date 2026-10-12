from __future__ import annotations

from services.messages.header import Header


class StatusLine(Header):
    """
    Unlike other Header subclasses, StatusLine isn't built purely from its
    own raw string - status_code/reason_phrase come from separate pyshark
    fields and are already validated (packet context, int check) by the
    caller. parse() takes them as explicit kwargs instead of the usual
    single `raw`.
    """

    _NAME = "Status-Line"

    sip_version: str
    status_code: int
    reason_phrase: str

    @classmethod
    def parse(  # type: ignore[override]
        cls, raw: str, *, status_code: int, reason_phrase: str
    ) -> StatusLine:
        return cls(
            raw=raw,
            sip_version=raw.split(" ", 1)[0] if raw else "",
            status_code=status_code,
            reason_phrase=reason_phrase,
        )
