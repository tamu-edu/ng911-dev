from dataclasses import dataclass, field
from typing import Any, NamedTuple

from services.messages.content_type import ContentType
from services.messages.errors.message_service_error import MessageServiceError
from services.messages.message import Message
from services.messages.utils import (
    ensure_present,
    get_body_value,
    get_field_value,
    get_field_values,
    parse_int_or_raise,
)


class _RequiredHttpFields(NamedTuple):
    """Fields required to recognize an HTTP request or response, already validated."""

    # method + request_target are set for requests, status_code_raw for responses.
    method: str | None
    request_target: str | None
    status_code_raw: str | None


@dataclass
class HttpMessage(Message):
    method: str | None = None
    request_target: str | None = None
    http_version: str | None = None

    status_code: int | None = None
    reason_phrase: str | None = None

    content_type: ContentType | None = None
    content_length: int | None = None

    headers: dict[str, list[str]] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        """One-line label, e.g. "POST /BadActors" for a request, "200 OK" for a response."""
        if self.method:
            return f"{self.method} {self.request_target}"
        return f"{self.status_code} {self.reason_phrase}"

    @classmethod
    def _all_header_lines(cls, http: Any) -> dict[str, list[str]]:
        """Dumps every field pyshark's http dissector exposed, keyed by sanitized name."""
        headers: dict[str, list[str]] = {}
        for name in getattr(http, "field_names", []):
            values = get_field_values(http, name)
            if values:
                headers[name] = values
        return headers

    @classmethod
    def validate_required(
        cls, http: Any, *, packet_number: int, is_request: bool
    ) -> _RequiredHttpFields:
        """
        Checks the fields required to recognize an HTTP request or response
        are present: method + request target for requests, a status code for
        responses.
        :raises MessageServiceError: a required field is missing
        """
        if is_request:
            method = ensure_present(
                get_field_value(http, "request_method"),
                packet_number=packet_number,
                layer_name="http",
                field_name="request_method",
            )
            request_target = ensure_present(
                get_field_value(http, "request_full_uri")
                or get_field_value(http, "request_uri"),
                packet_number=packet_number,
                layer_name="http",
                field_name="request_uri",
            )
            return _RequiredHttpFields(
                method=method, request_target=request_target, status_code_raw=None
            )

        status_code_raw = ensure_present(
            get_field_value(http, "response_code"),
            packet_number=packet_number,
            layer_name="http",
            field_name="response_code",
        )
        return _RequiredHttpFields(
            method=None, request_target=None, status_code_raw=status_code_raw
        )

    @classmethod
    def from_packet(cls, packet: Any) -> "HttpMessage | None":
        if hasattr(packet, "icmp"):
            return None
        if not hasattr(packet, "http"):
            return None

        http = packet.http
        packet_number = int(packet.number)

        is_request = hasattr(http, "request_method")
        is_response = hasattr(http, "response_code")

        if not is_request and not is_response:
            raise MessageServiceError(
                "HTTP layer present but the packet is neither a recognizable "
                "request nor a response.",
                errors=[
                    f"packet_number: {packet_number}",
                    "layer: http",
                    "reason: neither request_method nor response_code attribute present",
                ],
            )

        required = cls.validate_required(
            http, packet_number=packet_number, is_request=is_request
        )

        reason_phrase = None
        http_version = None
        status_code = None

        if is_request:
            http_version = get_field_value(http, "request_version")
        else:
            assert (
                required.status_code_raw is not None
            )  # guaranteed by validate_required
            status_code = parse_int_or_raise(
                required.status_code_raw,
                packet_number=packet_number,
                layer_name="http",
                field_name="response_code",
            )
            reason_phrase = get_field_value(http, "response_phrase")
            http_version = get_field_value(http, "response_version")

        content_type_raw = get_field_value(http, "content_type")
        content_length_raw = get_field_value(http, "content_length")
        headers = cls._all_header_lines(http)

        return cls(
            packet_number=packet_number,
            timestamp=float(packet.sniff_timestamp),
            src_ip=str(packet.ip.src) if hasattr(packet, "ip") else None,
            src_port=(
                int(packet.tcp.srcport)
                if hasattr(packet, "tcp")
                else (int(packet.udp.srcport) if hasattr(packet, "udp") else None)
            ),
            dst_ip=str(packet.ip.dst) if hasattr(packet, "ip") else None,
            dst_port=(
                int(packet.tcp.dstport)
                if hasattr(packet, "tcp")
                else (int(packet.udp.dstport) if hasattr(packet, "udp") else None)
            ),
            is_request=is_request,
            body=get_body_value(http, "file_data"),
            raw_headers_text="\n".join(
                f"{name}: {value}"
                for name, values in headers.items()
                for value in values
            ),
            method=required.method,
            request_target=required.request_target,
            http_version=http_version,
            status_code=status_code,
            reason_phrase=reason_phrase,
            content_type=(
                ContentType.parse(content_type_raw) if content_type_raw else None
            ),
            content_length=int(content_length_raw) if content_length_raw else None,
            headers=headers,
        )
