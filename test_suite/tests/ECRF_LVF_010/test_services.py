from dataclasses import dataclass

from services.aux_services.json_services import get_jws_data
from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
    get_messages,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ECRF_LVF_010.checks import (
    validate_sip_service_state_event_notification_package,
    validate_service_state,
    validate_event_members,
    validate_security_posture,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    key_filepath = None
    cert_filepath = None
    ecrf_fqdn = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
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
                        out_scr_ip = interface.ip
                        ecrf_fqdn = interface.fqdn
                        key_filepath = entity.certificate_key
                        cert_filepath = entity.certificate_file
                    elif interface.name == output.dst_interface:
                        out_dst_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_scr_ip is None
            or out_dst_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        elif not ecrf_fqdn:
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required FQDN records for ECRF-LVF interfaces"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                key_filepath,
                cert_filepath,
                ecrf_fqdn,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


@dataclass
class TestData:
    pass


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    ecrf_to_esrp_initial_notify_json = None
    ecrf_to_logger_http_post_message = None
    ecrf_to_logger_post_data = None
    ecrf_to_esrp_second_notify_json = None

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        key_filepath,
        cert_filepath,
        ecrf_fqdn,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.SUBSCRIBE,
            ],
        ),
    )

    stimulus_timestamp = getattr(stimulus_message, "sniff_timestamp", 0)

    ecrf_to_esrp_initial_notify_state_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.NOTIFY,
            ],
            after_timestamp=stimulus_timestamp,
        ),
    )

    if ecrf_to_esrp_initial_notify_state_message:
        message_content = extract_all_contents_from_message_body(
            ecrf_to_esrp_initial_notify_state_message
        )
        if message_content:
            ecrf_to_esrp_initial_notify_json = message_content[0].get("body", "")

    ecrf_to_logger_http_post_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
            after_timestamp=stimulus_timestamp,
        ),
    )

    if ecrf_to_logger_http_post_messages:
        for message in ecrf_to_logger_http_post_messages:
            if hasattr(message, "http") and hasattr(message.http, "file_data"):
                jws, key_found = get_jws_data(message, key_filepath)
                if (
                    not ecrf_to_logger_http_post_message
                    and jws
                    and jws.get("logEventType") == "ServiceStateChangeLogEvent"
                ):
                    ecrf_to_logger_post_data = jws
                    ecrf_to_logger_http_post_message = message

                if ecrf_to_logger_http_post_message and ecrf_to_logger_post_data:
                    break

    post_to_logger_timestamp = getattr(
        ecrf_to_logger_http_post_message, "sniff_timestamp", 0
    )

    ecrf_to_esrp_notify_second_state_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.NOTIFY,
            ],
            after_timestamp=post_to_logger_timestamp,
        ),
    )

    if ecrf_to_esrp_notify_second_state_message:
        message_content = extract_all_contents_from_message_body(
            ecrf_to_esrp_notify_second_state_message
        )
        if message_content:
            ecrf_to_esrp_second_notify_json = message_content[0].get("body", "")

    test_data = TestData()

    test_data.stimulus_message = stimulus_message
    test_data.ecrf_to_esrp_initial_notify_state_message = (
        ecrf_to_esrp_initial_notify_state_message
    )
    test_data.ecrf_to_esrp_initial_notify_json = ecrf_to_esrp_initial_notify_json
    test_data.ecrf_to_logger_http_post_message = ecrf_to_logger_http_post_message
    test_data.ecrf_to_logger_post_data = ecrf_to_logger_post_data
    test_data.ecrf_to_esrp_notify_second_state_message = (
        ecrf_to_esrp_notify_second_state_message
    )
    test_data.ecrf_to_esrp_second_notify_json = ecrf_to_esrp_second_notify_json
    test_data.ecrf_fqdn = ecrf_fqdn

    return test_data


def get_test_names() -> list:
    return [
        "Validation of server-side SIP ServiceState event notification package",
        "Validation of notification security posture value changed according to the logging newSecurityPosture value.",
        "Validation of the notification serviceState according to the logging newState value.",
        "Validation of ServiceStateChangeLogEvent of ECRF-LVF logging event members.",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation
    )

    checks = [
        TestCheck(
            test_name="Validation of server-side SIP ServiceState event notification package",
            test_method=validate_sip_service_state_event_notification_package,
            test_params={
                "test_data": test_data,
            },
        ),
        TestCheck(
            test_name="Validation of ServiceStateChangeLogEvent of ECRF-LVF logging event members.",
            test_method=validate_event_members,
            test_params={
                "test_data": test_data,
            },
        ),
    ]

    variant_one_name = (
        "Logging of ServiceStateChangeLogEvent on ECRF-LVF Security Posture change"
    )
    test_data.is_variant_one = False

    if variation.name == variant_one_name:
        test_data.is_variant_one = True
        checks.append(
            TestCheck(
                test_name="Validation of notification security posture value changed according to the logging newSecurityPosture value.",
                test_method=validate_security_posture,
                test_params={
                    "test_data": test_data,
                },
            ),
        )
    else:
        checks.append(
            TestCheck(
                test_name="Validation of the notification serviceState according to the logging newState value.",
                test_method=validate_service_state,
                test_params={
                    "test_data": test_data,
                },
            ),
        )

    return checks
