from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.test_config import MessageFilter


def get_filter_parameters_var_one(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param lab_config: LabConfig instance
    :param filtering_options: list of MessageFilter
    :return: Tuple of filtering parameters
        (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip)
    """

    messages_by_type = {m.message_type: m for m in filtering_options}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)
    output = messages_by_type.get(FilterMessageType.OUTPUT)

    if not (stimulus and output):
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    ip_by_interface_name = {}

    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface_name[interface.name] = interface.ip

    stimulus_src_ip = ip_by_interface_name.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface_name.get(stimulus.dst_interface)
    out_src_ip = ip_by_interface_name.get(output.src_interface)
    out_dst_ip = ip_by_interface_name.get(output.dst_interface)

    if None in (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip):
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
    )
