from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from checks.general.checks import is_test_data_the_same
from checks.http.lost_checks.checks import test_if_geolocation_included_in_find_service
from services.test_services.test_assessment_service import TestCheck
from services.aux_services.xml_services import extract_location_from_text

from test_suite.checks.general.checks import (
    test_if_parameter_has_one_of_expected_values,
)
from test_suite.enums import TransportProtocolEnum


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
) -> tuple[str, str, str, str, str, str, str, bool | None]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip,
    expected_response_code, is_tls_variation)
    """
    stimulus = None
    other = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    out_dst_port_tcp = None
    out_dst_port_tls = None
    expected_response_code = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        elif message.message_type == FilterMessageType.OTHER.value:
            other = message
            expected_response_code = message.response_status_code

    is_tls_variation = any(
        message.get("type") == "HTTPS" for message in variation.params["messages"]
    )

    if stimulus and other:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == other.src_interface:
                    out_scr_ip = interface.ip
                elif interface.name == other.dst_interface:
                    out_dst_ip = interface.ip
                    for interface_port in interface.port_mapping:
                        if (
                            interface_port.transport_protocol
                            == TransportProtocolEnum.TCP
                        ):
                            out_dst_port_tcp = str(interface_port.port)
                        elif (
                            interface_port.transport_protocol
                            == TransportProtocolEnum.TLSV1_2
                        ):
                            out_dst_port_tls = str(interface_port.port)
                        elif (
                            interface_port.transport_protocol
                            == TransportProtocolEnum.TLSV1_3
                        ):
                            out_dst_port_tls = str(interface_port.port)
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_scr_ip is None
            or out_dst_ip is None
            or expected_response_code is None
            or out_dst_port_tcp is None
            or out_dst_port_tls is None
        ):
            raise WrongConfigurationError(
                "Lab Config file error - src and dst ip addresses not found or port numbers"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                expected_response_code,
                out_dst_port_tcp,
                out_dst_port_tls,
                is_tls_variation,
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
) -> list:
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        expected_response_code,
        out_dst_port_tcp,
        out_dst_port_tls,
        is_tls_variation,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    stimulus_geolocation = None
    find_service_request = None
    port_value = None
    response_code = None
    request_transport = None

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
        ),
    )

    if stimulus_message:
        stimulus_geolocation = stimulus_message.sip.get("xml_cdata", None)

        output_message = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=out_scr_ip,
                dst_ip=out_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.POST],
                after_timestamp=float(stimulus_message.sniff_timestamp),
            ),
        )

        if output_message:
            if hasattr(output_message, "http") and hasattr(
                output_message.http, "file_data"
            ):
                hex_data = output_message.http.file_data.replace(":", "")
                byte_data = bytes.fromhex(hex_data)
                message_body = byte_data.decode("ascii", errors="ignore")
                find_service_request = extract_location_from_text(message_body)

            if hasattr(output_message, "tcp") and hasattr(
                output_message.tcp, "dstport"
            ):
                port_value = output_message.tcp.dstport
            if hasattr(output_message, "transport_layer"):
                request_transport = output_message.transport_layer

    return [
        is_tls_variation,
        stimulus_geolocation,
        find_service_request,
        port_value,
        expected_response_code,
        response_code,
        out_dst_port_tcp,
        out_dst_port_tls,
        request_transport,
    ]


def get_test_names() -> list:
    return [
        "Verify that 'findService' contains geolocations from received SIP INVITE",
        "Verify that correct port number is used by ESRP according to transport method",
        "Validate if correct transport is used",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        is_tls_variation,
        stimulus_geolocation,
        find_service_request,
        port_value,
        expected_response_code,
        response_code,
        expected_tcp_port,
        expected_tls_port,
        request_transport,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Verify that 'findService' contains geolocations from received SIP INVITE",
            test_method=test_if_geolocation_included_in_find_service,
            test_params={
                "parameter_value": find_service_request,
                "expected_value": stimulus_geolocation,
            },
        ),
        TestCheck(
            test_name="Verify that correct port number is used by ESRP according to transport method",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": (
                    expected_tls_port if is_tls_variation else expected_tcp_port
                ),
                "actual_data": str(port_value),
                "error": f"Port doesn't match."
                f"Expected port is {expected_tls_port if is_tls_variation else expected_tcp_port};"
                f"Actual port is {port_value}",
            },
        ),
        TestCheck(
            test_name="Validate if correct transport is used",
            test_method=test_if_parameter_has_one_of_expected_values,
            test_params={
                "parameter_name": "LoST request transport type",
                "parameter_value": request_transport,
                "expected_values": (
                    [
                        TransportProtocolEnum.TLSV1_2.value,
                        TransportProtocolEnum.TLSV1_3.value,
                    ]
                    if is_tls_variation
                    else [TransportProtocolEnum.TCP.value]
                ),
            },
        ),
    ]
