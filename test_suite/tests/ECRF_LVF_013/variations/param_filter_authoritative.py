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


def get_filter_parameters_authoritative(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Filtering params for the Authoritative and Recursive 'via' variations. A STIMULUS
    filtering option is always required in the Run Config. The Recursive variation
    also configures an OUTPUT filtering option; the Authoritative variation does not,
    so its output IPs are derived from the well-known interface names instead.
    :param lab_config: LabConfig instance
    :param filtering_options: list of MessageFilter
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip)
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    output_src_ip = None
    output_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

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
            elif output and interface.name == output.src_interface:
                output_src_ip = interface.ip
            elif output and interface.name == output.dst_interface:
                output_dst_ip = interface.ip

    if not output:
        output_src_ip = _get_interface_ip(lab_config, ECRF_LVF_TO_TS_INTERFACE)
        output_dst_ip = _get_interface_ip(lab_config, TS_TO_ECRF_LVF_INTERFACE)

    if (
        stimulus_src_ip is None
        or stimulus_dst_ip is None
        or output_src_ip is None
        or output_dst_ip is None
    ):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip
