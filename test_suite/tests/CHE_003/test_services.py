from bcp47 import bcp47

from services.aux.aux_services import get_messages
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.types.test_config import Test as TestConfig
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_conduction_service import TestCheck
from tests.CHE_003.checks import validate_language_response
from tests.CHE_003.constants import VARIATION_DESCRIPTIONS


def get_filter_parameters(lab_config: LabConfig,
                          filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str, str]:
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

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        if hasattr(message, 'response_status_code'):
            expected_response_code = message.response_status_code

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                          "parameters for osp_ip, bcf_ip, esrp_ip addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip, variation.name, expected_response_code
    else:
        raise WrongConfigurationError("It seems that the RunConfig does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, variation_name, expected_response_code = get_filter_parameters(lab_config,
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
        return False, variation_name
    for message in sip_invite_messages_response:
        if message.sip.status_code != expected_response_code:
            continue
        lang_attrs = message.sip.get('sdp_media_attribute_value', None)
        if lang_attrs:
            return all([lang in bcp47.tags for lang in lang_attrs.split(" ")]), variation_name
    return False, variation_name


def get_test_list(pcap_service: PcapCaptureService, test_config: TestConfig, lab_config: LabConfig,
                  variation: RunVariation) -> list:
    (
        is_languages_included, variation_name
    ) = get_test_parameters(pcap_service,  test_config, lab_config, variation)

    return [
        TestCheck(
            test_name=VARIATION_DESCRIPTIONS.get(variation_name, variation_name),
            test_method=validate_language_response,
            test_params={
                "response_result": is_languages_included,
            }
        )
    ]
