from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class MessageEntry:
    timestamp: float

    src_name: str
    src_ip: str

    dst_name: str
    dst_ip: str

    protocol: str

    message_type: str

    method: Optional[str]

    summary: str

    message: str

    packet_number: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)
