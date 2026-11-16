from dataclasses import dataclass

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation
from services.config.types.test_config import MessageFilter
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_019.checks import (
    validate_refer_to_sip_uri,
    validate_service_urn_prefix,
    validate_service_urn_quoted,
    validate_single_refer_to,
    validate_single_service_urn,
)
from tests.CHFE_019.constants import (
    NOT_RUN,
    SERVICE_URNS,
    VARIATIONS,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param lab_config: LabConfig instance
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :return: Tuple of filtering parameters
        (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip)
    """
    messages_by_type = {m.message_type: m for m in filtering_options or []}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)

    if not (stimulus and output):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    ip_by_interface_name = {}
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface_name[interface.name] = interface.ip

    stimulus_src_ip = ip_by_interface_name.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface_name.get(stimulus.dst_interface)
    out_src_ip = ip_by_interface_name.get(output.src_interface)
    out_dst_ip = ip_by_interface_name.get(output.dst_interface)

    if None in (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip


@dataclass
class TestData:
    """
    Holds data gathered from the PCAP required for CHFE_019 checks.
    """

    stimulus_message: Packet | None = None
    refer_message: Packet | None = None
    is_refer_to_present: bool = False
    refer_to_count: int = 0
    refer_to_uri: str | None = None
    refer_to_raw: str | None = None
    service_urn: str | None = None


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
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("chfe_esrp", out_src_ip, out_dst_ip)

    data = {}

    # Find the initial ESRP -> CHFE INVITE.
    stimulus_message, stimulus_ts = fetcher.get_first_sip_invite(
        "esrp_chfe",
        return_timestamp=True,
    )

    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    stimulus_sip = SipMessage.from_packet(stimulus_message)

    if not stimulus_sip:
        return TestData(**data)

    # Find CHFE -> ESRP REFER belonging to the same SIP dialog.
    refer_message = fetcher.get_first_sip_refer(
        "chfe_esrp",
        after_timestamp=stimulus_ts,
        call_id=stimulus_sip.call_id,
    )

    data["refer_message"] = refer_message

    if not refer_message:
        return TestData(**data)

    refer_sip = SipMessage.from_packet(refer_message)

    if not refer_sip or not refer_sip.refer_to:
        return TestData(**data)

    data["is_refer_to_present"] = True

    refer_to = refer_sip.refer_to[0]
    data["refer_to_count"] = len(refer_sip.refer_to)
    data["refer_to_uri"] = refer_to.uri
    data["refer_to_raw"] = refer_to.raw
    data["service_urn"] = refer_to.service_urn

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Validate SIP REFER message from CHFE to ESRP is present",
        "Validate Refer-To header field is present",
        "Validate exactly one Refer-To header field is present",
        "Validate Refer-To URI is a SIP URI",
        "Validate Refer-To contains exactly one serviceurn parameter",
        "Validate Refer-To serviceurn parameter is a quoted string",
        "Validate Refer-To serviceurn parameter contains suitable service URN",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    if run_variation.name not in VARIATIONS:
        raise VariationNotFoundError(
            f"Unknown variation name: '{run_variation.name}'\n"
            f"Expected variation names by Test Case: {', '.join(VARIATIONS)}"
        )

    test_data = get_test_parameters(
        pcap_service,
        lab_config,
        filtering_options,
        run_variation,
    )

    return [
        TestCheck(
            test_name="Validate SIP REFER message from CHFE to ESRP is present",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.refer_message,
                "error": "FAILED -> SIP REFER message from CHFE to ESRP not found",
            },
        ),
        TestCheck(
            test_name="Validate Refer-To header field is present",
            test_method=is_data_present,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_refer_to_present,
                "error": "FAILED -> Refer-To header field is not present",
            },
        ),
        TestCheck(
            test_name="Validate exactly one Refer-To header field is present",
            test_method=validate_single_refer_to,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "refer_message": test_data.refer_message,
                "refer_to_count": test_data.refer_to_count,
            },
        ),
        TestCheck(
            test_name="Validate Refer-To URI is a SIP URI",
            test_method=validate_refer_to_sip_uri,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "refer_message": test_data.refer_message,
                "refer_to_uri": test_data.refer_to_uri,
            },
        ),
        TestCheck(
            test_name="Validate Refer-To contains exactly one serviceurn parameter",
            test_method=validate_single_service_urn,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "refer_message": test_data.refer_message,
                "refer_to_raw": test_data.refer_to_raw,
            },
        ),
        TestCheck(
            test_name="Validate Refer-To serviceurn parameter is a quoted string",
            test_method=validate_service_urn_quoted,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "refer_message": test_data.refer_message,
                "refer_to_raw": test_data.refer_to_raw,
            },
        ),
        TestCheck(
            test_name="Validate Refer-To serviceurn parameter contains suitable service URN",
            test_method=validate_service_urn_prefix,
            precondition=test_data.stimulus_message,
            precondition_error=NOT_RUN,
            test_params={
                "refer_message": test_data.refer_message,
                "service_urn": test_data.service_urn,
                "allowed_urns": SERVICE_URNS,
            },
        ),
    ]
