import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

from services.aux_services.json_services import get_json
from services.messages.sip.sip_message import SipMessage
from tests.ESRP_023.constants import (
    QUEUE_STATE_CONTENT_TYPE,
    QUEUE_STATE_EVENT,
    STATE_ACTIVE,
    WINFO_CONTENT_TYPE,
    WINFO_EVENT,
    STATE_TERMINATED,
    WINFO_STATE_FULL,
    WINFO_STATE_PARTIAL,
)


@dataclass
class WatcherInfo:
    """Parsed 'application/watcherinfo+xml' body of one SIP NOTIFY."""

    timestamp: float
    state: Optional[str] = None  # 'full' / 'partial'
    resource: Optional[str] = None
    package: Optional[str] = None
    # normalized watcher URI -> status
    watchers: dict = field(default_factory=dict)


def normalize_sip_uri(uri: Optional[str]) -> str:
    """'<sip:User@Host:5060;x=y>' -> 'user@host:5060' (for comparison only)."""
    uri = (uri or "").strip().strip("<>").lower()
    uri = re.sub(r"^sips?:", "", uri)
    return re.split(r"[;?]", uri, maxsplit=1)[0]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_watcherinfo(body: Optional[str], timestamp: float) -> Optional[WatcherInfo]:
    """Parses watcherinfo XML (RFC 3858). Returns None if the body is not valid XML."""
    try:
        root = ET.fromstring((body or "").strip())
    except ET.ParseError:
        return None
    if _local_name(root.tag) != "watcherinfo":
        return None

    info = WatcherInfo(timestamp=timestamp, state=root.get("state"))
    for watcher_list in root:
        if _local_name(watcher_list.tag) != "watcher-list":
            continue
        if info.resource is None:
            info.resource = watcher_list.get("resource")
            info.package = watcher_list.get("package")
        for watcher in watcher_list:
            if _local_name(watcher.tag) == "watcher":
                info.watchers[normalize_sip_uri(watcher.text)] = watcher.get("status")
    return info


def _sip_host(uri: Optional[str]) -> str:
    """'sip:user@host:5061;x=y' -> 'host' (for comparison only)."""
    host = normalize_sip_uri(uri).rsplit("@", 1)[-1]
    if host.startswith("["):
        return host[1:].split("]", 1)[0]
    return host.split(":", 1)[0]


def validate_winfo_notifies(notify_packets: list) -> str:
    """
    Every NOTIFY to Test System BCF: Event emergency-QueueState.winfo and, unless
    it ends the subscription, Content-Type watcherinfo+xml with valid watcherinfo XML body.
    """
    try:
        assert notify_packets, "FAILED -> No SIP NOTIFY found"
        for packet in notify_packets:
            notify = SipMessage.from_packet(packet)
            cseq = notify.cseq
            assert (
                notify.event and notify.event.package == WINFO_EVENT
            ), f"FAILED -> NOTIFY (CSeq: {cseq}) Event is '{notify.event}', expected '{WINFO_EVENT}'"
            if (
                notify.subscription_state
                and notify.subscription_state.state == STATE_TERMINATED
            ):
                continue
            assert (
                notify.content_type
                and notify.content_type.media_type.lower() == WINFO_CONTENT_TYPE
            ), f"FAILED -> NOTIFY (CSeq: {cseq}) Content-Type is '{notify.content_type}', expected '{WINFO_CONTENT_TYPE}'"
            assert parse_watcherinfo(
                notify.body, 0
            ), f"FAILED -> NOTIFY (CSeq: {cseq}) body is not valid watcherinfo XML"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_initial_watcherinfo_no_watchers(initial_notify_packet) -> str:
    """The first watcher information is full or partial and has no 'watcher' tags."""
    try:
        assert (
            initial_notify_packet
        ), "FAILED -> No watcher information NOTIFY sent to Test System BCF"
        notify = SipMessage.from_packet(initial_notify_packet)
        info = parse_watcherinfo(notify.body, 0)
        assert info, "FAILED -> Initial NOTIFY body is not valid watcherinfo XML"
        assert info.state in (
            WINFO_STATE_FULL,
            WINFO_STATE_PARTIAL,
        ), f"FAILED -> Initial watcherinfo state is '{info.state}', expected '{WINFO_STATE_FULL}' or '{WINFO_STATE_PARTIAL}'"
        assert (
            not info.watchers
        ), f"FAILED -> Initial watcherinfo contains watchers: {list(info.watchers)}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_watcherinfo_identification(
    watcher_infos: list, allowed_hosts: list
) -> str:
    """
    Every watcher-list resource must contain the FQDN / IP address of the ESRP
    and refer to the emergency-QueueState package.
    """
    try:
        assert (
            watcher_infos
        ), "FAILED -> No watcher information NOTIFY sent to Test System BCF"
        allowed = {host.lower() for host in allowed_hosts if host}
        for info in watcher_infos:
            assert info.resource and _sip_host(info.resource) in allowed, (
                f"FAILED -> watcher-list resource '{info.resource}' "
                f"does not contain ESRP FQDN or IP address, expected one of {sorted(allowed)}"
            )
            assert (
                info.package == QUEUE_STATE_EVENT
            ), f"FAILED -> watcher-list package '{info.package}', expected '{QUEUE_STATE_EVENT}'"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_watcher_reported(
    watcher_infos: list, identity: str, expected_status: str, after_timestamp: float
) -> str:
    """
    Some full or partial watcher information sent after 'after_timestamp'
    reports the Test System with the expected watcher status.
    """
    try:
        statuses = [
            info.watchers[identity]
            for info in watcher_infos
            if info.timestamp >= after_timestamp and identity in info.watchers
        ]
        assert expected_status in statuses, (
            f"FAILED -> No watcher information with watcher '{identity}' "
            f"status='{expected_status}' sent to Test System BCF.\n"
            f"Reported statuses of this watcher: {statuses}"
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_queue_state_notify(notify_packet, expected_state: str) -> str:
    """
    NOTIFY to a QueueState subscriber: Event emergency-QueueState,
    expected Subscription-State and, for an active subscription, QueueState JSON.
    """
    try:
        assert notify_packet, "FAILED -> No SIP NOTIFY found"
        notify = SipMessage.from_packet(notify_packet)
        assert (
            notify.event and notify.event.package == QUEUE_STATE_EVENT
        ), f"FAILED -> NOTIFY Event is '{notify.event}', expected '{QUEUE_STATE_EVENT}'"
        assert (
            notify.subscription_state
            and notify.subscription_state.state == expected_state
        ), f"FAILED -> Subscription-State is '{notify.subscription_state}', expected '{expected_state}'"
        if expected_state == STATE_ACTIVE:
            assert (
                notify.content_type
                and notify.content_type.media_type.lower()
                == QUEUE_STATE_CONTENT_TYPE.lower()
            ), f"FAILED -> NOTIFY Content-Type is '{notify.content_type}', expected '{QUEUE_STATE_CONTENT_TYPE}'"
            assert get_json(
                (notify.body or "").strip()
            ), "FAILED -> NOTIFY body is not a valid QueueState JSON"
        return "PASSED"
    except AssertionError as e:
        return str(e)
