from __future__ import annotations

from services.messages.errors.message_service_error import MessageServiceError
from services.messages.header import Header


class CSeq(Header):
    _NAME = "CSeq"

    sequence: int
    method: str

    @classmethod
    def parse(cls, raw: str) -> CSeq:
        seq_str, _, method = raw.strip().partition(" ")
        try:
            sequence = int(seq_str)
        except ValueError as exc:
            raise MessageServiceError(
                "CSeq header does not start with a valid sequence number.",
                errors=[
                    "layer: sip",
                    "field: CSeq",
                    f"raw_value: {raw!r}",
                    f"underlying_exception: {exc!r}",
                ],
            ) from exc
        return cls(raw=raw, sequence=sequence, method=method.strip())
