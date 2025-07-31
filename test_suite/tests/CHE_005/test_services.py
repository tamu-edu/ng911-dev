from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.message_services import get_messages
from services.aux_services.sip_msg_body_services import get_sip_media_attributes
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHE_005.checks import validate_che_response_code


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, exp_resp_code), strings
    """
    stimulus = None
    expected_response_code = None
    stimulus_src_ip = None
    stimulus_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    if 'messages' in getattr(variation, 'params', None):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get('response_code', None)
                if config_response_code and not expected_response_code:
                    expected_response_code = config_response_code.lower()

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
            return stimulus_src_ip, stimulus_dst_ip, expected_response_code
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> str or None:
    stimulus_src_ip, stimulus_dst_ip, expected_response_code = get_filter_parameters(lab_config,
                                                                                     filtering_options,
                                                                                     variation)

    sip_invite_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
            )
        )
    out_timestamp = None
    call_id = None
    if sip_invite_message:
        out_timestamp = float(sip_invite_message.sniff_timestamp)
        call_id = sip_invite_message.sip.get('call_id')

    if out_timestamp:
        invite_media_attrs = get_sip_media_attributes(sip_invite_message)
        messages_after_timestamp = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                message_method=[SIPMethodEnum.INVITE, ],
                after_timestamp=out_timestamp
            )
        )
    else:
        return None, None, None

    for out_message in messages_after_timestamp:
        try:
            if (out_message.sip.status_code == expected_response_code and
                    out_message.sip.get('call_id') == call_id):
                resp_media_attrs = get_sip_media_attributes(out_message)
                return out_message.sip.status_code, invite_media_attrs, resp_media_attrs
        except AttributeError:
            continue
    return None, None, None


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        response_code, expected_media_attrs, actual_media_attrs
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Validate CHE response for SIP INVITE",
            test_method=validate_che_response_code,
            test_params={
                "response_code": response_code,
                "expected_media_attrs": expected_media_attrs,
                "actual_media_attrs": actual_media_attrs
            }
        )
    ]
