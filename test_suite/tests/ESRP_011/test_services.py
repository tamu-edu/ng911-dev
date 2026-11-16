from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_011.checks import validate_mime_integrity


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
) -> tuple[str, str, str, str]:
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip)
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_src_ip = None
    out_dst_ip = None

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_src_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_src_ip is None
            or out_dst_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip
    else:
        raise WrongConfigurationError(
            "Stimulus and output messages must be provided in filtering options"
        )


def get_test_names() -> list:
    return ["MIME Integrity Validation"]


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
) -> tuple:
    stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip = get_filter_parameters(
        lab_config, filtering_options, variation
    )

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            packet_type=PacketTypeEnum.SIP,
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            message_method=[SIPMethodEnum.INVITE],
        ),
    )

    output_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            packet_type=PacketTypeEnum.SIP,
            src_ip=out_src_ip,
            dst_ip=out_dst_ip,
            message_method=[SIPMethodEnum.INVITE],
        ),
    )

    return stimulus_message, output_message


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_message,
        output_message,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="MIME Integrity Validation",
            test_method=validate_mime_integrity,
            test_params={
                "stimulus_message": stimulus_message,
                "output_message": output_message,
            },
        )
    ]
