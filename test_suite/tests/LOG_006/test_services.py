from checks.http.checks import validate_response_code_class
from services.aux_services.message_services import (
    get_http_response_containing_string_in_http_body_for_message_matching_filter,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.LOG_005.checks import (
    validate_response_json_body_for_http_get_on_log_event_ids_entry_point,
)
from tests.LOG_006.constants import CALL_ID


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, variation_url,
    message_method, expected_response_code), strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    variation_url = None
    message_method = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    if "messages" in getattr(variation, "params", []):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get("response_code", None)
                if config_response_code and not expected_response_code:
                    expected_response_code = config_response_code.lower()

    for param in variation.params:
        if param == "messages":
            for message in variation.params["messages"]:
                variation_url = message.get("http_url", None)
                message_method = message.get("method", None)

    if stimulus and expected_response_code:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError(
                "Lab Config file error - src and dst ip addresses not found"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                variation_url,
                message_method,
                expected_response_code,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        variation_url,
        message_method,
        expected_response_code,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    out_message = (
        get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[
                    HTTPMethodEnum.GET,
                ],
            ),
            uri=variation_url,
        )
    )
    response_code = (
        out_message.http.response_code
        if getattr(out_message, "http", None) is not None
        else None
    )

    is_additional_parameters = False
    if expected_response_code != "4xx":
        return (
            out_message,
            response_code,
            expected_response_code,
            is_additional_parameters,
        )

    if (
        len(variation_url) > 10
    ):  # if it /CallIds + some additional parameters like incidentId/startTime/endTime
        is_additional_parameters = True
    return None, response_code, expected_response_code, is_additional_parameters


def get_test_names() -> list:
    return [
        "Validate 4xx error response",
        "Validate 200 OK + JSON response for /CallIds correct request",
        "Validate 200 OK + JSON response for /CallIds with additional parameters",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    test_response, response_code, expected_response_code, is_additional_parameters = (
        get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    )

    # Verification of 4XX invalid responses
    if str(expected_response_code) == "4xx":
        return [
            TestCheck(
                test_name="Validate 4xx error response",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": expected_response_code,
                    "response_code": response_code,
                },
            )
        ]

    else:
        # Verification of 200 OK response for /CallIds + additional parameters (incidentId/startTime/endTime)
        if is_additional_parameters:
            return [
                TestCheck(
                    test_name="Validate 200 OK + JSON response for /CallIds with additional parameters",
                    test_method=validate_response_json_body_for_http_get_on_log_event_ids_entry_point,
                    test_params={
                        "response": test_response,
                        "additional_element": {"callIds": (list, dict, tuple)},
                        "array_name": "CallIdArray",
                        "id_name": "callIds",
                        "call_id": CALL_ID,
                    },
                )
            ]
        # Verification of 200 OK response for /CallIds
        else:
            return [
                TestCheck(
                    test_name="Validate 200 OK + JSON response for any correct request",
                    test_method=validate_response_json_body_for_http_get_on_log_event_ids_entry_point,
                    test_params={
                        "response": test_response,
                        "additional_element": {"callIds": (list, dict, tuple)},
                        "array_name": "CallIdArray",
                        "id_name": "callIds",
                    },
                )
            ]
