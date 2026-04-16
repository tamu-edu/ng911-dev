from services.aux_services.json_services import decode_jws, iso_to_timestamp
from services.aux_services.message_services import get_messages
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.PS_010.checks import (
    validate_policy_created_successfully,
    validate_expired_policy_response,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip,
                    exp_resp_code_policy_created, exp_resp_code_expired), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    exp_resp_code_policy_created = None
    exp_resp_code_expired = None
    variation_file_path = None
    key_filepath = None

    for param in variation.params:
        if param == "messages":
            for message in variation.params[param]:
                variation_file_path = (
                    message["prep_steps"][-1]["kwargs"]["output_file"].replace(
                        "file.", ""
                    )
                    if message.get("prep_steps", None)
                    and message["prep_steps"][-1].get("kwargs", None)
                    and message["prep_steps"][-1]["kwargs"].get("output_file", None)
                    else None
                )

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
            exp_resp_code_expired = (
                message.response_status_code
                if hasattr(message, "response_status_code")
                else exp_resp_code_expired
            )
        elif message.message_type == FilterMessageType.OTHER:
            output = message
            exp_resp_code_policy_created = (
                message.response_status_code
                if hasattr(message, "response_status_code")
                else exp_resp_code_policy_created
            )

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
        if not any(
            [
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                variation_file_path,
                key_filepath,
            ]
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
                exp_resp_code_policy_created,
                exp_resp_code_expired,
                variation_file_path,
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
    variation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        exp_resp_code_policy_created,
        exp_resp_code_expired,
        variation_file_path,
        key_filepath,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    policy_created_status_code = None
    policy_expired_status_code = None
    timestamp_from_payload = 0
    is_get_request_time_correct = False

    try:
        payload_header, payload_data = decode_jws(variation_file_path, key_filepath)
    except ValueError:
        payload_data = None

    if payload_data:
        timestamp_from_payload = iso_to_timestamp(
            payload_data.get("policyExpirationTime", "")
        )

    send_policy = get_first_message_matching_filter(
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

    if send_policy:
        ps_responses = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=out_dst_ip,
                dst_ip=out_scr_ip,
                packet_type=PacketTypeEnum.HTTP,
                after_timestamp=float(send_policy.sniff_timestamp),
            ),
        )

        for message in ps_responses:
            response_code = (
                message.http.response_code
                if (hasattr(message, "http") and hasattr(message.http, "response_code"))
                else ""
            )
            if response_code == "201":
                policy_created_status_code = response_code
                break

    expired_get_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.GET,
            ],
        ),
    )

    if expired_get_request:
        expired_get_request_timestamp = float(expired_get_request.sniff_timestamp)
        ps_responses = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.HTTP,
                after_timestamp=expired_get_request_timestamp,
            ),
        )

        is_get_request_time_correct = (
            True
            if timestamp_from_payload and expired_get_request > timestamp_from_payload
            else False
        )

        for message in ps_responses:
            response_code = (
                message.http.response_code
                if (hasattr(message, "http") and hasattr(message.http, "response_code"))
                else ""
            )
            if response_code.startswith("4"):
                policy_expired_status_code = response_code
                break

    return (
        is_get_request_time_correct,
        send_policy,
        policy_created_status_code,
        exp_resp_code_policy_created,
        expired_get_request,
        policy_expired_status_code,
        exp_resp_code_expired,
    )


def get_test_names() -> list:
    return [
        "Verify policy successfully created by Policy Store",
        "Verify that Policy Store does not provide expired policies",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        is_get_request_time_correct,
        send_policy,
        policy_created_status_code,
        exp_resp_code_policy_created,
        expired_get_request,
        policy_expired_status_code,
        exp_resp_code_expired,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Verify policy successfully created by Policy Store",
            test_method=validate_policy_created_successfully,
            test_params={
                "send_policy": send_policy,
                "policy_created_status_code": policy_created_status_code,
                "exp_resp_code_policy_created": exp_resp_code_policy_created,
            },
        ),
        TestCheck(
            test_name="Verify that Policy Store does not provide expired policies",
            test_method=validate_expired_policy_response,
            test_params={
                "is_get_request_time_correct": is_get_request_time_correct,
                "expired_get_request": expired_get_request,
                "policy_expired_status_code": policy_expired_status_code,
                "exp_resp_code_expired": exp_resp_code_expired,
            },
        ),
    ]
