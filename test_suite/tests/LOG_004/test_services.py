from checks.http.checks import validate_response_code_class
from services.aux_services.message_services import get_http_response_containing_string_in_http_body_for_message_matching_filter
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.LOG_004.checks import validate_response_json_for_http_get_to_logevents_entrypoint, \
    validate_json_body_for_log_events


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation)\
        -> tuple[str, str, str, str, str, str, str, dict]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, request_url, pca_file_path,
    pca_key_path, resp_code, entities_keys)
    """
    stimulus = None

    stimulus_src_ip = None
    stimulus_dst_ip = None
    request_url = None
    pca_file_path = lab_config.pca_certificate_file.removeprefix('file.')
    pca_key_path = lab_config.pca_certificate_key.removeprefix('file.')
    resp_code = None
    entities_keys = {}

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                resp_code = message.get('response_code', None)
                request_url = message.get('http_url', None)

    if stimulus and request_url:
        for entity in lab_config.entities:
            key_path = entity.certificate_key.removeprefix('file.')
            cert_path = entity.certificate_file.removeprefix('file.')
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                    entities_keys[interface.ip] = {'cert_path': cert_path,
                                                   'key_path': key_path}
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return (stimulus_src_ip, stimulus_dst_ip, request_url, pca_file_path, pca_key_path, resp_code,
                    variation.name, entities_keys)
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    (stimulus_src_ip, stimulus_dst_ip, variation_uri, pca_file_path, pca_file_cert, exp_resp_code, variation_name,
     entities_key_file_dict) = get_filter_parameters(lab_config, filtering_options, variation)

    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.GET, ]
        ),
        uri=variation_uri
    )
    if not out_message:
        return ('', pca_file_path, pca_file_cert, entities_key_file_dict[stimulus_src_ip], exp_resp_code,
                variation_name)

    if variation_name == 'LogEvents_request_incorrect_logEventId':
        return out_message.http.response_code, None, None, None, exp_resp_code, variation_name

    else:
        return (out_message, pca_file_path, pca_file_cert, entities_key_file_dict[stimulus_src_ip],
                exp_resp_code, variation_name)


def get_test_names() -> list:
    return [
         f"Validate 4xx error response",
         f"Validate JSON body from HTTP 200 OK response for HTTP GET request to /LogEvents entrypoint.",
         f"Validate JWS body from HTTP 200 OK response for HTTP GET request with correct logEventId.",
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        http_response_codes_or_response_data, pca_key, cert_file, entity_data, exp_resp_code, variation_name
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    if variation_name == 'LogEvents_request_incorrect_logEventId':
        return [
            TestCheck(
                test_name="Validate 4xx error response",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": exp_resp_code,
                    "response": http_response_codes_or_response_data
                }
            )
            ]
    elif variation_name == "LogEvents_request_with_logEventId":
        return [
            TestCheck(
                test_name="Validate JSON body from HTTP 200 OK response for HTTP GET request to /LogEvents entrypoint.",
                test_method=validate_json_body_for_log_events,
                test_params={
                    "response": http_response_codes_or_response_data,
                    "key_filepath": entity_data['key_path'],
                    "pca_key": pca_key,
                    "variation": variation_name

                }
            )
            ]
    else:
        return [
            TestCheck(
                test_name="Validate JWS body from HTTP 200 OK response for HTTP GET request with correct logEventId.",
                test_method=validate_response_json_for_http_get_to_logevents_entrypoint,
                test_params={
                    "response": http_response_codes_or_response_data,
                    "key_filepath": entity_data['key_path'],
                    "pca_key": pca_key,
                    "variation": variation_name
                }
            )
        ]
