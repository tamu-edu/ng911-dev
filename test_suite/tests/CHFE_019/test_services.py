from dataclasses import dataclass

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation
from services.config.types.test_config import MessageFilter
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_019.checks import validate_service_urn_prefix
from tests.CHFE_019.constants import NOT_RUN, SERVICE_URN_PREFIXES
from tests.CHFE_019.variations.param_filter_var_one import (
    get_filter_parameters_var_one,
)


@dataclass
class TestData:
    """
    Holds data gathered from the PCAP required for CHFE_019 checks.
    """

    stimulus_message: Packet | None = None
    refer_message: Packet | None = None
    is_refer_to_present: bool = False
    service_urn: str | None = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
) -> TestData:
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        _out_src_ip,
        _out_dst_ip,
    ) = filtering_data

    fetcher = PacketFetcher(pcap_service)

    fetcher.add_route(
        "esrp_chfe",  # stimulus
        stimulus_src_ip,
        stimulus_dst_ip,
    )

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
    data["service_urn"] = refer_to.service_urn

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Validate SIP REFER message from CHFE to ESRP is present",
        "Validate Refer-To header field is present",
        "Validate Refer-To serviceurn parameter is present",
        "Validate Refer-To serviceurn parameter contains suitable service URN",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:
    if run_variation.name != "Refer_To_serviceurn_parameter":
        raise VariationNotFoundError(
            f"Unknown variation name: '{run_variation.name}'\n"
            "Expected variation name by Test Case: 'Refer_To_serviceurn_parameter'"
        )

    filtering_data = get_filter_parameters_var_one(
        lab_config,
        filtering_options,
    )

    test_data = get_test_parameters(
        pcap_service,
        filtering_data,
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
            precondition=test_data.refer_message,
            precondition_error="NOT RUN -> SIP REFER message not found.",
            test_params={
                "test_data": test_data.is_refer_to_present,
                "error": "FAILED -> Refer-To header field is not present",
            },
        ),
        TestCheck(
            test_name="Validate Refer-To serviceurn parameter is present",
            test_method=is_data_present,
            precondition=test_data.is_refer_to_present,
            precondition_error="NOT RUN -> Refer-To header field is not present.",
            test_params={
                "test_data": test_data.service_urn,
                "error": "FAILED -> Refer-To serviceurn parameter is not present",
            },
        ),
        TestCheck(
            test_name="Validate Refer-To serviceurn parameter contains suitable service URN",
            test_method=validate_service_urn_prefix,
            precondition=test_data.service_urn,
            precondition_error="NOT RUN -> Refer-To serviceurn parameter is not present.",
            test_params={
                "service_urn": test_data.service_urn,
                "allowed_prefixes": SERVICE_URN_PREFIXES,
            },
        ),
    ]
