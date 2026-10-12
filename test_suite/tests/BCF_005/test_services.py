from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_messages
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.BCF_005.checks import (
    validate_log_post_presence,
    validate_iut_sip_forwarding,
    validate_log_event_by_sip_type,
    validate_direction,
    analyze_sip_methods,
)
from tests.BCF_005.constants import LOG_EVENTS_URI, TEST_NAMES


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
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

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_src_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_src_ip is None
            or out_dst_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip = get_filter_parameters(
        lab_config, filtering_options, variation
    )
    stimulus_sip_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, SIPMethodEnum.MESSAGE],
        ),
    )
    bcf_output_sip_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_src_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, SIPMethodEnum.MESSAGE],
        ),
    )
    log_src_ip = None
    log_dst_ip = None
    # Find the HTTP POST interfaces from filtering options (message_type="other")
    for message in filtering_options or []:
        if message.message_type == FilterMessageType.OTHER:
            for entity in lab_config.entities:
                for interface in entity.interfaces:
                    if interface.name == message.src_interface:
                        log_src_ip = interface.ip
                    elif interface.name == message.dst_interface:
                        log_dst_ip = interface.ip
            break

    http_post_requests = list(
        pcap_service.get_messages_by_config(
            FilterConfig(
                src_ip=log_src_ip,
                dst_ip=log_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.POST],
                header_part=LOG_EVENTS_URI,
            )
        )
    )
    return stimulus_sip_messages, bcf_output_sip_messages, http_post_requests


def get_test_names() -> list:
    return TEST_NAMES


def _determine_sip_method(
    variation: RunVariation,
    bcf_output_sip_messages=None,
    stimulus_sip_messages=None,
):
    """
    Determine the SIP method for a test variation.

    Args:
        variation: RunVariation instance containing test variation data
        bcf_output_sip_messages: List of SIP messages from BCF output (optional)
        stimulus_sip_messages: List of SIP messages from stimulus (optional)

    Returns:
        str: Determined SIP method (e.g., 'MESSAGE', 'INVITE') or None if cannot be determined
    """
    # First, check actual SIP messages in pcap (both stimulus and output)
    all_sip_messages = []
    if stimulus_sip_messages:
        all_sip_messages.extend(stimulus_sip_messages)
    if bcf_output_sip_messages:
        all_sip_messages.extend(bcf_output_sip_messages)

    if all_sip_messages:
        methods = [
            str(msg.sip.method).upper()
            for msg in all_sip_messages
            if hasattr(msg, "sip")
            and hasattr(msg.sip, "method")
            and msg.sip.method is not None
        ]
        if methods:
            # Return the most common method found in actual SIP messages
            from collections import Counter

            method_counts = Counter(methods)
            most_common_method = method_counts.most_common(1)[0][0]
            # Special handling: prioritize INVITE over OPTIONS if both present
            if "INVITE" in methods and "OPTIONS" in methods:
                invite_count = method_counts["INVITE"]
                options_count = method_counts["OPTIONS"]
                if invite_count >= options_count:
                    most_common_method = "INVITE"
                elif options_count > invite_count:
                    most_common_method = "OPTIONS"
            return most_common_method

    var_name = getattr(variation, "name", None) or getattr(variation, "id", None)
    if var_name:
        upper_name = str(var_name).upper()
        if "MESSAGE" in upper_name:
            return "MESSAGE"
        elif "INVITE" in upper_name:
            return "INVITE"

    return None


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_sip_messages,
        bcf_output_sip_messages,
        http_post_requests,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    checks = [
        TestCheck(
            test_name=TEST_NAMES[0],
            test_method=validate_log_post_presence,
            test_params={"http_post_requests": http_post_requests},
        ),
        TestCheck(
            test_name=TEST_NAMES[1],
            test_method=validate_iut_sip_forwarding,
            test_params={"iut_output_messages": bcf_output_sip_messages},
        ),
        TestCheck(
            test_name=TEST_NAMES[4],
            test_method=validate_direction,
            test_params={"http_post_requests": http_post_requests},
        ),
    ]
    # TODO CHECK
    # sip_method = _determine_sip_method(variation, bcf_output_sip_messages, stimulus_sip_messages)

    # Analyze SIP methods present in pcap
    sip_analysis = analyze_sip_methods(stimulus_sip_messages, bcf_output_sip_messages)

    # Add tests based on what SIP methods are actually present in pcap
    if sip_analysis["has_message"] and not sip_analysis["has_other"]:
        # Only MESSAGE messages present - only run MESSAGE test
        checks.append(
            TestCheck(
                test_name=TEST_NAMES[2],  # "Validate Log Event depends on SIP MESSAGE"
                test_method=validate_log_event_by_sip_type,
                test_params={
                    "http_post_requests": http_post_requests,
                    "sip_message_type": "MESSAGE",
                    "force_pass": False,
                    "test_name": TEST_NAMES[2],
                },
            )
        )
    elif sip_analysis["has_other"] and not sip_analysis["has_message"]:
        # Only non-MESSAGE messages present - only run Other test
        checks.append(
            TestCheck(
                test_name=TEST_NAMES[
                    3
                ],  # "Validate Log Event depends on SIP Other message type"
                test_method=validate_log_event_by_sip_type,
                test_params={
                    "http_post_requests": http_post_requests,
                    "sip_message_type": sip_analysis["other_method"],
                    "force_pass": False,
                    "test_name": TEST_NAMES[3],
                },
            )
        )
    elif sip_analysis["has_message"] and sip_analysis["has_other"]:
        # Both MESSAGE and non-MESSAGE messages present - run both tests
        checks.append(
            TestCheck(
                test_name=TEST_NAMES[2],  # "Validate Log Event depends on SIP MESSAGE"
                test_method=validate_log_event_by_sip_type,
                test_params={
                    "http_post_requests": http_post_requests,
                    "sip_message_type": "MESSAGE",
                    "force_pass": False,
                    "test_name": TEST_NAMES[2],
                },
            )
        )
        checks.append(
            TestCheck(
                test_name=TEST_NAMES[
                    3
                ],  # "Validate Log Event depends on SIP Other message type"
                test_method=validate_log_event_by_sip_type,
                test_params={
                    "http_post_requests": http_post_requests,
                    "sip_message_type": sip_analysis["other_method"],
                    "force_pass": False,
                    "test_name": TEST_NAMES[3],
                },
            )
        )

    return checks
