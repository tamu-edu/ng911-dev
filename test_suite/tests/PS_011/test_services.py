from services.aux_services.message_services import (
    get_handshake_protocol_type,
    get_cipher_suite_values_list,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_messages
from enums import PacketTypeEnum
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
]:
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, packet_type, message_method, http_header)
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None

    for message in filtering_options or []:
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
        return (
            stimulus_src_ip,
            stimulus_dst_ip,
        )
    else:
        raise WrongConfigurationError(
            "Stimulus message must be provided in filtering options"
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
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    client_cipher_suite_values_list = None
    server_cipher_suite_values_list = None

    ts_esrp_messages = get_messages(
        pcap_service,
        FilterConfig(
            packet_type=PacketTypeEnum.TCP,
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
        ),
    )

    ps_messages = get_messages(
        pcap_service,
        FilterConfig(
            packet_type=PacketTypeEnum.TCP,
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
        ),
    )

    for message in ts_esrp_messages + ps_messages:
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
            if client_cipher_suite_values_list and server_cipher_suite_values_list:
                break

    if not (client_cipher_suite_values_list and server_cipher_suite_values_list):
        print(
            "⚠️ WARNING -> TLS handshake not found in pcap. Client/Server Hello missing."
        )

    return (
        client_cipher_suite_values_list,
        server_cipher_suite_values_list,
    )


def get_test_names() -> list:
    return [
        "Validate BOTH Client and Server Hello are found",
        "Validate ClientHello contain Cipher Suites with SHA-256 only",
        "Validate that Server Hello contain Cipher Suite with SHA-256",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        client_cipher_suite_values_list,
        server_cipher_suite_values_list,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
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
