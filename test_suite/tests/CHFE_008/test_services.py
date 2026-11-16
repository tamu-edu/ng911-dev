from pyshark.packet.packet import Packet

from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.message_services import get_messages
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_008.checks import validate_chfe_state_response_data


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
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
            raise WrongConfigurationError(
                "Lab Config file error - src and dst ip addresses not found"
            )
        else:
            return stimulus_src_ip, stimulus_dst_ip
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
) -> tuple[Packet, Packet, Packet] | None:

    subscribe_seq_num = None
    subscribe_seq_method = None
    subscribe_request = None
    subscribe_response = None

    stimulus_src_ip, stimulus_dst_ip = get_filter_parameters(
        lab_config, filtering_options
    )
    sip_subscribe_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.SUBSCRIBE,
            ],
        ),
    )
    if sip_subscribe_message:
        subscribe_request = sip_subscribe_message

        if hasattr(sip_subscribe_message.sip, "CSeq"):
            cseq_full = sip_subscribe_message.sip.get_field("CSeq")

            if cseq_full:
                parts = cseq_full.strip().split()
                subscribe_seq_num, subscribe_seq_method = parts

        try:
            out_timestamp = float(sip_subscribe_message.sniff_timestamp)
        except AttributeError:
            return None

        if out_timestamp:
            messages_after_timestamp = get_messages(
                pcap_service,
                FilterConfig(
                    src_ip=stimulus_dst_ip,
                    dst_ip=stimulus_src_ip,
                    after_timestamp=out_timestamp,
                ),
            )
        else:
            return None

        if messages_after_timestamp:
            try:
                for message in messages_after_timestamp:
                    if "SIP" in message and all(
                        hasattr(message.sip, x)
                        for x in ("status_code", "cseq", "status_line")
                    ):
                        if (
                            subscribe_seq_num
                            and subscribe_seq_num in message.sip.cseq
                            and not subscribe_response
                        ):
                            subscribe_response = message

                    if "SIP" in message and hasattr(message.sip, "cseq"):
                        if (
                            subscribe_seq_num
                            and "NOTIFY" in message.sip.cseq
                            and subscribe_seq_num in message.sip.cseq
                        ):
                            return (message, subscribe_request, subscribe_response)

            except AttributeError:
                return None
        else:
            return None
    return None


def get_test_names() -> list:
    return [
        "The PSAP MUST deploy a ServiceState notifier",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    sip_response_data = get_test_parameters(pcap_service, lab_config, filtering_options)
    return [
        TestCheck(
            test_name="The PSAP MUST deploy a ServiceState notifier",
            test_method=validate_chfe_state_response_data,
            test_params={
                "sip_response_data": sip_response_data,
            },
        )
    ]
