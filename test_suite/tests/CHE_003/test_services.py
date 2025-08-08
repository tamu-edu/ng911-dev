from bcp47 import bcp47

from services.aux_services.aux_services import get_messages
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHE_003.checks import validate_language_response


def get_filter_parameters(lab_config: LabConfig,
                          filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, expected_response_code, request_method),
    all are strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    request_method = None

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
                request_method = message.get('action', None)

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None or request_method is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip, expected_response_code, request_method
    else:
        raise WrongConfigurationError("It seems that the RunConfig does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, expected_response_code, request_method = get_filter_parameters(lab_config,
                                                                                                     filtering_options,
                                                                                                     variation)

    sip_invite_messages_response = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
            )
        )
    if not sip_invite_messages_response:
        return False, request_method
    for message in sip_invite_messages_response:
        try:
            if message.sip.status_code != expected_response_code:
                continue
            lang_attrs = message.sip.get('sdp_media_attribute_value', None)
            if lang_attrs:
                return all([lang in bcp47.tags for lang in lang_attrs.split(" ")]), request_method
        except AttributeError:
            continue
    return False, request_method


def get_test_names() -> list:
    return [
        f"Validate SDP answer from CHE.",
        f"Validate SDP offer from CHE for outgoing calls",
    ]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        is_languages_included, request_method
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    if request_method == 'send':
        test_name = "Validate SDP answer from CHE."
    else:
        test_name = "Validate SDP offer from CHE for outgoing calls"

    return [
        TestCheck(
            test_name=test_name,
            test_method=validate_language_response,
            test_params={
                "response_result": is_languages_included,
            }
        )
    ]
