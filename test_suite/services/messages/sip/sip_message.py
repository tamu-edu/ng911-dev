from dataclasses import dataclass
from typing import Any, NamedTuple

from services.messages.content_type import ContentType
from services.messages.message import Message
from services.messages.sip.inner_types.call_id import CallId
from services.messages.sip.inner_types.call_info import CallInfo
from services.messages.sip.inner_types.cseq import CSeq
from services.messages.sip.inner_types.event import Event
from services.messages.sip.inner_types.geolocation import Geolocation
from services.messages.sip.inner_types.request_line import RequestLine
from services.messages.sip.inner_types.sip_address import SipAddress
from services.messages.sip.inner_types.status_line import StatusLine
from services.messages.sip.inner_types.subscription_state import SubscriptionState
from services.messages.sip.inner_types.via import Via
from services.messages.utils import (
    ensure_present,
    get_body_value,
    get_field_value,
    get_field_values,
    list_or_none,
    parse_int_or_raise,
    require_non_empty_list,
)


class _RequiredSipFields(NamedTuple):
    """Fields RFC 3261 mandates on every SIP message, checked present (still raw strings)."""

    call_id_raw: str
    cseq_raw: str
    via_raw_list: list[str]
    status_code_raw: str | None  # only set (and checked present) for responses


@dataclass
class SipMessage(Message):
    # Required: from_packet() raises MessageServiceError if any of these
    # can't be extracted.
    request_line: RequestLine | None
    status_line: StatusLine | None
    via: list[Via]
    call_id: CallId
    cseq: CSeq

    # Repeatable headers: None if absent, list (never empty) if 1+ occurrences.
    route: list[SipAddress] | None = None
    record_route: list[SipAddress] | None = None
    contact: list[SipAddress] | None = None
    call_info: list[CallInfo] | None = None
    resource_priority: list[str] | None = None

    from_: SipAddress | None = None
    to: SipAddress | None = None
    max_forwards: int | None = None
    content_type: ContentType | None = None
    content_length: int | None = None
    event: Event | None = None
    subscription_state: SubscriptionState | None = None
    geolocation: list[Geolocation] | None = None

    @property
    def summary(self) -> str:
        """One-line label, e.g. "INVITE" for a request, "200 OK" for a response."""
        if self.request_line:
            return self.request_line.method
        if self.status_line:
            return f"{self.status_line.status_code} {self.status_line.reason_phrase}"
        return "SIP"

    @property
    def status_code(self) -> int | None:
        if self.is_request:
            return None
        assert (
            self.status_line is not None
        )  # guaranteed by from_packet's validate_required
        return self.status_line.status_code

    @classmethod
    def validate_required(
        cls, sip: Any, *, packet_number: int, is_request: bool
    ) -> _RequiredSipFields:
        """
        Checks every header RFC 3261 mandates on every SIP message is present:
        Via, Call-ID, CSeq, plus a status code for responses.
        :raises MessageServiceError: a required header is missing
        """
        status_code_raw = None
        if not is_request:
            status_code_raw = ensure_present(
                get_field_value(sip, "status_code"),
                packet_number=packet_number,
                layer_name="sip",
                field_name="status_code",
            )

        call_id_raw = ensure_present(
            get_field_value(sip, "call_id"),
            packet_number=packet_number,
            layer_name="sip",
            field_name="Call-ID",
        )
        cseq_raw = ensure_present(
            get_field_value(sip, "cseq"),
            packet_number=packet_number,
            layer_name="sip",
            field_name="CSeq",
        )
        via_raw_list = require_non_empty_list(
            get_field_values(sip, "via"),
            packet_number=packet_number,
            layer_name="sip",
            field_name="Via",
        )

        return _RequiredSipFields(
            call_id_raw=call_id_raw,
            cseq_raw=cseq_raw,
            via_raw_list=via_raw_list,
            status_code_raw=status_code_raw,
        )

    @classmethod
    def from_packet(cls, packet: Any) -> "SipMessage | None":
        if hasattr(packet, "icmp"):
            return None
        if not hasattr(packet, "sip"):
            return None

        sip = packet.sip
        packet_number = int(packet.number)
        is_request = hasattr(sip, "method")

        required = cls.validate_required(
            sip, packet_number=packet_number, is_request=is_request
        )

        request_line = None
        status_line = None

        if is_request:
            r_uri_host = get_field_value(sip, "r_uri_host") or ""
            r_uri_port = get_field_value(sip, "r_uri_port")
            host = f"{r_uri_host}:{r_uri_port}" if r_uri_port else r_uri_host
            raw_rl = get_field_value(sip, "request_line") or ""
            request_line = RequestLine.parse(
                raw_rl,
                method=get_field_value(sip, "method") or "",
                user=get_field_value(sip, "r_uri_user"),
                host=host,
            )
        else:
            assert (
                required.status_code_raw is not None
            )  # guaranteed by validate_required
            raw_sl = get_field_value(sip, "status_line") or ""
            status_line = StatusLine.parse(
                raw_sl,
                status_code=parse_int_or_raise(
                    required.status_code_raw,
                    packet_number=packet_number,
                    layer_name="sip",
                    field_name="status_code",
                ),
                reason_phrase=get_field_value(sip, "reason_phrase") or "",
            )

        content_type_raw = get_field_value(sip, "content_type")
        content_length_raw = get_field_value(sip, "content_length")
        max_forwards_raw = get_field_value(sip, "max_forwards")

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
            body=get_body_value(sip, "msg_body"),
            raw_headers_text=get_field_value(sip, "msg_hdr") or "",
            request_line=request_line,
            status_line=status_line,
            via=[Via.parse(v) for v in required.via_raw_list],
            call_id=CallId.parse(required.call_id_raw),
            cseq=CSeq.parse(required.cseq_raw),
            route=list_or_none(
                [
                    SipAddress.parse(v, name="Route")
                    for v in get_field_values(sip, "route")
                ]
            ),
            record_route=list_or_none(
                [
                    SipAddress.parse(v, name="Record-Route")
                    for v in get_field_values(sip, "record_route")
                ]
            ),
            from_=next(
                iter(
                    [
                        SipAddress.parse(v, name="From")
                        for v in get_field_values(sip, "from")
                    ]
                ),
                None,
            ),
            to=next(
                iter(
                    [
                        SipAddress.parse(v, name="To")
                        for v in get_field_values(sip, "to")
                    ]
                ),
                None,
            ),
            contact=list_or_none(
                [
                    SipAddress.parse(v, name="Contact")
                    for v in get_field_values(sip, "contact")
                ]
            ),
            max_forwards=(
                parse_int_or_raise(
                    max_forwards_raw,
                    packet_number=packet_number,
                    layer_name="sip",
                    field_name="Max-Forwards",
                )
                if max_forwards_raw is not None
                else None
            ),
            content_type=(
                ContentType.parse(content_type_raw) if content_type_raw else None
            ),
            content_length=int(content_length_raw) if content_length_raw else None,
            call_info=list_or_none(
                [CallInfo.parse(v) for v in get_field_values(sip, "call_info")]
            ),
            resource_priority=list_or_none(get_field_values(sip, "resource_priority")),
            event=next(
                iter([Event.parse(v) for v in get_field_values(sip, "event")]), None
            ),
            subscription_state=next(
                iter(
                    [
                        SubscriptionState.parse(v)
                        for v in get_field_values(sip, "subscription_state")
                    ]
                ),
                None,
            ),
            geolocation=list_or_none(
                [Geolocation.parse(v) for v in get_field_values(sip, "geolocation")]
            ),
        )
