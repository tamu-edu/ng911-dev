from typing import Literal

from checks.general.checks import is_data_present
from checks.http.checks import validate_response_code
from services.aux_services.message_services import (
    get_http_response_containing_string_in_http_body_for_message_matching_filter,
    get_handshake_protocol_type,
    get_cipher_suite_values_list,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    get_first_message_matching_filter,
    get_messages,
)
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_010.checks import (
    is_both_client_and_server_hello_present,
    is_cipher_suites_hello_has_sha_256,
    is_server_hello_contain_sha_256_from_client_hello,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
) -> tuple[
    str,
    str,
    str | None,
    str | None,
    str | None,
    Literal[PacketTypeEnum.SIP, PacketTypeEnum.HTTP],
    list[SIPMethodEnum] | list[HTTPMethodEnum],
    str | None,
]:
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
    packet_type = None
    message_method = None
    http_header = None
    expected_response_code = None

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
            if message.sip_method == "INVITE":
                message_method = [SIPMethodEnum.INVITE]
                packet_type = PacketTypeEnum.SIP
            else:
                message_method = [HTTPMethodEnum.POST]
                packet_type = PacketTypeEnum.HTTP
                http_header = message.header_contains
                expected_response_code = message.response_status_code
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                if output:
                    if interface.name == output.src_interface:
                        out_src_ip = interface.ip
                    elif interface.name == output.dst_interface:
                        out_dst_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or packet_type is None
            or message_method is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_src_ip,
                out_dst_ip,
                expected_response_code,
                packet_type,
                message_method,
                http_header,
            )
    else:
        raise WrongConfigurationError(
            "Stimulus and output messages must be provided in filtering options"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
) -> tuple:
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        expected_response_code,
        packet_type,
        message_method,
        http_header,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    bcf_4xx_response_code = None
    client_cipher_suite_values_list = None
    server_cipher_suite_values_list = None
    server_hello_timestamp = None
    output_message = None

    ########## TLS ##########
    tls_messages = get_messages(
        pcap_service,
        FilterConfig(),
    )

    for message in tls_messages:
        if hasattr(message, "tls"):
            handshake_protocol_type = get_handshake_protocol_type(message)
            if handshake_protocol_type:
                if (
                    "Client" in handshake_protocol_type
                    and client_cipher_suite_values_list is None
                ):
                    client_cipher_suite_values_list = get_cipher_suite_values_list(
                        message
                    )
                if (
                    "Server" in handshake_protocol_type
                    and server_cipher_suite_values_list is None
                ):
                    server_cipher_suite_values_list = get_cipher_suite_values_list(
                        message
                    )
                    server_hello_timestamp = float(message.sniff_timestamp)
            if client_cipher_suite_values_list and server_cipher_suite_values_list:
                break

    if server_hello_timestamp:
        # For variation #2 (HTTPS)
        if http_header:
            bcf_http_response = get_http_response_containing_string_in_http_body_for_message_matching_filter(
                pcap_service,
                FilterConfig(
                    packet_type=packet_type,
                    src_ip=stimulus_src_ip,
                    dst_ip=stimulus_dst_ip,
                    message_method=message_method,
                    after_timestamp=server_hello_timestamp,
                ),
                uri=http_header,
            )

            if bcf_http_response and hasattr(bcf_http_response.http, "response_code"):
                bcf_4xx_response_code = bcf_http_response.http.response_code

            return (
                expected_response_code,
                bcf_4xx_response_code,
                output_message,
                client_cipher_suite_values_list,
                server_cipher_suite_values_list,
            )

        # Variation 1 (SIP_over_TLS)
        else:
            output_message = get_first_message_matching_filter(
                pcap_service,
                FilterConfig(
                    packet_type=packet_type,
                    src_ip=out_src_ip,
                    dst_ip=out_dst_ip,
                    message_method=message_method,
                    after_timestamp=server_hello_timestamp,
                ),
            )
            return (
                expected_response_code,
                bcf_4xx_response_code,
                output_message,
                client_cipher_suite_values_list,
                server_cipher_suite_values_list,
            )

    print("⚠️ WARNING -> TLS handshake not found in pcap. Client/Server Hello missing.")
    return expected_response_code, None, None, None, None


def get_test_names() -> list:
    return [
        "Validate BOTH Client and Server Hello are found",
        "Validate ClientHello contain Cipher Suites with SHA-256 only",
        "Validate that Server Hello contain Cipher Suite with SHA-256",
        "Validate BCF initiates SIP INVITE call after successful handshake",
        "Validate BCF response with HTTPS 433 error for bad actors",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        expected_response_code,
        bcf_4xx_response_code,
        output_message,
        client_cipher_suite_values_list,
        server_cipher_suite_values_list,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    test_checks = [
        TestCheck(
            test_name="Validate BOTH Client and Server Hello are found",
            test_method=is_both_client_and_server_hello_present,
            test_params={
                "client_hello": client_cipher_suite_values_list,
                "server_hello": server_cipher_suite_values_list,
            },
        ),
        TestCheck(
            test_name="Validate ClientHello contain Cipher Suites with SHA-256 only",
            test_method=is_cipher_suites_hello_has_sha_256,
            test_params={
                "hello_list": client_cipher_suite_values_list,
            },
        ),
        TestCheck(
            test_name="Validate that Server Hello contain Cipher Suite with SHA-256",
            test_method=is_server_hello_contain_sha_256_from_client_hello,
            test_params={
                "client_hello": client_cipher_suite_values_list,
                "server_hello": server_cipher_suite_values_list,
            },
        ),
    ]
    # Variation #2
    if expected_response_code:
        test_checks.append(
            TestCheck(
                test_name="Validate BCF response with HTTPS 433 error for bad actors",
                test_method=validate_response_code,
                test_params={
                    "expected_response_code": expected_response_code,
                    "response_code": bcf_4xx_response_code,
                },
            )
        )
    # Variation #1
    else:
        test_checks.append(
            TestCheck(
                test_name="Validate BCF initiates SIP INVITE call after successful handshake",
                test_method=is_data_present,
                test_params={
                    "test_data": output_message,
                    "error": "FAILED -> SIP INVITE from BCF to Test System ESRP not found",
                },
            ),
        )
    return test_checks
