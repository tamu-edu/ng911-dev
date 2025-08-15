import json
import re
from json import JSONDecodeError

from checks.http.checks import validate_response_code_class, validate_response_code, is_type
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.aux_services.json_services import get_payload_data_from_file
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.LOG_003.checks import validate_logger_response_data


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation)\
        -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip,
    expected_response_code, request_payload_path), all are strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    request_payload_path = None
    expected_response_code = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                request_payload_path = message.get('body', None).removeprefix('file.')

    if 'messages' in getattr(variation, 'params', None):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get('response_code', None)
                if config_response_code and not expected_response_code:
                    expected_response_code = config_response_code.lower()

    if stimulus and request_payload_path:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip,  str(expected_response_code), request_payload_path
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, expected_response_code, payload_path = get_filter_parameters(lab_config,
                                                                                                   filtering_options,
                                                                                                   variation)

    payload = get_payload_data_from_file(payload_path, 'plain')
    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST, ]
        ),
        str(payload),
    )

    response_code = None
    log_event_id = None
    log_id_string = None
    fqdn = None

    if hasattr(out_message, 'http') and hasattr(out_message.http, 'response_code'):
        response_code = out_message.http.response_code
    try:
        log_event_id = json.loads(out_message.json.object)['logEventId']

        match = re.search(r'logid:([^:]+):', log_event_id)
        log_id_string = match.group(1)

        fqdn = log_event_id.split(f'{log_id_string}:')[1]

        return response_code, expected_response_code, log_event_id, log_id_string, fqdn
    except AttributeError or JSONDecodeError:
        return response_code, expected_response_code, log_event_id, log_id_string, fqdn


def get_test_names() -> list:
    return [
        f"Validate 201 success response code for request.",
        f"Validate 201 response JSON data.",
        f"Verify logEventId is a string.",
        f"Validate 4xx error response code class for request."
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        http_response_codes_or_response_data, expected_response_code, log_event_id, log_id_string, fqdn
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    if '201' in expected_response_code:
        return [
            TestCheck(
                test_name="Validate 201 success response code for request.",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": expected_response_code,
                    "response": http_response_codes_or_response_data
                }
            ),
            TestCheck(
                test_name="Validate 201 response JSON data.",
                test_method=validate_logger_response_data,
                test_params={
                    "response": http_response_codes_or_response_data,
                    "log_event_id": log_event_id,
                    "log_id_string": log_id_string,
                    "fqdn": fqdn
                }
            ),
            TestCheck(
                test_name="Verify logEventId is a string.",
                test_method=is_type,
                test_params={
                    "param": log_event_id,
                    "param_name": "logEventId",
                    "expected_type": str,
                }
            )
        ]
    else:
        return [
            TestCheck(
                test_name="Validate 4xx error response code class for request.",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": 400,
                    "response": http_response_codes_or_response_data
                }
            )
        ]
