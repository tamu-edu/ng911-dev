from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present
from checks.log_events.checks import extract_enclosed_value
from services.aux_services.xml_services import extract_location_from_text
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation
from services.config.types.test_config import MessageFilter
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_022.constants import (
    NOT_RUN,
    NOT_RUN_NO_LIS_PIDFLO,
    NOT_RUN_VARIATION,
)


class LocationVariation(IntEnum):
    REF_URL = 1  # location by reference via REF URL (HTTP, HTTPS)
    SIP = 2  # location by reference via SIP


GEOLOCATION_SCHEME_TO_VARIATION = {
    "http": LocationVariation.REF_URL,
    "https": LocationVariation.REF_URL,
    "sip": LocationVariation.SIP,
    "sips": LocationVariation.SIP,
}

# Run Config "other" direction differs per variation:
# REF_URL - ESRP -> LIS, SIP - LIS -> ESRP
LIS_ROUTE_BY_VARIATION = {
    LocationVariation.REF_URL: "esrp_lis",
    LocationVariation.SIP: "lis_esrp",
}


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip,
        out_src_ip, out_dst_ip, other_src_ip, other_dst_ip, lis_url_contains)
    """
    messages_by_type = {m.message_type: m for m in filtering_options or []}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)
    other = messages_by_type.get(FilterMessageType.OTHER)

    if not (stimulus and output and other):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    ip_by_interface = {
        interface.name: interface.ip
        for entity in lab_config.entities
        for interface in entity.interfaces
    }

    stimulus_src_ip = ip_by_interface.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface.get(stimulus.dst_interface)
    out_src_ip = ip_by_interface.get(output.src_interface)
    out_dst_ip = ip_by_interface.get(output.dst_interface)
    other_src_ip = ip_by_interface.get(other.src_interface)
    other_dst_ip = ip_by_interface.get(other.dst_interface)

    if None in (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
    ):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    lis_url_contains = other.header_contains or None

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        lis_url_contains,
    )


def _get_pos_coordinates(pidflo_body: Optional[str]) -> Optional[str]:
    """Returns gml:pos value (e.g. '40.7166 -73.9906') from a PIDF-LO body, or None."""
    raw_pos = extract_location_from_text(pidflo_body or "")
    return " ".join(raw_pos.split()) or None


def _get_ref_url_exchange(
    fetcher: PacketFetcher, after_ts, url_contains: Optional[str]
) -> tuple[Optional[Packet], Optional[str]]:
    """REF_URL variation: ESRP HTTP POST to LIS and PIDF-LO from the LIS 200 OK."""
    request, request_ts = fetcher.get_first_http_post(
        "esrp_lis",
        return_timestamp=True,
        after_timestamp=after_ts,
        url_contains=url_contains,
    )
    if not request:
        return None, None

    response = fetcher.get_first_http_200("lis_esrp", after_timestamp=request_ts)
    response_msg = HttpMessage.from_packet(response) if response else None
    return request, (response_msg.body or None) if response_msg else None


def _get_sip_exchange(
    fetcher: PacketFetcher, after_ts
) -> tuple[Optional[Packet], Optional[str]]:
    """SIP variation: ESRP SUBSCRIBE to LIS and PIDF-LO from the first
    LIS NOTIFY with a body within the same dialog."""
    subscribe, subscribe_ts = fetcher.get_first_sip_subscribe(
        "esrp_lis", return_timestamp=True, after_timestamp=after_ts
    )
    if not subscribe:
        return None, None

    # Same field as PacketFetcher uses for its call_id post-filter
    call_id = getattr(getattr(subscribe, "sip", None), "call_id", None)
    notifies = fetcher.get_sip_notifies(
        "lis_esrp", after_timestamp=subscribe_ts, call_id=call_id
    )
    for notify in notifies:
        notify_msg = SipMessage.from_packet(notify)
        if notify_msg and notify_msg.body:
            return subscribe, notify_msg.body
    return subscribe, None


def get_lis_exchange(
    fetcher: PacketFetcher,
    variation_number: Optional[int],
    after_ts,
    url_contains: Optional[str] = None,
) -> tuple[Optional[Packet], Optional[str]]:
    """
    Returns (ESRP request to LIS, PIDF-LO body from LIS response).

    :param fetcher: PacketFetcher with "esrp_lis"/"lis_esrp" routes registered
    :param variation_number: LocationVariation.REF_URL - HTTP POST to the reference URL,
        LocationVariation.SIP - SIP SUBSCRIBE/NOTIFY
    :param after_ts: only LIS traffic after this timestamp (the stimulus) is used
    :param url_contains: REF_URL - substring of the ESRP HTTP POST URL (Run Config 'other' header_contains)
    :return: (request packet or None, PIDF-LO body or None)
    """
    if variation_number == LocationVariation.REF_URL:
        return _get_ref_url_exchange(fetcher, after_ts, url_contains)
    if variation_number == LocationVariation.SIP:
        return _get_sip_exchange(fetcher, after_ts)
    return None, None


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Optional[Packet] = None
    lis_request_message: Optional[Packet] = None
    esrp_chfe_invite_message: Optional[Packet] = None
    variation_number: Optional[int] = None
    stimulus_geolocation: Optional[str] = None
    outgoing_geolocations: list[str] = field(default_factory=list)
    has_lis_pidflo: bool = False
    is_no_pidf_in_outgoing: Optional[bool] = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> TestData:
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        lis_url_contains,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    data: dict = {}

    msg_fetcher = PacketFetcher(pcap_service)
    msg_fetcher.add_route("bcf_esrp", stimulus_src_ip, stimulus_dst_ip)
    msg_fetcher.add_route("esrp_chfe", out_src_ip, out_dst_ip)

    # BCF to ESRP stimulus message
    stimulus_message, stimulus_timestamp = msg_fetcher.get_first_sip_invite(
        "bcf_esrp", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message
    if not stimulus_message:
        return TestData(**data)

    stimulus_msg = SipMessage.from_packet(stimulus_message)

    # Get stimulus Geolocation value
    stimulus_geolocation_raw = None
    if stimulus_msg and stimulus_msg.geolocation:
        stimulus_geolocation_raw = data["stimulus_geolocation"] = (
            extract_enclosed_value(stimulus_msg.geolocation[0])
        )

    # Detect the variation by the Geolocation reference URI scheme
    geolocation_scheme = (
        stimulus_geolocation_raw.split(":", 1)[0].strip().lower()
        if stimulus_geolocation_raw and ":" in stimulus_geolocation_raw
        else None
    )
    data["variation_number"] = GEOLOCATION_SCHEME_TO_VARIATION.get(geolocation_scheme)

    # Register LIS route according to the direction set in Run Config for this variation
    lis_route = LIS_ROUTE_BY_VARIATION.get(data["variation_number"])
    if lis_route:
        msg_fetcher.add_route(lis_route, other_src_ip, other_dst_ip)

    # Get ESRP request to LIS and PIDF-LO from the LIS response
    lis_request, pidflo_body = get_lis_exchange(
        msg_fetcher, data["variation_number"], stimulus_timestamp, lis_url_contains
    )
    data["lis_request_message"] = lis_request
    lis_pos_coordinates = _get_pos_coordinates(pidflo_body)
    data["has_lis_pidflo"] = bool(lis_pos_coordinates)

    # Get outgoing SIP INVITE from the ESRP to CHFE (independent of the LIS exchange)
    esrp_chfe_invite = msg_fetcher.get_first_sip_invite(
        "esrp_chfe", after_timestamp=stimulus_timestamp
    )
    data["esrp_chfe_invite_message"] = esrp_chfe_invite
    outgoing_invite_msg = (
        SipMessage.from_packet(esrp_chfe_invite) if esrp_chfe_invite else None
    )
    if not outgoing_invite_msg:
        return TestData(**data)

    if outgoing_invite_msg.geolocation:
        data["outgoing_geolocations"] = [
            extract_enclosed_value(value) for value in outgoing_invite_msg.geolocation
        ]

    # PIDF-LO from LIS must not be sent in the outgoing INVITE body.
    if lis_pos_coordinates:
        outgoing_pos_coordinates = _get_pos_coordinates(outgoing_invite_msg.body)
        data["is_no_pidf_in_outgoing"] = outgoing_pos_coordinates != lis_pos_coordinates

    return TestData(**data)


def _geolocation_check_error(test_data: TestData) -> str:
    """Returns the real reason of failure for the Geolocation reference check."""
    if not test_data.esrp_chfe_invite_message:
        return "FAILED -> Outgoing ESRP to CHFE SIP INVITE message not found"
    return (
        "FAILED -> Outgoing ESRP to CHFE SIP INVITE doesn't contain incoming Geolocation value.\n"
        f"Actual list: {test_data.outgoing_geolocations}\n"
        f"Expected in list: {test_data.stimulus_geolocation}"
    )


def _pidf_check_error(test_data: TestData) -> str:
    """Returns the real reason of failure for the PIDF-LO forwarding check."""
    if not test_data.lis_request_message:
        request_name = (
            "SIP SUBSCRIBE"
            if test_data.variation_number == LocationVariation.SIP
            else "HTTP POST location request"
        )
        return (
            "FAILED -> Unable to check outgoing INVITE for LIS PIDF-LO: "
            f"ESRP did not send {request_name} to Test System LIS"
        )
    if not test_data.esrp_chfe_invite_message:
        return (
            "FAILED -> Unable to check outgoing INVITE for LIS PIDF-LO: "
            "ESRP to CHFE SIP INVITE message not found"
        )
    return (
        "FAILED -> Outgoing ESRP to CHFE SIP INVITE contains PIDF-LO XML body "
        "received from Test System LIS"
    )


def get_test_names() -> list:
    return [
        "Verify that ESRP sends HTTP POST location request to Test System LIS",
        "Verify that ESRP sends SIP SUBSCRIBE location request to Test System LIS",
        "Verify that outgoing ESRP to CHFE SIP INVITE message is present",
        "Verify that outgoing ESRP to CHFE SIP INVITE contains the same Geolocation reference as the incoming one",
        "Verify that outgoing ESRP to CHFE SIP INVITE does not contain PIDF-LO XML body received from Test System LIS",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, run_variation
    )

    has_valid_stimulus = (
        bool(test_data.stimulus_message) and test_data.variation_number is not None
    )
    stimulus_precondition_error = (
        NOT_RUN if not test_data.stimulus_message else NOT_RUN_VARIATION
    )

    # PIDF-LO check is NOT RUN only when ESRP sent the request but the LIS stub did not answer
    is_lis_stub_missing = (
        bool(test_data.lis_request_message) and not test_data.has_lis_pidflo
    )
    pidf_precondition = has_valid_stimulus and not is_lis_stub_missing
    pidf_precondition_error = (
        stimulus_precondition_error if not has_valid_stimulus else NOT_RUN_NO_LIS_PIDFLO
    )

    check_list = []

    if test_data.variation_number == LocationVariation.REF_URL:
        check_list.append(
            TestCheck(
                test_name="Verify that ESRP sends HTTP POST location request to Test System LIS",
                test_method=is_data_present,
                precondition=has_valid_stimulus,
                precondition_error=stimulus_precondition_error,
                test_params={
                    "test_data": test_data.lis_request_message,
                    "error": "FAILED -> No ESRP to LIS HTTP POST location request found",
                },
            )
        )

    if test_data.variation_number == LocationVariation.SIP:
        check_list.append(
            TestCheck(
                test_name="Verify that ESRP sends SIP SUBSCRIBE location request to Test System LIS",
                test_method=is_data_present,
                precondition=has_valid_stimulus,
                precondition_error=stimulus_precondition_error,
                test_params={
                    "test_data": test_data.lis_request_message,
                    "error": "FAILED -> No ESRP to LIS SIP SUBSCRIBE location request found",
                },
            )
        )

    check_list.extend(
        [
            TestCheck(
                test_name="Verify that outgoing ESRP to CHFE SIP INVITE message is present",
                test_method=is_data_present,
                precondition=has_valid_stimulus,
                precondition_error=stimulus_precondition_error,
                test_params={
                    "test_data": test_data.esrp_chfe_invite_message,
                    "error": "FAILED -> Outgoing ESRP to CHFE SIP INVITE message not found",
                },
            ),
            TestCheck(
                test_name="Verify that outgoing ESRP to CHFE SIP INVITE contains the same Geolocation reference as the incoming one",
                test_method=is_data_present,
                precondition=has_valid_stimulus,
                precondition_error=stimulus_precondition_error,
                test_params={
                    "test_data": test_data.stimulus_geolocation
                    in test_data.outgoing_geolocations,
                    "error": _geolocation_check_error(test_data),
                },
            ),
            TestCheck(
                test_name="Verify that outgoing ESRP to CHFE SIP INVITE does not contain PIDF-LO XML body received from Test System LIS",
                test_method=is_data_present,
                precondition=pidf_precondition,
                precondition_error=pidf_precondition_error,
                test_params={
                    "test_data": test_data.is_no_pidf_in_outgoing,
                    "error": _pidf_check_error(test_data),
                },
            ),
        ]
    )

    return check_list
