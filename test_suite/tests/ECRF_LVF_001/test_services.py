from services.aux_services.aux_services import get_messages
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ECRF_LVF_001.checks import validate_ecrf_lvf_certs_acceptance


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, method_name),strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    method_name = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            try:
                method_name = variation.params[param][0]['prep_steps'][0].get('method_name')
            except IndexError or KeyError:
                continue

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
            return stimulus_src_ip, stimulus_dst_ip, method_name
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> tuple or None:
    stimulus_src_ip, stimulus_dst_ip, method_name = get_filter_parameters(lab_config, filtering_options, variation)

    tcp_responses = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.TCP
        ),
    )
    has_app_data = None
    has_alert_message = None

    if tcp_responses:
        has_app_data = True if [record for record in tcp_responses if hasattr(record, 'tls')
                                and hasattr(record.tls, 'app_data')
                                and record.tls.app_data is not None] else False
        has_alert_message = True if [record for record in tcp_responses if hasattr(record, 'tls')
                                     and hasattr(record.tls, 'alert_message')
                                     and record.tls.alert_message is not None] else False

    return method_name, has_app_data, has_alert_message


def get_test_names() -> list:
    return [f"Verify ECRF-LVF accepts only PCA traceable certificates", ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    (
        method_name, has_app_data, has_alert_message
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Verify ECRF-LVF accepts only PCA traceable certificates",
            test_method=validate_ecrf_lvf_certs_acceptance,
            test_params={
                "variation_type": method_name,
                "has_app_data": has_app_data,
                "has_alert_message": has_alert_message
            }
        )
    ]
