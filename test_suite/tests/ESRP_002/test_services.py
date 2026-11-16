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


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
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
    xml_sender_data_path = ""

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT.value:
            output = message

    for action in variation.params["messages"]:
        if_name = action.get("if_name", None)
        if if_name and if_name.startswith("IF_LIS"):
            message_type = action.get("type", None)
            if message_type == "HTTP":
                http_url = action.get("http_url", None)
                http_body = action.get("body", None)
                if http_url and http_body:
                    for url, body in zip(http_url, http_body):
                        if "location" in url:
                            xml_sender_data_path = body.removeprefix("file.")
            elif message_type == "SIP":
                sipp_scenario = action.get("sipp_scenario", None)
                xml_sender_data_path = (
                    sipp_scenario.get("scenario_file_path") if sipp_scenario else ""
                )
                xml_sender_data_path = (
                    xml_sender_data_path.removeprefix("file.")
                    if xml_sender_data_path
                    else ""
                )

    if not xml_sender_data_path:
        for action in variation.params["messages"]:
            if_name = action.get("if_name", None)
            if if_name and if_name.startswith("IF_BCF"):
                prep_steps = action.get("prep_steps", None)
                replace_string_in_file = [
                    m
                    for m in prep_steps
                    if m.get("method_name", "") == "replace_string_in_file"
                ]
                for step in replace_string_in_file:
                    kwargs = step.get("kwargs", None)
                    input_file = kwargs.get("input_file", None) if kwargs else None
                    if input_file and input_file.startswith(
                        "file.test_suite/test_files/SIPp_scenarios/"
                    ):
                        xml_sender_data_path = input_file.removeprefix("file.")

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
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_scr_ip is None
            or out_dst_ip is None
        ):
            raise WrongConfigurationError(
                "Lab Config file error - src and dst ip addresses not found"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                xml_sender_data_path,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        http_stub_server_response_path,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    # Get XML data from original variation sipp scenario file
    content = ""
    if http_stub_server_response_path:
        try:
            with open(http_stub_server_response_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except FileNotFoundError:
            print(f"File_path: {http_stub_server_response_path} not found")

    # Extract location from XML file which will be used as reference to compare.
    location = extract_location_from_text(content)

    # Getting HTTP POST (LoST) from ESRP to ECRF-LVF
    http_lost_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
        ),
    )

    return location, http_lost_request


def get_test_names() -> list:
    return [
        "Verify receiving location and dereferencing",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        dereferenced_geolocation_data,
        http_lost_request,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Verify receiving location and dereferencing",
            test_method=verify_location_and_dereferencing,
            test_params={
                "http_lost_request": http_lost_request,
                "dereferenced_geolocation_data": dereferenced_geolocation_data,
            },
        )
    ]
