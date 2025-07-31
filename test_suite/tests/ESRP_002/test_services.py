from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum

from services.test_services.test_assessment_service import TestCheck

from services.aux_services.xml_services import extract_location_from_text
from tests.ESRP_002.checks import verify_location_and_dereferencing


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation) -> tuple[
    str, str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip,
                                            xml_sender_data_path), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    xml_sender_data_path = ''

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT.value:
            output = message

    # !NOTE:SENSITIVE DATA TO CHANGES IN ESRP_002 run_config.yaml file
    try:
        if variation.params['messages'][1].get('sipp_scenario', None):
            xml_sender_data_path = variation.params['messages'][1]['sipp_scenario']["scenario_file_path"]
        else:
            body = variation.params['messages'][1].get('body', None)
            if body:
                xml_sender_data_path = body
        if xml_sender_data_path:
            xml_sender_data_path = xml_sender_data_path.removeprefix('file.')
    except AttributeError:
        pass

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_scr_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
        if (stimulus_src_ip is None or stimulus_dst_ip is None
                or out_scr_ip is None or out_dst_ip is None):
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, xml_sender_data_path
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> tuple:
    (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, http_stub_server_response_path) = (
        get_filter_parameters(lab_config, filtering_options, variation))

    # Get XML data from original variation sipp scenario file
    content = ''
    if http_stub_server_response_path:
        try:
            with open(http_stub_server_response_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except FileNotFoundError:
            print(f'File_path: {http_stub_server_response_path} not found')

    # Extract location from XML file which will be used as reference to compare.
    location = extract_location_from_text(content)

    # Getting HTTP GET (LoST) from ESRP to ECRF-LVF
    geolocation_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.GET, ]
        )
    )

    return location, geolocation_request


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    geolocation_incoming_data, geolocation_request, = get_test_parameters(pcap_service,
                                                                          lab_config,
                                                                          filtering_options,
                                                                          variation)

    return [
        TestCheck(
            test_name="Verify receiving location and dereferencing",
            test_method=verify_location_and_dereferencing,
            test_params={
                "geolocation_request": geolocation_request,
                "geolocation_incoming_data": geolocation_incoming_data,
            }
        )
    ]
