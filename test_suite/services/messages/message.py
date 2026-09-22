from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Message(ABC):
    """Base class for a parsed SIP/HTTP message built from a pyshark packet."""

    packet_number: int
    timestamp: float

    src_ip: str | None
    src_port: int | None
    dst_ip: str | None
    dst_port: int | None

    is_request: bool
    body: str
    raw_headers_text: str

    @property
    @abstractmethod
    def summary(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_packet(cls, packet: Any) -> Message | None:
        """
        :param packet: pyshark packet
        :return: parsed Message, or None if the packet has no relevant layer
        :raises MessageServiceError: a required header is missing or malformed
        """
        raise NotImplementedError
