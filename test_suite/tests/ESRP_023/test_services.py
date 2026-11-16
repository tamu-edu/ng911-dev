from dataclasses import dataclass, field
from typing import Optional

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present
from services.aux_services.sip_msg_body_services import clean_up_string
from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_023.checks import (
    _sip_host,
    normalize_sip_uri,
    parse_watcherinfo,
    validate_initial_watcherinfo_no_watchers,
    validate_queue_state_notify,
    validate_watcher_reported,
    validate_watcherinfo_identification,
    validate_winfo_notifies,
)
from tests.ESRP_023.constants import (
    CHFE,
    ESRP_2,
    INTERFACE_NAMES,
    NOT_RUN_BCF,
    NOT_RUN_SUBSCRIBE,
    NOT_RUN_TERMINATE,
    QUEUE_STATE_EVENT,
    ROUTE_KEYS,
    STATE_ACTIVE,
    STATE_TERMINATED,
    WATCHER_STATUS_ACTIVE,
    WATCHER_STATUS_TERMINATED,
    WINFO_EVENT,
)


@dataclass
class SubscriberDialog:
    """SIP messages of one Test System emergency-QueueState subscription."""

    identity: Optional[str] = None  # normalized From URI of the Test System
    subscribe: Optional[Packet] = None
    subscribe_ok: Optional[Packet] = None
    notify: Optional[Packet] = None
    terminate_subscribe: Optional[Packet] = None
    terminate_ok: Optional[Packet] = None
    final_notify: Optional[Packet] = None


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    bcf_subscribe: Optional[Packet] = None
    bcf_subscribe_ts: float = 0
    bcf_subscribe_ok: Optional[Packet] = None
    bcf_initial_notify: Optional[Packet] = None
    bcf_notifies: list = field(default_factory=list)
    queue_uri: Optional[str] = None
    esrp_ip: Optional[str] = None
    watcher_infos: list = field(default_factory=list)
    # Test System name -> SubscriberDialog
    subscribers: dict = field(default_factory=dict)

    @property
    def has_bcf(self) -> bool:
        return self.bcf_subscribe is not None

    @property
    def identities(self) -> dict:
        """normalized SIP URI -> Test System name"""
        return {
            dialog.identity: role
            for role, dialog in self.subscribers.items()
            if dialog.identity
        }


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    Run Config: STIMULUS - SUBSCRIBE Test System BCF to ESRP (IF_BCF_ESRP),
    OTHER SUBSCRIBE - Test System CHFE to ESRP (IF_CHFE_ESRP) and Test System
    ESRP-2 to ESRP (IF_ESRP-2_ESRP); the opposite directions are registered as well
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation
    :return: dict {lower-case interface name: (src IP, dst IP)}, e.g.
             {'if_bcf_esrp': (...), 'if_chfe_esrp': (...), 'if_esrp-2_esrp': (...)}
    """
    selected = [
        message
        for message in filtering_options or []
        if message.message_type == FilterMessageType.STIMULUS
        or (
            message.message_type == FilterMessageType.OTHER
            and message.sip_method == "SUBSCRIBE"
        )
    ]
    if len(selected) != 3:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering (expected STIMULUS and two OTHER SUBSCRIBE messages)"
        )

    ip_by_interface = {
        interface.name: interface.ip
        for entity in lab_config.entities
        for interface in entity.interfaces
    }
    addresses = {
        message.src_interface.lower(): (
            ip_by_interface.get(message.src_interface),
            ip_by_interface.get(message.dst_interface),
        )
        for message in selected
    }

    if set(addresses) != set(INTERFACE_NAMES) or any(
        None in pair for pair in addresses.values()
    ):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )
    return addresses


def _timestamp(packet: Optional[Packet]) -> Optional[float]:
    return float(packet.sniff_timestamp) if packet is not None else None


def _get_expires(packet: Packet) -> Optional[int]:
    fields = extract_all_header_fields_matching_name_from_sip_message(packet, "Expires")
    try:
        return int(clean_up_string(fields[0].split(":", 1)[1].strip()))
    except (IndexError, ValueError):
        return None


def _get_event_subscribes(
    fetcher: PacketFetcher, route: str, event_package: str
) -> list:
    """All SIP SUBSCRIBE messages of the route with the given Event package, in time order."""
    subscribes = []
    for packet in fetcher.get_sip_subscribes(route):
        message = SipMessage.from_packet(packet)
        if message and message.event and message.event.package == event_package:
            subscribes.append(packet)
    return sorted(subscribes, key=_timestamp)


def _get_ok_for_request(
    fetcher: PacketFetcher, route: str, request: Packet
) -> Optional[Packet]:
    """
    First SIP 200 OK after the request in the same dialog whose CSeq (number
    and method) equals the request's, so a 200 OK of another transaction
    (e.g. the terminating SUBSCRIBE) is not taken as the response.
    """
    request_cseq = SipMessage.from_packet(request).cseq
    candidates = sorted(
        fetcher.get_sip_oks(
            route,
            after_timestamp=_timestamp(request),
            call_id=request.sip.call_id,
        ),
        key=_timestamp,
    )
    for packet in candidates:
        cseq = SipMessage.from_packet(packet).cseq
        if (
            cseq.sequence == request_cseq.sequence
            and cseq.method.upper() == request_cseq.method.upper()
        ):
            return packet
    return None


def _get_subscriber_dialog(fetcher: PacketFetcher, role: str) -> SubscriberDialog:
    """
    Initial SUBSCRIBE and the terminating SUBSCRIBE (Expires: 0, same dialog)
    of the Test System with ESRP responses to them.
    """
    key = ROUTE_KEYS[role]
    to_esrp, from_esrp = f"{key}_esrp", f"esrp_{key}"

    subscribes = _get_event_subscribes(fetcher, to_esrp, QUEUE_STATE_EVENT)
    dialog = SubscriberDialog()
    if not subscribes:
        return dialog

    dialog.subscribe = subscribes[0]
    call_id = dialog.subscribe.sip.call_id
    from_header = SipMessage.from_packet(dialog.subscribe).from_
    dialog.identity = normalize_sip_uri(from_header.uri) if from_header else None
    subscribe_ts = _timestamp(dialog.subscribe)

    dialog.terminate_subscribe = next(
        (
            packet
            for packet in subscribes[1:]
            if packet.sip.call_id == call_id and _get_expires(packet) == 0
        ),
        None,
    )
    terminate_ts = _timestamp(dialog.terminate_subscribe)

    dialog.subscribe_ok = _get_ok_for_request(fetcher, from_esrp, dialog.subscribe)
    dialog.notify = fetcher.get_first_sip_notify(
        from_esrp, after_timestamp=subscribe_ts, call_id=call_id
    )
    if dialog.terminate_subscribe is not None:
        dialog.terminate_ok = _get_ok_for_request(
            fetcher, from_esrp, dialog.terminate_subscribe
        )
        dialog.final_notify = fetcher.get_first_sip_notify(
            from_esrp, after_timestamp=terminate_ts, call_id=call_id
        )
    return dialog


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> TestData:
    addresses = get_filter_parameters(lab_config, filtering_options, variation)

    fetcher = PacketFetcher(pcap_service)
    for interface_name, (src_ip, dst_ip) in addresses.items():
        # 'if_bcf_esrp' -> route 'bcf_esrp' (the reverse one is registered as well)
        fetcher.add_route(interface_name.removeprefix("if_"), src_ip, dst_ip)

    data = TestData(esrp_ip=addresses["if_bcf_esrp"][1])

    # Test System CHFE / ESRP-2 subscriptions
    data.subscribers = {
        role: _get_subscriber_dialog(fetcher, role) for role in (CHFE, ESRP_2)
    }

    # Test System BCF to ESRP stimulus - watcher information SUBSCRIBE
    bcf_subscribes = _get_event_subscribes(fetcher, "bcf_esrp", WINFO_EVENT)
    if not bcf_subscribes:
        return data

    data.bcf_subscribe = bcf_subscribes[0]
    data.bcf_subscribe_ts = _timestamp(data.bcf_subscribe)
    bcf_call_id = data.bcf_subscribe.sip.call_id
    data.queue_uri = SipMessage.from_packet(data.bcf_subscribe).request_line.uri

    data.bcf_subscribe_ok = _get_ok_for_request(fetcher, "esrp_bcf", data.bcf_subscribe)

    # ESRP to Test System BCF watcher information; the final NOTIFY of the
    # terminated winfo subscription is not an update of the subscribers
    bcf_notifies = sorted(
        fetcher.get_sip_notifies(
            "esrp_bcf", after_timestamp=data.bcf_subscribe_ts, call_id=bcf_call_id
        ),
        key=_timestamp,
    )
    data.bcf_notifies = bcf_notifies
    data.bcf_initial_notify = bcf_notifies[0] if bcf_notifies else None
    for packet in bcf_notifies:
        message = SipMessage.from_packet(packet)
        if (
            message.subscription_state
            and message.subscription_state.state == STATE_TERMINATED
        ):
            continue
        info = parse_watcherinfo(message.body, _timestamp(packet))
        if info:
            data.watcher_infos.append(info)

    return data


def get_test_names() -> list:
    return [
        "Verify ESRP responds to Test System BCF SIP SUBSCRIBE (emergency-QueueState.winfo) with SIP 200 OK",
        "Verify each SIP NOTIFY (emergency-QueueState.winfo) sent to Test System BCF has 'application/watcherinfo+xml' Content-Type and watcherinfo XML body",
        "Verify initial watcher information sent to Test System BCF is full or partial and has no watchers",
        "Verify watcher information contains ESRP FQDN or IP address and 'emergency-QueueState' package",
        "Verify ESRP responds to Test System CHFE SIP SUBSCRIBE with SIP 200 OK",
        "Verify ESRP sends SIP NOTIFY with QueueState to Test System CHFE when its subscription is established",
        'Verify ESRP sends watcher information to Test System BCF when Test System CHFE becomes a new subscriber (status="active")',
        "Verify ESRP responds to Test System ESRP-2 SIP SUBSCRIBE with SIP 200 OK",
        "Verify ESRP sends SIP NOTIFY with QueueState to Test System ESRP-2 when its subscription is established",
        'Verify ESRP sends watcher information to Test System BCF when Test System ESRP-2 becomes a new subscriber (status="active")',
        "Verify ESRP responds to Test System CHFE terminating SIP SUBSCRIBE with SIP 200 OK",
        "Verify ESRP sends final SIP NOTIFY with 'Subscription-State: terminated' to Test System CHFE",
        'Verify ESRP sends watcher information to Test System BCF when Test System CHFE terminates subscription (status="terminated")',
        "Verify ESRP responds to Test System ESRP-2 terminating SIP SUBSCRIBE with SIP 200 OK",
        "Verify ESRP sends final SIP NOTIFY with 'Subscription-State: terminated' to Test System ESRP-2",
        'Verify ESRP sends watcher information to Test System BCF when Test System ESRP-2 terminates subscription (status="terminated")',
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    data = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    checks = [
        TestCheck(
            test_name="Verify ESRP responds to Test System BCF SIP SUBSCRIBE (emergency-QueueState.winfo) with SIP 200 OK",
            precondition=data.has_bcf,
            precondition_error=NOT_RUN_BCF,
            test_method=is_data_present,
            test_params={
                "test_data": data.bcf_subscribe_ok,
                "error": "FAILED -> No ESRP to Test System BCF SIP 200 OK for SIP SUBSCRIBE found",
            },
        ),
        TestCheck(
            test_name="Verify each SIP NOTIFY (emergency-QueueState.winfo) sent to Test System BCF has 'application/watcherinfo+xml' Content-Type and watcherinfo XML body",
            precondition=data.has_bcf,
            precondition_error=NOT_RUN_BCF,
            test_method=validate_winfo_notifies,
            test_params={"notify_packets": data.bcf_notifies},
        ),
        TestCheck(
            test_name="Verify initial watcher information sent to Test System BCF is full or partial and has no watchers",
            precondition=data.has_bcf,
            precondition_error=NOT_RUN_BCF,
            test_method=validate_initial_watcherinfo_no_watchers,
            test_params={"initial_notify_packet": data.bcf_initial_notify},
        ),
        TestCheck(
            test_name="Verify watcher information contains ESRP FQDN or IP address and 'emergency-QueueState' package",
            precondition=data.has_bcf,
            precondition_error=NOT_RUN_BCF,
            test_method=validate_watcherinfo_identification,
            test_params={
                "watcher_infos": data.watcher_infos,
                "allowed_hosts": [data.esrp_ip, _sip_host(data.queue_uri)],
            },
        ),
    ]

    for role in (CHFE, ESRP_2):
        dialog = data.subscribers[role]
        subscribed = dialog.subscribe is not None
        not_run = NOT_RUN_SUBSCRIBE.format(role=role)
        checks += [
            TestCheck(
                test_name=f"Verify ESRP responds to Test System {role} SIP SUBSCRIBE with SIP 200 OK",
                precondition=subscribed,
                precondition_error=not_run,
                test_method=is_data_present,
                test_params={
                    "test_data": dialog.subscribe_ok,
                    "error": f"FAILED -> No ESRP to Test System {role} SIP 200 OK for SIP SUBSCRIBE found",
                },
            ),
            TestCheck(
                test_name=f"Verify ESRP sends SIP NOTIFY with QueueState to Test System {role} when its subscription is established",
                precondition=subscribed,
                precondition_error=not_run,
                test_method=validate_queue_state_notify,
                test_params={
                    "notify_packet": dialog.notify,
                    "expected_state": STATE_ACTIVE,
                },
            ),
            TestCheck(
                test_name=f'Verify ESRP sends watcher information to Test System BCF when Test System {role} becomes a new subscriber (status="active")',
                test_method=validate_watcher_reported,
                test_params={
                    "watcher_infos": data.watcher_infos,
                    "identity": dialog.identity,
                    "expected_status": WATCHER_STATUS_ACTIVE,
                    "after_timestamp": _timestamp(dialog.subscribe) or 0,
                },
                precondition=data.has_bcf and subscribed,
                precondition_error=NOT_RUN_BCF if not data.has_bcf else not_run,
            ),
        ]

    for role in (CHFE, ESRP_2):
        dialog = data.subscribers[role]
        terminated = dialog.terminate_subscribe is not None
        not_run = NOT_RUN_TERMINATE.format(role=role)
        checks += [
            TestCheck(
                test_name=f"Verify ESRP responds to Test System {role} terminating SIP SUBSCRIBE with SIP 200 OK",
                precondition=terminated,
                precondition_error=not_run,
                test_method=is_data_present,
                test_params={
                    "test_data": dialog.terminate_ok,
                    "error": f"FAILED -> No ESRP to Test System {role} SIP 200 OK for SIP SUBSCRIBE found",
                },
            ),
            TestCheck(
                test_name=f"Verify ESRP sends final SIP NOTIFY with 'Subscription-State: terminated' to Test System {role}",
                precondition=terminated,
                precondition_error=not_run,
                test_method=validate_queue_state_notify,
                test_params={
                    "notify_packet": dialog.final_notify,
                    "expected_state": STATE_TERMINATED,
                },
            ),
            TestCheck(
                test_name=f'Verify ESRP sends watcher information to Test System BCF when Test System {role} terminates subscription (status="terminated")',
                test_method=validate_watcher_reported,
                test_params={
                    "watcher_infos": data.watcher_infos,
                    "identity": dialog.identity,
                    "expected_status": WATCHER_STATUS_TERMINATED,
                    "after_timestamp": _timestamp(dialog.terminate_subscribe) or 0,
                },
                precondition=data.has_bcf and terminated,
                precondition_error=NOT_RUN_BCF if not data.has_bcf else not_run,
            ),
        ]
    return checks
