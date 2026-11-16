from dataclasses import dataclass

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present, is_test_data_the_same
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation, MessageFilter
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.pcap_service import PcapCaptureService

from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from checks.http.checks import validate_response_code_class
from tests.PS_015.constants import (
    NOT_RUN,
    NO_PS_RESPONSE,
    VARIATIONS,
    POST_SUCCESS_VARIATIONS,
    POST_ERROR_VARIATIONS,
    PUT_ERROR_VARIATIONS,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip)
    """
    messages_by_type = {m.message_type: m for m in filtering_options}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)

    if not stimulus:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    expected_code = stimulus.response_status_code
    if not expected_code:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "response_status_code value"
        )

    stimulus_endpoint = stimulus.header_contains or ""

    ip_by_interface_name = {}
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface_name[interface.name] = interface.ip

    stimulus_src_ip = ip_by_interface_name.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface_name.get(stimulus.dst_interface)

    required_ips = (
        stimulus_src_ip,
        stimulus_dst_ip,
    )
    if None in required_ips:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return stimulus_src_ip, stimulus_dst_ip, stimulus_endpoint, expected_code


def _get_variation_number(variation: RunVariation) -> int:
    variation_number = VARIATIONS.get(variation.name)
    if variation_number is None:
        raise VariationNotFoundError(
            f"Unknown variation name: '{variation.name}'\n"
            f"Expected variation names by Test Case: '{VARIATIONS}'"
        )
    return variation_number


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    expected_code: str = None
    ps_response_code: str | None = None
    stimulus_message: Packet | None = None
    ps_response: Packet | None = None
    variation_number: int | None = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    stimulus_src_ip, stimulus_dst_ip, stimulus_endpoint, expected_code = (
        get_filter_parameters(lab_config, filtering_options, variation)
    )

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_ps", stimulus_src_ip, stimulus_dst_ip)

    data: dict = {
        "variation_number": _get_variation_number(variation),
        "expected_code": expected_code,
    }

    # Get the stimulus message and its timestamp; the HTTP method (POST or PUT) depends on the variation
    http_method = "PUT" if data["variation_number"] in PUT_ERROR_VARIATIONS else "POST"

    stimulus_message, stimulus_ts = fetcher.get_first_http(
        "esrp_ps",
        return_timestamp=True,
        url_contains=stimulus_endpoint,
        message_method=http_method,
    )

    data["stimulus_message"] = stimulus_message
    if not stimulus_message:
        return TestData(**data)

    # Get First HTTP response from Policy Store and response code
    ps_response = fetcher.get_first_http("ps_esrp", after_timestamp=stimulus_ts)
    data["ps_response"] = ps_response
    ps_msg = HttpMessage.from_packet(ps_response) if ps_response else None
    data["ps_response_code"] = str(ps_msg.status_code) if ps_msg else None

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Verify that Policy Store response is present",
        "Verify that Policy Store responded with 201 code",
        "Verify that Policy Store responded with 4xx code on POST request",
        "Verify that Policy Store responded with 4xx code on PUT request",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation
    )

    has_stimulus = bool(test_data.stimulus_message)
    has_ps_response = has_stimulus and bool(test_data.ps_response)
    ps_response_precondition_error = NOT_RUN if not has_stimulus else NO_PS_RESPONSE

    check_list = [
        TestCheck(
            test_name="Verify that Policy Store response is present",
            test_method=is_data_present,
            precondition=has_stimulus,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.ps_response,
                "error": NO_PS_RESPONSE,
            },
        ),
    ]

    if test_data.variation_number in POST_SUCCESS_VARIATIONS:
        check_list.append(
            TestCheck(
                test_name="Verify that Policy Store responded with 201 code",
                test_method=is_test_data_the_same,
                precondition=has_ps_response,
                precondition_error=ps_response_precondition_error,
                test_params={
                    "expected_data": test_data.expected_code,
                    "actual_data": test_data.ps_response_code,
                    "error": "No Policy Store 201 Created response code found.",
                },
            )
        )

    if test_data.variation_number in POST_ERROR_VARIATIONS:
        check_list.append(
            TestCheck(
                test_name="Verify that Policy Store responded with 4xx code on POST request",
                test_method=validate_response_code_class,
                precondition=has_ps_response,
                precondition_error=ps_response_precondition_error,
                test_params={
                    "expected_response_code_class": test_data.expected_code,
                    "response_code": test_data.ps_response_code,
                },
            )
        )

    if test_data.variation_number in PUT_ERROR_VARIATIONS:
        check_list.append(
            TestCheck(
                test_name="Verify that Policy Store responded with 4xx code on PUT request",
                test_method=validate_response_code_class,
                precondition=has_ps_response,
                precondition_error=ps_response_precondition_error,
                test_params={
                    "expected_response_code_class": test_data.expected_code,
                    "response_code": test_data.ps_response_code,
                },
            )
        )

    return check_list
