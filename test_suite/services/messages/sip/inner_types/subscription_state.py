from __future__ import annotations

from services.messages.header import Header
from services.messages.utils import parse_params


class SubscriptionState(Header):
    _NAME = "Subscription-State"

    state: str
    expires: int | None
    params: dict[str, str]

    @classmethod
    def parse(cls, raw: str) -> SubscriptionState:
        params = parse_params(raw)
        expires = int(params["expires"]) if "expires" in params else None
        return cls(
            raw=raw, state=raw.split(";")[0].strip(), expires=expires, params=params
        )
