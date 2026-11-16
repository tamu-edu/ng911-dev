from typing import Literal

from services.aux_services.message_services import (
    get_handshake_types,
    get_cipher_suite_values_list,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    get_messages,
)
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_010.checks import (
    validate_both_client_and_server_hello_present,
    validate_cipher_suites_hello_has_sha_256,
    validate_server_hello_contain_sha_256_from_client_hello,
    validate_cipher_suites_hello_containing_aes_256_or_better,
)

from test_suite.tests.BCF_010.constants import (
    CLIENT_HELLO_TSHARK_HANDSHAKE_TYPE,
    SERVER_HELLO_TSHARK_HANDSHAKE_TYPE,
)


def get_client_and_server_cipher_suite_values_lists(
    tls_messages,
) -> tuple[list | None, list | None]:
    client_cipher_suite_values_list = None
    server_cipher_suite_values_list = None
    for message in tls_messages or []:
        if hasattr(message, "tls"):
            handshake_types = get_handshake_types(message)
            if (
                client_cipher_suite_values_list is None
                and CLIENT_HELLO_TSHARK_HANDSHAKE_TYPE in handshake_types
            ):
                client_cipher_suite_values_list = get_cipher_suite_values_list(message)
            if (
                server_cipher_suite_values_list is None
                and SERVER_HELLO_TSHARK_HANDSHAKE_TYPE in handshake_types
            ):
                server_cipher_suite_values_list = get_cipher_suite_values_list(message)
            if (
                client_cipher_suite_values_list is not None
                and server_cipher_suite_values_list is not None
            ):
                break
    return client_cipher_suite_values_list, server_cipher_suite_values_list


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
    str | None,
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
    log_output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_src_ip = None
    out_dst_ip = None
    log_out_src_ip = None
    log_out_dst_ip = None
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
        elif message.message_type == FilterMessageType.OTHER:
            log_output = message
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
                if log_output:
                    if interface.name == log_output.src_interface:
                        log_out_src_ip = interface.ip
                    elif interface.name == log_output.dst_interface:
                        log_out_dst_ip = interface.ip
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
                log_out_src_ip,
                log_out_dst_ip,
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
        log_out_src_ip,
        log_out_dst_ip,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    ########## TLS ##########
    tls_osp_bcf_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip_list=[stimulus_src_ip, stimulus_dst_ip],
            dst_ip_list=[stimulus_src_ip, stimulus_dst_ip],
        ),
    )

    tls_bcf_esrp_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip_list=[out_src_ip, out_dst_ip], dst_ip_list=[out_src_ip, out_dst_ip]
        ),
    )

    tls_bcf_log_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip_list=[log_out_src_ip, log_out_dst_ip],
            dst_ip_list=[log_out_src_ip, log_out_dst_ip],
        ),
    )

    client_cipher_suite_values_list_osp_bcf, server_cipher_suite_values_list_osp_bcf = (
        get_client_and_server_cipher_suite_values_lists(tls_osp_bcf_messages)
    )
    (
        client_cipher_suite_values_list_bcf_esrp,
        server_cipher_suite_values_list_bcf_esrp,
    ) = get_client_and_server_cipher_suite_values_lists(tls_bcf_esrp_messages)
    client_cipher_suite_values_list_bcf_log, server_cipher_suite_values_list_bcf_log = (
        get_client_and_server_cipher_suite_values_lists(tls_bcf_log_messages)
    )
    return (
        expected_response_code,
        client_cipher_suite_values_list_osp_bcf,
        server_cipher_suite_values_list_osp_bcf,
        client_cipher_suite_values_list_bcf_esrp,
        server_cipher_suite_values_list_bcf_esrp,
        client_cipher_suite_values_list_bcf_log,
        server_cipher_suite_values_list_bcf_log,
    )


def get_test_names() -> list:
    return [
        "Validate BOTH Client and Server Hello are found for OSP-BCF",
        "Validate BOTH Client and Server Hello are found for BCF-ESRP",
        "Validate BOTH Client and Server Hello are found for BCF-LOG",
        "Validate ClientHello contain Cipher Suites with SHA-256 only",
        "Validate that Server Hello contain Cipher Suite with SHA-256",
        "Validate that ClientHello from BCF to ESRP contains AES-256 Cipher Suites or better",
        "Validate that ClientHello from BCF to LOG contains AES-256 Cipher Suites or better",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        expected_response_code,
        client_cipher_suite_values_list_osp_bcf,
        server_cipher_suite_values_list_osp_bcf,
        client_cipher_suite_values_list_bcf_esrp,
        server_cipher_suite_values_list_bcf_esrp,
        client_cipher_suite_values_list_bcf_log,
        server_cipher_suite_values_list_bcf_log,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    test_checks = [
        TestCheck(
            test_name="Validate BOTH Client and Server Hello are found for OSP-BCF",
            test_method=validate_both_client_and_server_hello_present,
            test_params={
                "client_hello": client_cipher_suite_values_list_osp_bcf,
                "server_hello": server_cipher_suite_values_list_osp_bcf,
            },
        ),
        TestCheck(
            test_name="Validate ClientHello contain Cipher Suites with SHA-256 only",
            test_method=validate_cipher_suites_hello_has_sha_256,
            test_params={
                "hello_list": client_cipher_suite_values_list_osp_bcf,
            },
        ),
        TestCheck(
            test_name="Validate that Server Hello contain Cipher Suite with SHA-256",
            test_method=validate_server_hello_contain_sha_256_from_client_hello,
            test_params={
                "client_hello": client_cipher_suite_values_list_osp_bcf,
                "server_hello": server_cipher_suite_values_list_osp_bcf,
            },
        ),
    ]
    # Variation #1
    if not expected_response_code:
        test_checks.append(
            TestCheck(
                test_name="Validate BOTH Client and Server Hello are found for BCF-ESRP",
                test_method=validate_both_client_and_server_hello_present,
                test_params={
                    "client_hello": client_cipher_suite_values_list_bcf_esrp,
                    "server_hello": server_cipher_suite_values_list_bcf_esrp,
                },
            )
        )
        test_checks.append(
            TestCheck(
                test_name="Validate BOTH Client and Server Hello are found for BCF-LOG",
                test_method=validate_both_client_and_server_hello_present,
                test_params={
                    "client_hello": client_cipher_suite_values_list_bcf_log,
                    "server_hello": server_cipher_suite_values_list_bcf_log,
                },
            )
        )
        test_checks.append(
            TestCheck(
                test_name="Validate that ClientHello from BCF to ESRP contains AES-256 Cipher Suites or better",
                test_method=validate_cipher_suites_hello_containing_aes_256_or_better,
                test_params={
                    "hello_list": client_cipher_suite_values_list_bcf_esrp,
                },
            )
        )
        test_checks.append(
            TestCheck(
                test_name="Validate that ClientHello from BCF to LOG contains AES-256 Cipher Suites or better",
                test_method=validate_cipher_suites_hello_containing_aes_256_or_better,
                test_params={
                    "hello_list": client_cipher_suite_values_list_bcf_log,
                },
            )
        )
    return test_checks
