from services.aux_services.sip_services import extract_message_data
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_first_message_matching_filter, get_messages
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.LIS_003.checks import validate_lis_responses_distance_filter, validate_lis_responses_speed_filter, \
    validate_lis_responses_element_val_change_filter, validate_lis_responses_entering_area_change_filter, \
    validate_lis_responses_location_type_change_filter


def get_variation(message):
    decoded_message = extract_message_data(message)
    if 'moved' in decoded_message:
        return 'distance_filter'
    if 'dyn:speed' in decoded_message:
        return 'speed_filter'
    if 'ca:country' in decoded_message:
        return 'element_value_filter'
    if 'enterOrExit' in decoded_message:
        return 'entering_area_filter'
    if 'locationType' in decoded_message:
        return 'location_type_filter'


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter]) -> tuple[str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

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
            return stimulus_src_ip, stimulus_dst_ip

    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter]) -> list or None:
    stimulus_src_ip, stimulus_dst_ip = get_filter_parameters(lab_config, filtering_options)

    sip_notify_messages = None

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

    variation_name = None
    if sip_subscribe_message:
        variation_name = get_variation(sip_subscribe_message)

    return sip_subscribe_message, sip_notify_messages, variation_name


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:

    sip_subscribe, sip_notify_messages, variation_name = get_test_parameters(pcap_service,
                                                                             lab_config,
                                                                             filtering_options)
    if variation_name == 'distance_filter':
        return [
            TestCheck(
                test_name="Validate LIS location filters by distance",
                test_method=validate_lis_responses_distance_filter,
                test_params={
                    'subscribe_msg': sip_subscribe,
                    "responses": sip_notify_messages
                }
            ),]
    if variation_name == 'speed_filter':
        return [
            TestCheck(
                test_name="Validate LIS speed filters by distance",
                test_method=validate_lis_responses_speed_filter,
                test_params={
                    'subscribe_msg': sip_subscribe,
                    "responses": sip_notify_messages
                }
            ),]
    if variation_name == 'element_value_filter':
        return [
            TestCheck(
                test_name="Validate LIS elements value change filters by distance",
                test_method=validate_lis_responses_element_val_change_filter,
                test_params={
                    'subscribe_msg': sip_subscribe,
                    "responses": sip_notify_messages
                }
            ),
        ]
    if variation_name == 'entering_area_filter':
        return [
            TestCheck(
                test_name="Validate LIS entering area filters by distance",
                test_method=validate_lis_responses_entering_area_change_filter,
                test_params={
                    'subscribe_msg': sip_subscribe,
                    "responses": sip_notify_messages
                }
            ),]
    if variation_name == 'location_type_filter':
        return [
            TestCheck(
                test_name="Validate LIS location type filters by distance",
                test_method=validate_lis_responses_location_type_change_filter,
                test_params={
                    "responses": sip_notify_messages
                }
            )
        ]
