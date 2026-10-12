from typing import Any
from checks.general.checks import (
    is_data_present,
    test_if_parameter_has_one_of_expected_values,
    is_parameter_not_equal_to_expected_value,
)
from checks.http.checks import validate_response_code, is_type
from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.json_services import get_json
from services.aux_services.message_services import get_messages
from services.aux_services.sip_msg_body_services import (
    extract_all_contents_from_message_body,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter]
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    expected_resp_code = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
            expected_resp_code = message.response_status_code
    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or expected_resp_code is None
        ):
            raise WrongConfigurationError(
                "Lab Config file error - src and dst ip addresses not found"
            )
        else:
            return stimulus_src_ip, stimulus_dst_ip, expected_resp_code
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
) -> (
    tuple[str, Any | None, bool, Any | None, Any | None, Any | None, Any | None]
    | tuple[str, None, bool, None, None, None, None]
    | tuple[str, Any | None, bool, None, None, None, None]
):

    subscribe_seq_num = None
    subscribe_response_code = None
    queue_uri = None
    queue_length = None
    queue_max_length = None
    state = None
    is_emergency_state_found_in_notify = False

    stimulus_src_ip, stimulus_dst_ip, expected_response_code = get_filter_parameters(
        lab_config, filtering_options
    )
    sip_subscribe_message = get_first_message_matching_filter(
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
    if sip_subscribe_message:
        if hasattr(sip_subscribe_message.sip, "CSeq"):
            cseq_full = sip_subscribe_message.sip.get_field("CSeq")

            if cseq_full:
                subscribe_seq_num, _ = cseq_full.strip().split(maxsplit=1)

        out_timestamp = float(sip_subscribe_message.sniff_timestamp)

        messages_after_timestamp = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.SIP,
                after_timestamp=out_timestamp,
            ),
        )

        for message in messages_after_timestamp or []:
            if not hasattr(message, "sip") or not hasattr(message.sip, "cseq"):
                continue

            if (
                subscribe_seq_num
                and subscribe_seq_num in message.sip.cseq
                and hasattr(message.sip, "status_code")
            ):
                subscribe_response_code = message.sip.status_code

            if (
                subscribe_seq_num
                and "NOTIFY" in message.sip.cseq
                and subscribe_seq_num in message.sip.cseq
            ):
                if hasattr(message.sip, "event"):
                    is_emergency_state_found_in_notify = (
                        message.sip.event.lower() == "emergency-QueueState".lower()
                    )
                try:
                    json_object = getattr(message, "json", None)
                    if json_object is None:
                        all_body_content = extract_all_contents_from_message_body(
                            message
                        )
                        if isinstance(all_body_content, list) and all_body_content:
                            body = all_body_content[0].get("body")
                            json_object = get_json(body)
                            queue_uri = json_object.get("queueUri")
                            queue_length = json_object.get("queueLength")
                            queue_max_length = json_object.get("queueMaxLength")
                            state = json_object.get("state")
                            return (
                                expected_response_code,
                                subscribe_response_code,
                                is_emergency_state_found_in_notify,
                                queue_uri,
                                queue_length,
                                queue_max_length,
                                state,
                            )
                except AttributeError:
                    continue

    return (
        expected_response_code,
        subscribe_response_code,
        is_emergency_state_found_in_notify,
        queue_uri,
        queue_length,
        queue_max_length,
        state,
    )


def get_test_names() -> list:
    return [
        "Validate CHFE responds with 200 OK for SIP SUBSCRIBE",
        "Validate CHFE sends SIP NOTIFY with the same event as requested in SIP SUBSCRIBE",
        "Validate 'queueUri' parameter in CHFE SIP NOTIFY message",
        "Validate 'queueLength' parameter in CHFE SIP NOTIFY message",
        "Validate 'queueMaxLength' parameter in CHFE SIP NOTIFY message",
        "Validate 'state' parameter value in CHFE SIP NOTIFY message",
        "Validate 'state' parameter value is not 'unreachable'",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        expected_response_code,
        subscribe_response_code,
        is_emergency_state_found_in_notify,
        queue_uri,
        queue_length,
        queue_max_length,
        state,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)
    return [
        TestCheck(
            test_name="Validate CHFE responds with 200 OK for SIP SUBSCRIBE",
            test_method=validate_response_code,
            test_params={
                "expected_response_code": expected_response_code,
                "response_code": subscribe_response_code,
            },
        ),
        TestCheck(
            test_name="Validate CHFE sends SIP NOTIFY with the same event as requested in SIP SUBSCRIBE",
            test_method=is_data_present,
            test_params={
                "test_data": is_emergency_state_found_in_notify,
                "error": "FAILED -> No SIP NOTIFY with event type 'emergency-QueueState' from CHFE found",
            },
        ),
        TestCheck(
            test_name="Validate 'queueUri' parameter in CHFE SIP NOTIFY message",
            test_method=is_type,
            test_params={
                "param": queue_uri,
                "param_name": "'queueUri'",
                "expected_type": str,
            },
        ),
        TestCheck(
            test_name="Validate 'queueLength' parameter in CHFE SIP NOTIFY message",
            test_method=is_type,
            test_params={
                "param": queue_length,
                "param_name": "'queueLength'",
                "expected_type": int,
            },
        ),
        TestCheck(
            test_name="Validate 'queueMaxLength' parameter in CHFE SIP NOTIFY message",
            test_method=is_type,
            test_params={
                "param": queue_max_length,
                "param_name": "'queueMaxLength'",
                "expected_type": int,
            },
        ),
        TestCheck(
            test_name="Validate 'state' parameter value in CHFE SIP NOTIFY message",
            test_method=test_if_parameter_has_one_of_expected_values,
            test_params={
                "parameter_name": "'state' parameter from CHFE SIP NOTIFY message",
                "parameter_value": state,
                "expected_values": ["Active", "Inactive", "Disabled"],
            },
        ),
        TestCheck(
            test_name="Validate 'state' parameter value is not 'unreachable'",
            test_method=is_parameter_not_equal_to_expected_value,
            test_params={
                "parameter_name": "'state' parameter from CHFE SIP NOTIFY message",
                "parameter_value": state,
                "unexpected_value": "Unreachable",
            },
        ),
    ]
