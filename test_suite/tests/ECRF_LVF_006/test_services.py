from checks.http.checks import validate_response_code_class
from services.aux_services.aux_services import is_valid_timestamp
from services.aux_services.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter, extract_json_data_from_http, \
    get_messages
from services.aux_services.test_list_services import find_path_value
from services.aux_services.xml_services import extract_xml_body_string_from_file, extract_all_values_for_xml_tag_name
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ECRF_LVF_006.checks import validate_ecrf_response_data


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str, list, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    variation_url = None
    variation_scenario = None
    message_method = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    if 'messages' in getattr(variation, 'params', None):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get('response_code', None)
                if config_response_code and not expected_response_code:
                    expected_response_code = config_response_code.lower()

    for param in variation.params:
        if param == 'messages':
            for message in variation.params['messages']:
                variation_scenario = message.get('body')
                variation_url = find_path_value(message.get('prep_steps', None))
                message_from_config = message.get('method', None)
                if message_from_config:
                    if "GET".lower() in message_from_config.lower():
                        message_method = [HTTPMethodEnum.GET, ]
                    elif "POST".lower() in message_from_config.lower():
                        message_method = [HTTPMethodEnum.POST, ]

    if stimulus and expected_response_code:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return (stimulus_src_ip, stimulus_dst_ip, variation_url, variation_scenario, message_method,
                    expected_response_code)
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_url, variation_scenario, message_method, expected_response_code = (
        get_filter_parameters(lab_config, filtering_options, variation))

    xml_tag_as_of = None
    response_data = None
    response_code = None

    xml_request = extract_xml_body_string_from_file(variation_scenario.removeprefix("file."))
    if xml_request:
        xml_tag_as_of_result = extract_all_values_for_xml_tag_name(xml_request, 'asOf')
        if xml_tag_as_of_result:
            xml_tag_as_of = xml_tag_as_of_result[0] if isinstance(xml_tag_as_of_result, list) else xml_tag_as_of_result

    # Variation 3/4
    if variation_url == '/PlannedChangePoll':
        ecrf_lvf_requests = get_messages(pcap_service,
                                         FilterConfig(
                                             src_ip=stimulus_src_ip,
                                             dst_ip=stimulus_dst_ip,
                                             packet_type=PacketTypeEnum.HTTP,
                                             message_method=message_method
                                         )
                                         )
        stimulus_messages = [message for message in ecrf_lvf_requests
                             if hasattr(message.http, 'request_uri')
                             and variation_url in message.http.request_uri]
        if stimulus_messages:
            ecrf_lvf_responses = get_messages(pcap_service,
                                              FilterConfig(
                                                  src_ip=stimulus_dst_ip,
                                                  dst_ip=stimulus_src_ip,
                                                  packet_type=PacketTypeEnum.HTTP,
                                              )
                                              )
            ok_and_json_response_list = [message for message in ecrf_lvf_responses
                                         if hasattr(message.http, 'response_code')
                                         and message.http.response_code == '200']

            response_code = '200' if ok_and_json_response_list else None
            json_responses = [extract_json_data_from_http(message) for message in ok_and_json_response_list]

            if len(stimulus_messages) > 1:
                if len(set(json_responses)) > 1:
                    response_data = json_responses
                else:
                    # If there is no response data matching for Variation #4-> create an empty set() as flag that this
                    # is Variation #4
                    response_data = set()
            else:
                if json_responses and isinstance(json_responses[0], str):
                    response_data = json_responses[0]
        return response_data, response_code, expected_response_code, variation_url, xml_tag_as_of

    else:
        out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=message_method
            ),
            uri=variation_url,
        )

        response_code = out_message.http.response_code if getattr(out_message, 'http', None) is not None \
            else None

        if expected_response_code != '4xx' and out_message:
            # Variation #1
            if hasattr(out_message, 'xml'):
                decoded_data = bytes.fromhex(
                    out_message.http.file_data.replace(":", "")
                ).decode("utf-8")
                result_data_list = extract_all_values_for_xml_tag_name(
                    decoded_data, 'findServiceResponse'
                )
                for result in result_data_list:
                    if is_valid_timestamp(result):
                        response_data = result
                        break
            # Variation #5
            elif hasattr(out_message, 'json'):
                response_data = extract_json_data_from_http(out_message)

            return response_data, response_code, expected_response_code, variation_url, xml_tag_as_of
        # Variations #2/6
        else:
            return None, response_code, expected_response_code, None, None


def get_test_names() -> list:
    return [
        f"Validate 4xx error response",
        f"Validate ECRF-LVF response for any correct request",
    ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options: list[MessageFilter],
                  variation: RunVariation) -> list:
    (
        response_data,
        response_code,
        expected_response_code,
        variation_url,
        xml_tag_as_of
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    # Variations #2/6
    if expected_response_code == '4xx':
        return [
            TestCheck(
                test_name=f"Validate 4xx error response",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": expected_response_code,
                    "response_code": response_code
                }
            )
        ]
    # Variations #1/3/4/5
    else:
        return [
            TestCheck(
                test_name="Validate ECRF-LVF response for any correct request",
                test_method=validate_ecrf_response_data,
                test_params={
                    "response_data": response_data,
                    "expected_response_code": expected_response_code,
                    "response_code": response_code,
                    "variation_url": variation_url,
                    "xml_tag_as_of": xml_tag_as_of
                }
            )
        ]
