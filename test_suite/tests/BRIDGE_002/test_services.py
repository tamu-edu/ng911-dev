from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.message_services import get_messages
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BRIDGE_002.checks import validate_bridge_state_response_data


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter])\
        -> tuple[str, str]:
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
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter]) -> str or None:
    stimulus_src_ip, stimulus_dst_ip = get_filter_parameters(lab_config, filtering_options)

    sip_invite_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.SUBSCRIBE, ]
            )
        )
    if sip_invite_message:
        try:
            out_timestamp = float(sip_invite_message.sniff_timestamp)
        except AttributeError:
            return None

        if out_timestamp:
            messages_after_timestamp = get_messages(
                pcap_service,
                FilterConfig(
                    src_ip=stimulus_dst_ip,
                    dst_ip=stimulus_src_ip,
                    message_method=[SIPMethodEnum.OK, ],
                    after_timestamp=out_timestamp
                )
            )
        else:
            return None

        if messages_after_timestamp:
            for message in messages_after_timestamp:
                try:
                    if "NOTIFY" in messages_after_timestamp[1].sip.cseq:
                        return message
                except AttributeError:
                    return None
        else:
            return None


def get_test_names() -> list:
    return [f"Validate BRIDGE state response", ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        sip_response
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)
    return [
        TestCheck(
            test_name="Validate BRIDGE state response",
            test_method=validate_bridge_state_response_data,
            test_params={
                "sip_response": sip_response,
            }
        )
    ]
