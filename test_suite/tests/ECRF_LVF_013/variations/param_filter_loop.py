from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter
from tests.ECRF_LVF_013.constants import (
    ECRF_LVF_TO_TS_INTERFACE,
    TS_TO_ECRF_LVF_INTERFACE,
)


def _get_interface_ip(lab_config: LabConfig, interface_name: str):
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            if interface.name == interface_name:
                return interface.ip
    return None


def get_filter_parameters_loop(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Filtering params for the loop detection variations, where only a STIMULUS
    filtering option is configured in the Run Config. The recursive query towards
    Test System ECRF-LVF must never happen, but the pcap file is still searched
    for it, so its IPs are derived from the well-known interface names.
    :param lab_config: LabConfig instance
    :param filtering_options: list of MessageFilter
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip)
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message

    if not stimulus:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    for entity in lab_config.entities:
        for interface in entity.interfaces:
            if interface.name == stimulus.src_interface:
                stimulus_src_ip = interface.ip
            elif interface.name == stimulus.dst_interface:
                stimulus_dst_ip = interface.ip

    if stimulus_src_ip is None or stimulus_dst_ip is None:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    output_src_ip = _get_interface_ip(lab_config, ECRF_LVF_TO_TS_INTERFACE)
    output_dst_ip = _get_interface_ip(lab_config, TS_TO_ECRF_LVF_INTERFACE)

    return stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip
