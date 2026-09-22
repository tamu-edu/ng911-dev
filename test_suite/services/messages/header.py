from __future__ import annotations

from typing import Any, ClassVar, Self


class Header(str):
    """
    Base for composite header values (Via, SipAddress, CallId, ContentType, etc.).
    Instances are the raw header string, with the header name and parsed
    sub-fields available as attributes on top.
    """

    _NAME: ClassVar[str] = ""

    raw: str
    name: str

    def __new__(cls, raw: str, *, name: str | None = None, **fields: Any) -> Self:
        self = str.__new__(cls, raw)
        self.raw = raw
        self.name = name if name is not None else cls._NAME
        for field_name, value in fields.items():
            setattr(self, field_name, value)
        return self

    def __init__(self, raw: str, *, name: str | None = None, **fields: Any) -> None:
        # str is immutable, __new__ already did the work. Needed so
        # type.__call__ doesn't choke on the extra kwargs passed to __new__.
        pass

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Override in each subclass with its own parsing logic."""
        raise NotImplementedError
