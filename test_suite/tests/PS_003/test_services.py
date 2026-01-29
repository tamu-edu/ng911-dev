from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation, MessageFilter
from services.pcap_service import PcapCaptureService, FilterConfig
from tests.PS_003.checks import validate_version_int_values, validate_version_service_info, validate_version_vendor
from services.aux_services.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter, extract_json_data_from_http
from enums import PacketTypeEnum
from services.test_services.test_assessment_service import TestCheck
from checks.http.checks import is_type


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, variation_url, message_method), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    variation_url = None
    message_method = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                variation_url = message.get('http_url', None)
                message_method = message.get('method', None)

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip, variation_url, message_method
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> dict:
    stimulus_src_ip, stimulus_dst_ip, variation_url, message_method = (
        get_filter_parameters(lab_config, filtering_options, variation))
    out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP
        ),
        uri=variation_url
    )

    out_message_json = None
    if out_message:
        out_message_json = extract_json_data_from_http(out_message)
    return out_message_json


def get_test_names() -> list:
    return [
         f"Verify if 'fingerprint' has string value",
         f"Verify if 'version' is an array",
         f"Verify if all 'versions' contain 'major' and 'minor' integer values",
         f"Verify if all 'versions' contain 'serviceInfo' with 'requiredAlgorithms' array of string values",
         f"Verify 'vendor' is present in version and is a string",
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter],
                  variation: RunVariation) -> list:

    http_response = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Verify if 'fingerprint' has string value",
            test_method=is_type,
            test_params={
                "param": http_response.get('fingerprint') if http_response else None,
                "param_name": "fingerprint",
                "expected_type": str
            }
        ),
        TestCheck(
            test_name="Verify if 'version' is an array",
            test_method=is_type,
            test_params={
                "param": http_response.get('versions') if http_response else None,
                "param_name": "versions",
                "expected_type": (list, dict)
            }
        ),
        TestCheck(
            test_name="Verify if all 'versions' contain 'major' and 'minor' integer values",
            test_method=validate_version_int_values,
            test_params={
                "response": http_response
            }
        ),
        TestCheck(
            test_name="Verify if all 'versions' contain 'serviceInfo' "
                      "with 'requiredAlgorithms' array of string values",
            test_method=validate_version_service_info,
            test_params={
                "response": http_response
            }
        ),
        TestCheck(
            test_name="Verify 'vendor' is present in version and is a string",
            test_method=validate_version_vendor,
            test_params={
                "response": http_response
            }
        )
    ]
