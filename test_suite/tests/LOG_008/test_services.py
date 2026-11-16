import json
import os.path

from services.aux_services.aux_services import get_first_message_matching_filter
from services.aux_services.json_services import decode_jws
from services.aux_services.message_services import (
    get_http_response_containing_string_in_http_body_for_message_matching_filter,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.LOG_008.checks import verify_logger_response_code_extended


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip,
                                            expected_response_code, variation_file_path, key_filepath), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    out_dst_fqdn = None
    expected_response_code = None
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

    # TODO CHECK
    # for param in variation.params:
    #     if param == 'messages':
    #         for message in variation.params['messages']:
    #             variation_url = message.get('http_url', None)

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
            expected_response_code = (
                message.response_status_code
                if hasattr(message, "response_status_code")
                else expected_response_code
            )
        elif message.message_type == FilterMessageType.OTHER:
            output = message

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                    key_filepath = entity.certificate_key
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                if output:
                    if interface.name == output.src_interface:
                        out_scr_ip = interface.ip
                    elif interface.name == output.dst_interface:
                        out_dst_ip = interface.ip
                        out_dst_fqdn = interface.fqdn
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or variation_file_path is None
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
                out_dst_fqdn,
                expected_response_code,
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
        out_dst_fqdn,
        expected_response_code,
        variation_file_path,
        key_filepath,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    response_code = None
    x5u_from_response = None

    try:
        payload_header, payload_data = decode_jws(variation_file_path, key_filepath)
    except ValueError:
        payload_header = None

    if os.path.exists(variation_file_path):
        with open(variation_file_path) as var_json:
            data_in_request = json.load(var_json)
    else:
        data_in_request = ""

    logger_out_message = (
        get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[
                    HTTPMethodEnum.POST,
                ],
            ),
            str(data_in_request).replace("'", '"'),
        )
    )
    if logger_out_message:
        response_code = (
            logger_out_message.http.response_code
            if hasattr(logger_out_message.http, "response_code")
            else None
        )

    request_x5u = payload_header.get("x5u", None) if payload_header else payload_header
    # Variations 2/6/7 specific - Requires additional call from Logging Service to Test System LIS
    if (
        request_x5u
        and out_dst_ip
        and ((out_dst_ip in request_x5u) or (out_dst_fqdn in request_x5u))
    ):
        logger_to_lis_request = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=out_scr_ip,
                dst_ip=out_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[
                    HTTPMethodEnum.GET,
                ],
                after_timestamp=(
                    float(logger_out_message.sniff_timestamp)
                    if logger_out_message
                    else None
                ),
            ),
        )
        if logger_to_lis_request and hasattr(
            logger_to_lis_request.http,
            "request_full_uri",
        ):
            x5u_from_response = logger_to_lis_request.http.request_full_uri

        is_x5u_the_same = (
            True
            if (request_x5u and x5u_from_response)
            and (request_x5u == x5u_from_response)
            else False
        )
        return (
            response_code,
            expected_response_code,
            request_x5u,
            logger_to_lis_request,
            is_x5u_the_same,
        )
    # Rest of variations (1/3/4/5)
    else:
        return response_code, expected_response_code, request_x5u, "", ""


def get_test_names() -> list:
    return [
        "Verify Logging Service response.",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        response_code,
        expected_response_code,
        request_x5u,
        logger_to_lis_request,
        is_x5u_the_same,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Verify Logging Service response.",
            test_method=verify_logger_response_code_extended,
            test_params={
                "response_code": response_code,
                "expected_response_code": expected_response_code,
                "request_x5u": request_x5u,
                "logger_to_lis_request": logger_to_lis_request,
                "is_x5u_the_same": is_x5u_the_same,
            },
        )
    ]
