from dataclasses import dataclass
from typing import Optional

from pyshark.packet.packet import Packet

from checks.general.checks import is_test_data_the_same
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
from tests.PS_017.constants import (
    NOT_RUN,
    NO_PS_RESPONSE,
    VARIATIONS,
    POLICIES_URL_PART,
    PUT_VARIATIONS,
    SETUP_POST_EXPECTED_CODE,
)


def get_filter_parameters(
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, expected_code)
    """
    messages_by_type = {m.message_type: m for m in filtering_options or []}
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

    return stimulus_src_ip, stimulus_dst_ip, expected_code


def _get_variation_number(variation: RunVariation) -> int:
    variation_number = VARIATIONS.get(variation.name)
    if variation_number is None:
        raise VariationNotFoundError(
            f"Unknown variation name: '{variation.name}'\n"
            f"Expected variation names by Test Case: '{VARIATIONS}'"
        )
    return variation_number


def _get_response_code(response: Optional[Packet]) -> Optional[str]:
    """Returns the HTTP status code of a response packet as a string, or None."""
    msg = HttpMessage.from_packet(response) if response else None
    return str(msg.status_code) if msg and msg.status_code is not None else None


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Optional[Packet] = None
    ps_response: Optional[Packet] = None
    ps_response_code: Optional[str] = None
    expected_code: Optional[str] = None
    setup_post_message: Optional[Packet] = None
    setup_post_response: Optional[Packet] = None
    setup_post_response_code: Optional[str] = None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation_number: int,
) -> TestData:
    stimulus_src_ip, stimulus_dst_ip, expected_code = get_filter_parameters(
        lab_config, filtering_options
    )

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_ps", stimulus_src_ip, stimulus_dst_ip)

    data: dict = {"expected_code": expected_code}

    if variation_number in PUT_VARIATIONS:
        # Preliminary POST creating the policy, then the PUT stimulus after it
        setup_post, setup_post_ts = fetcher.get_first_http_post(
            "esrp_ps", return_timestamp=True, url_contains=POLICIES_URL_PART
        )
        data["setup_post_message"] = setup_post
        if not setup_post:
            return TestData(**data)

        setup_post_response = fetcher.get_http_response_for("ps_esrp", setup_post)
        data["setup_post_response"] = setup_post_response
        data["setup_post_response_code"] = _get_response_code(setup_post_response)

        stimulus_message = fetcher.get_first_http_put(
            "esrp_ps", after_timestamp=setup_post_ts, url_contains=POLICIES_URL_PART
        )
    else:
        stimulus_message = fetcher.get_first_http_post(
            "esrp_ps", url_contains=POLICIES_URL_PART
        )

    data["stimulus_message"] = stimulus_message
    if not stimulus_message:
        return TestData(**data)

    # Policy Store response to the stimulus request
    ps_response = fetcher.get_http_response_for("ps_esrp", stimulus_message)
    data["ps_response"] = ps_response
    data["ps_response_code"] = _get_response_code(ps_response)

    return TestData(**data)


def _setup_post_error(test_data: TestData) -> Optional[str]:
    """Returns the NOT RUN reason if the preliminary POST did not create the policy, else None."""
    if not test_data.setup_post_message:
        return "NOT RUN -> No preliminary HTTP POST creating the policy found"
    if not test_data.setup_post_response:
        return "NOT RUN -> No Policy Store response to the preliminary HTTP POST found"
    if test_data.setup_post_response_code != SETUP_POST_EXPECTED_CODE:
        return (
            "NOT RUN -> Preliminary HTTP POST was not accepted by Policy Store. "
            f"Expected: {SETUP_POST_EXPECTED_CODE}, Actual: {test_data.setup_post_response_code}"
        )
    return None


def get_test_names() -> list:
    return [
        "Verify that Policy Store responded with 201 code",
        "Verify that Policy Store responded with 4xx code",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    variation_number = _get_variation_number(variation)
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation_number
    )

    has_stimulus = bool(test_data.stimulus_message)
    has_response = has_stimulus and bool(test_data.ps_response)

    # PUT variations: NOT RUN if the preliminary POST did not create the policy
    setup_error = (
        _setup_post_error(test_data) if variation_number in PUT_VARIATIONS else None
    )

    # Response code checks: NOT RUN without setup or stimulus, FAILED without response
    if setup_error:
        precondition_error = setup_error
    elif not has_stimulus:
        precondition_error = NOT_RUN
    else:
        precondition_error = NO_PS_RESPONSE
    response_precondition = {
        "precondition": not setup_error and has_response,
        "precondition_error": precondition_error,
    }

    if variation_number != 1:
        return [
            TestCheck(
                test_name="Verify that Policy Store responded with 4xx code",
                test_method=validate_response_code_class,
                **response_precondition,
                test_params={
                    "expected_response_code_class": test_data.expected_code,
                    "response_code": test_data.ps_response_code,
                },
            )
        ]

    return [
        TestCheck(
            test_name="Verify that Policy Store responded with 201 code",
            test_method=is_test_data_the_same,
            **response_precondition,
            test_params={
                "expected_data": test_data.expected_code,
                "actual_data": test_data.ps_response_code,
            },
        )
    ]
