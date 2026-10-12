from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.test_config import MessageFilter


def get_filter_parameters_var_other(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param lab_config: LabConfig instance
    :param filtering_options: list of MessageFilter
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
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
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )
