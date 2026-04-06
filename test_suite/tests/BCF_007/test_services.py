from services.aux_services.json_services import decode_jws
from services.aux_services.message_services import extract_json_data_from_http
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
from tests.BCF_007.checks import (
    validate_logging_call_status,
    validate_logging_call_signaling_message,
)

from test_suite.services.aux_services.message_services import (
    extract_header_field_value_from_raw_string_body,
)
from test_suite.services.aux_services.sip_services import extract_raw_sip_message_string


def extract_message_info(message):
    """
    Extracts timestamp, text, and call_id from a message object.
    :praram message: PCAP message
    :return Timestamp, Text, Call_id attributes
    """
    if (
        not message
        or not hasattr(message, "sip")
        or not hasattr(message, "sniff_timestamp")
    ):
        return None, None, None

    # Timestamp extraction (always done if message exists)
    ts = float(message.sniff_timestamp)

    # Check for the attribute once and reuse the result
    has_call_id = hasattr(message.sip, "call_id")

    # Data extraction (only if has_call_id is True)
    text = extract_raw_sip_message_string(message) if has_call_id else None
    call_id = message.sip.get("call_id") if has_call_id else None

    return ts, text, call_id


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

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                    key_filepath = entity.certificate_key
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
                "It seems that the LabConfig does not contain required"
                "parameters for osp_ip, bcf_ip, esrp_ip addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                key_filepath,
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
    variation: RunVariation,
):
    call_start_request = None
    call_signalling_message_1 = None
    call_end_request = None
    call_signalling_message_2 = None

    stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, key_filepath = (
        get_filter_parameters(lab_config, filtering_options, variation)
    )

    invite_message = get_first_message_matching_filter(
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

    bye_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.BYE,
            ],
        ),
    )

    invite_message_ts, invite_message_text, invite_message_call_id = (
        extract_message_info(invite_message)
    )
    bye_message_ts, bye_message_text, bye_message_call_id = extract_message_info(
        bye_message
    )

    fe_request_messages = get_messages(
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

    if fe_request_messages:
        for message in fe_request_messages:
            if hasattr(message, "http") and hasattr(message.http, "file_data"):
                jws_data_from_message = extract_json_data_from_http(message)
                try:
                    payload_header, payload_data = decode_jws(
                        jws_data_from_message, key_filepath
                    )
                except ValueError:
                    _, payload_data = None, None
                if payload_data:
                    log_event_type = payload_data.get("logEventType", None)
                    if log_event_type == "CallStartLogEvent":
                        call_start_request = payload_data
                    elif log_event_type == "CallSignalingMessageLogEvent":

                        def get_request_line_and_call_id(raw_message_text: str):
                            request_line = (
                                next(iter(raw_message_text.splitlines()), "")
                                .strip()
                                .lower()
                                .replace(" ", "")
                                .replace("\n", "")
                                .replace("\r", "")
                            )
                            call_id = extract_header_field_value_from_raw_string_body(
                                "Call-ID", raw_message_text
                            )
                            if call_id:
                                call_id = (
                                    call_id.strip()
                                    .lower()
                                    .replace(" ", "")
                                    .replace("\n", "")
                                    .replace("\r", "")
                                )
                            return request_line, call_id

                        if call_signalling_message_1 is None:
                            if (
                                payload_data.get("direction", "").lower().strip()
                                == "incoming"
                            ):
                                payload_request_line, payload_call_id = (
                                    get_request_line_and_call_id(
                                        payload_data.get("text", "")
                                    )
                                )
                                invite_request_line, invite_call_id = (
                                    get_request_line_and_call_id(invite_message_text)
                                )
                                if (
                                    payload_request_line
                                    and payload_call_id
                                    and invite_request_line
                                    and invite_call_id
                                ):
                                    if (
                                        payload_request_line == invite_request_line
                                        and payload_call_id == invite_call_id
                                    ):
                                        call_signalling_message_1 = payload_data
                        else:
                            if call_signalling_message_2 is None:
                                if (
                                    payload_data.get("direction", "").lower().strip()
                                    == "incoming"
                                ):
                                    payload_request_line, payload_call_id = (
                                        get_request_line_and_call_id(
                                            payload_data.get("text", "")
                                        )
                                    )
                                    bye_request_line, bye_call_id = (
                                        get_request_line_and_call_id(bye_message_text)
                                    )
                                    if (
                                        payload_request_line
                                        and payload_call_id
                                        and bye_request_line
                                        and bye_call_id
                                    ):
                                        if (
                                            payload_request_line == bye_request_line
                                            and payload_call_id == bye_call_id
                                        ):
                                            call_signalling_message_2 = payload_data
                    elif log_event_type == "CallEndLogEvent":
                        call_end_request = payload_data

    return (
        call_start_request,
        call_signalling_message_1,
        call_end_request,
        call_signalling_message_2,
        invite_message_ts,
        invite_message_text,
        invite_message_call_id,
        bye_message_ts,
        bye_message_text,
        bye_message_call_id,
    )


def get_test_names() -> list:
    return [
        "Verify Logging call status for CallStartLogEvent.",
        "Verify Logging call status for SIP INVITE CallSignalingMessageLogEvent.",
        "Verify Logging call status for CallEndLogEvent.",
        "Verify Logging call status for SIP BYE CallSignalingMessageLogEvent.",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        call_start_request,
        call_signalling_message_1,
        call_end_request,
        call_signalling_message_2,
        invite_message_ts,
        invite_message_text,
        invite_message_call_id,
        bye_message_ts,
        bye_message_text,
        bye_message_call_id,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Verify Logging call status for CallStartLogEvent.",
            test_method=validate_logging_call_status,
            test_params={
                "jws_data": call_start_request,
                "init_timestamp": invite_message_ts,
                "call_id": invite_message_call_id,
            },
        ),
        TestCheck(
            test_name="Verify Logging call status for SIP INVITE CallSignalingMessageLogEvent.",
            test_method=validate_logging_call_signaling_message,
            test_params={
                "jws_data": call_signalling_message_1,
                "init_timestamp": invite_message_ts,
                "text": invite_message_text,
                "call_id": invite_message_call_id,
            },
        ),
        TestCheck(
            test_name="Verify Logging call status for CallEndLogEvent.",
            test_method=validate_logging_call_status,
            test_params={
                "jws_data": call_end_request,
                "init_timestamp": bye_message_ts,
                "call_id": bye_message_call_id,
            },
        ),
        TestCheck(
            test_name="Verify Logging call status for SIP BYE CallSignalingMessageLogEvent.",
            test_method=validate_logging_call_signaling_message,
            test_params={
                "jws_data": call_signalling_message_2,
                "init_timestamp": bye_message_ts,
                "text": bye_message_text,
                "call_id": bye_message_call_id,
            },
        ),
    ]
