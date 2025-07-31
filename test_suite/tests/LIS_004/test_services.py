from checks.http.checks import validate_response_code_class
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_first_message_matching_filter, get_messages
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.LIS_004.checks import validate_lis_response_time_between_messages, extract_parameter_value


def get_filter_parameters(lab_config: LabConfig,
                          filtering_options: list[MessageFilter], variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip,
    stimulus_dst_ip, expected_response_code, scenario_file_path), strings

    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    expected_response_code = None
    scenario_file_path = None

    if 'messages' in getattr(variation, 'params', None):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get('response_code', None)
                if config_response_code and not expected_response_code:
                    expected_response_code = config_response_code.lower()

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for message in variation.params.get('messages'):
        sipp_scenario = message.get("sipp_scenario", None)
        scenario_file_path = sipp_scenario.get('scenario_file_path').removeprefix('file.') if sipp_scenario else None

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
            return stimulus_src_ip, stimulus_dst_ip, expected_response_code, scenario_file_path

    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> list or None:
    stimulus_src_ip, stimulus_dst_ip, expected_resp_code, scen_filepath = get_filter_parameters(lab_config,
                                                                                                filtering_options,
                                                                                                variation)

    sip_notify_messages = None
    lis_response_code = None
    variation_name = None
    param_value = None

    sip_subscribe_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.SUBSCRIBE, ]
        )
    )
    if sip_subscribe_message:
        sip_notify_messages = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[SIPMethodEnum.NOTIFY, ],
                after_timestamp=float(sip_subscribe_message.sniff_timestamp)
            )
        )

        if not expected_resp_code == '4xx':
            # Get XML data from original variation sipp scenario file
            if scen_filepath:
                try:
                    with open(scen_filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        for parameter in ['min-rate', 'max-rate', 'adaptive-min-rate']:
                            param_value = extract_parameter_value(content, parameter)
                            if param_value:
                                variation_name = parameter
                                break

                except FileNotFoundError:
                    print(f'File_path: {scen_filepath} not found')

        else:
            variation_name = '4xx_response'

    if expected_resp_code and expected_resp_code == '4xx' and sip_subscribe_message:
        response = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.SIP,
                after_timestamp=float(sip_subscribe_message.sniff_timestamp),
            )
        )
        if response and hasattr(response, 'sip') and hasattr(response.sip, 'status_code'):
            lis_response_code = response.sip.status_code

    return (sip_subscribe_message,
            sip_notify_messages,
            expected_resp_code,
            lis_response_code,
            variation_name,
            param_value)


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    (sip_subscribe,
     sip_notify_messages,
     expected_resp_code,
     lis_response,
     var_name,
     param_value) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    if expected_resp_code == '4xx':
        return [
            TestCheck(
                test_name="Validate LIS response with 4XX error code",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": expected_resp_code,
                    "response": lis_response
                }
            )
        ]
    else:
        return [
            TestCheck(
                test_name="Validate LIS response time between SIP NOTIFY messages",
                test_method=validate_lis_response_time_between_messages,
                test_params={
                    "subscribe_msgs": sip_subscribe,
                    "responses": sip_notify_messages,
                    "variation_name": var_name,
                    "param_value": param_value
                }
            )
        ]
