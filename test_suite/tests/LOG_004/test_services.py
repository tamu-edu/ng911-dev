from enum import Enum

from checks.http.checks import validate_response_code_class
from services.aux.message_services import get_http_response_containing_string_in_http_body_for_message_matching_filter
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter
from services.config.types.test_config import Test as TestConfig
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_conduction_service import TestCheck
from tests.LOG_004.checks import validate_response_json_for_http_get_to_logevents_entrypoint, \
    validate_json_body_for_log_events


class RequestVariations(Enum):
    # TODO read data from config
    INCORRECT_LOG_EVENT_ID = '/LogEvents/test123'
    EMPTY_LOG_EVENT = '/LogEvents'
    CORRECT_LOG_IVENT_ID = '/LogEvents/test_log_1'


# TODO take certs from config
pca_key = 'pcaps/LOG_004/PCA.key'
self_signed_key = 'pcaps/LOG_004/bcf.ng911.test-self_signed.key'
subject_alt_name_key = 'pcaps/LOG_004/bcf.ng911.test-alt_name.key'

# TODO remove this section
scenarios_config = {'pass': subject_alt_name_key,
                    'fail': subject_alt_name_key,
                    'fail2': subject_alt_name_key,
                    'fail3': self_signed_key}


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter]) -> tuple[str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT.value:
            output = message

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None :
            raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                          "parameters for osp_ip, bcf_ip, esrp_ip addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter]) -> dict:
    response_codes_or_response_data = {}
    stimulus_src_ip, stimulus_dst_ip = get_filter_parameters(lab_config, filtering_options)
    for request in RequestVariations:
        out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.GET, ]
            ),
            uri=request.value
        )
        if request.name == 'INCORRECT_LOG_EVENT_ID':
            response_codes_or_response_data[request.name] = out_message.http.response_code
        else:
            # TODO remove this
            pcap_variation_name = pcap_service.capture.input_filepath.name.split('TC_LOG_004_')[1][:-5]
            scenarios_file_path = scenarios_config[pcap_variation_name]

            response_codes_or_response_data[request.name] = (out_message, scenarios_file_path, pca_key, pcap_variation_name)
    return response_codes_or_response_data


def get_test_list(pcap_service: PcapCaptureService, test_config: TestConfig, lab_config: LabConfig) -> list:
    (
        http_response_codes_or_response_data
    ) = get_test_parameters(pcap_service, test_config, lab_config)
    return [
        TestCheck(
            test_name="Validate 4xx error response for HTTP GET request with incorrect logEventId.",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.INCORRECT_LOG_EVENT_ID.name]
            }
        ),
        TestCheck(
            test_name="Validate JSON body from HTTP 200 OK response for HTTP GET request to /LogEvents entrypoint.",
            test_method=validate_json_body_for_log_events,
            test_params={
                "response": http_response_codes_or_response_data[RequestVariations.EMPTY_LOG_EVENT.name][0],
                "scen_filepath": http_response_codes_or_response_data[RequestVariations.EMPTY_LOG_EVENT.name][1],
                "pca_key": http_response_codes_or_response_data[RequestVariations.EMPTY_LOG_EVENT.name][2],
                "pcap": http_response_codes_or_response_data[RequestVariations.EMPTY_LOG_EVENT.name][3],

            }
        ),
        TestCheck(
            test_name="Validate JWS body from HTTP 200 OK response for HTTP GET request with correct logEventId.",
            test_method=validate_response_json_for_http_get_to_logevents_entrypoint,
            test_params={
                "response": http_response_codes_or_response_data[RequestVariations.EMPTY_LOG_EVENT.name][0],
                "scen_filepath": http_response_codes_or_response_data[RequestVariations.EMPTY_LOG_EVENT.name][1],
                "pca_key": http_response_codes_or_response_data[RequestVariations.EMPTY_LOG_EVENT.name][2],
                "pcap":  http_response_codes_or_response_data[RequestVariations.EMPTY_LOG_EVENT.name][3],
            }
        )
    ]