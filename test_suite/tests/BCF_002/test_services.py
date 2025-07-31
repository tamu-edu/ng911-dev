from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_002.checks import validate_support_of_discrepancy_report


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter]) -> tuple[str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
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
            raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                          "parameters for osp_ip, bcf_ip, esrp_ip addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter]) -> tuple:

    stimulus_src_ip, stimulus_dst_ip = get_filter_parameters(lab_config, filtering_options)
    bcf_output_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.HTTP,
            http_status_code=201
        )
    )

    return bcf_output_message


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    bfc_out_mess = get_test_parameters(pcap_service, lab_config, filtering_options)
    return [
        TestCheck(
            test_name="Check if BCF supports Discrepancy Report function",
            test_method=validate_support_of_discrepancy_report,
            test_params={
                "output_message": bfc_out_mess
            }
        )
    ]


