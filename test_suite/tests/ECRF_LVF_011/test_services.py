from dataclasses import dataclass

from checks.http.checks import validate_response_code_class
from services.aux_services.json_services import get_json
from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
    get_messages,
    extract_json_data_from_http,
)
from services.aux_services.xml_services import extract_all_xml_bodies_from_message
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.aux_services.aux_services import (
    get_first_message_matching_filter,
)
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.ECRF_LVF_011.checks import (
    validate_jws_algorithm_type,
    validate_jws_protection_and_format,
)
from tests.ECRF_LVF_011.variations.param_filter_var_one import (
    get_filter_parameters_var_one,
)
from tests.ECRF_LVF_011.variations.param_filter_var_other import (
    get_filter_parameters_var_other,
)


@dataclass
class TestData:
    stimulus_message = None
    post_to_logger_message = None
    json_dict_body_from_message: dict = None
    content_body: str = None
    key_filepath: str = None
    cert_filepath: str = None
    ecrf_response_code: str = ""
    ecrf_response_code_after_block: str = ""


def get_test_parameters_var_one(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
):
    test_data = TestData()

    post_to_logger_messages = None
    post_to_logger_message = None
    json_dict_body_from_message = None
    content_body = None

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_scr_ip,
        out_dst_ip,
        key_filepath,
        cert_filepath,
    ) = filtering_data

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
        ),
    )

    stimulus_timestamp = getattr(stimulus_message, "sniff_timestamp", 0)

    if stimulus_message and stimulus_timestamp:
        post_to_logger_messages = get_messages(
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

    if post_to_logger_messages:
        for message in post_to_logger_messages:
            if hasattr(message, "http") and hasattr(message.http, "file_data"):
                message_content = extract_all_contents_from_message_body(
                    message, ignore_content_type=True
                )
                if message_content:
                    content_body = message_content[0].get("body", "")
                    if content_body and get_json(content_body):
                        post_to_logger_message = message
                        json_dict_body_from_message = extract_json_data_from_http(
                            message
                        )
                        break

    test_data.stimulus_message = stimulus_message
    test_data.post_to_logger_message = post_to_logger_message
    test_data.json_dict_body_from_message = json_dict_body_from_message
    test_data.content_body = content_body
    test_data.key_filepath = key_filepath
    test_data.cert_filepath = cert_filepath

    return test_data


def get_ecrf_to_esrp_response(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
    ) = filtering_data

    ecrf_to_esrp_response_message = None
    stimulus_timestamp = 0

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
        ),
    )

    if stimulus_message:
        stimulus_timestamp = getattr(stimulus_message, "sniff_timestamp", 0)

    if stimulus_message and stimulus_timestamp:
        ecrf_to_esrp_response_message = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_dst_ip,
                dst_ip=stimulus_src_ip,
                packet_type=PacketTypeEnum.HTTP,
                after_timestamp=stimulus_timestamp,
            ),
        )

    return ecrf_to_esrp_response_message


def get_test_parameters_var_two(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
):
    test_data = TestData()

    ecrf_to_esrp_response_message = get_ecrf_to_esrp_response(
        pcap_service, filtering_data
    )

    if ecrf_to_esrp_response_message:
        test_data.ecrf_response_code = (
            ecrf_to_esrp_response_message.http.response_code
            if hasattr(ecrf_to_esrp_response_message, "http")
            else ""
        )

    return test_data


def get_test_parameters_var_three(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
):
    test_data = TestData()
    ecrf_to_esrp_response_timestamp = 0
    esrp_to_ecrf_request_after_block = None
    esrp_to_ecrf_request_after_block_timestamp = 0
    ecrf_to_esrp_response_message_after_block = None

    (
        stimulus_src_ip,
        stimulus_dst_ip,
    ) = filtering_data

    ecrf_to_esrp_response_message = get_ecrf_to_esrp_response(
        pcap_service, filtering_data
    )

    if ecrf_to_esrp_response_message:
        ecrf_to_esrp_response_timestamp = getattr(
            ecrf_to_esrp_response_message, "sniff_timestamp", 0
        )

    if ecrf_to_esrp_response_message:
        test_data.ecrf_response_code = (
            ecrf_to_esrp_response_message.http.response_code
            if hasattr(ecrf_to_esrp_response_message, "http")
            else ""
        )

    if ecrf_to_esrp_response_timestamp:
        esrp_to_ecrf_request_after_block = get_first_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                after_timestamp=ecrf_to_esrp_response_timestamp,
                message_method=[
                    HTTPMethodEnum.POST,
                ],
            ),
        )

    if esrp_to_ecrf_request_after_block:
        esrp_to_ecrf_request_after_block_timestamp = getattr(
            esrp_to_ecrf_request_after_block, "sniff_timestamp", 0
        )

    ecrf_to_esrp_response_messages_after_block = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.HTTP,
            after_timestamp=esrp_to_ecrf_request_after_block_timestamp,
        ),
    )

    if ecrf_to_esrp_response_messages_after_block:
        for message in ecrf_to_esrp_response_messages_after_block:
            if not hasattr(message, "http"):
                continue

            http_xml_request = extract_all_xml_bodies_from_message(message)
            if http_xml_request and any(
                "listServicesResponse" in item for item in http_xml_request
            ):
                ecrf_to_esrp_response_message_after_block = message
                break

    if ecrf_to_esrp_response_message_after_block:
        test_data.ecrf_response_code_after_block = (
            ecrf_to_esrp_response_message_after_block.http.response_code
            if hasattr(ecrf_to_esrp_response_message, "http")
            else ""
        )

    return test_data


def get_test_names() -> list:
    return [
        "Validation that the JWS uses 'EdDSA' algorithm when Signed and 'none' when Unsigned.",
        "Validate Signed and Unsigned JWS, Including Payload, Algorithm, and Certificates.",
        "Validate if ECRF does not apply policies provided in incorrect JWS (signed with RSA certificate).",
        "Validate if ECRF applies policies provided in correct JWS (signed with EdDSA certificate) - block services for 15sec.",
        "Validate if ECRF received 2xx response after blocked services for 15sec.",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:

    variations = {
        "LogEvents_JWS_format": 1,
        "Incorrect_XACML_policy_JWS": 2,
        "Correct_XACML_policy_JWS": 3,
    }

    if run_variation.name in variations:
        variation_number = variations.get(run_variation.name)
    else:
        raise VariationNotFoundError(
            f"Unknown variation name: '{run_variation.name}'\n"
            f"Expected variation names by Test Case: '{variations}'"
        )

    if variation_number == 1:

        filtering_data = get_filter_parameters_var_one(lab_config, filtering_options)

        test_data = get_test_parameters_var_one(pcap_service, filtering_data)

        return [
            TestCheck(
                test_name="Validation that the JWS uses 'EdDSA' algorithm when Signed and 'none' when Unsigned.",
                test_method=validate_jws_algorithm_type,
                test_params={
                    "test_data": test_data,
                },
            ),
            TestCheck(
                test_name="Validate Signed and Unsigned JWS, Including Payload, Algorithm, and Certificates.",
                test_method=validate_jws_protection_and_format,
                test_params={
                    "test_data": test_data,
                },
            ),
        ]
    elif variation_number == 2:

        filtering_data = get_filter_parameters_var_other(lab_config, filtering_options)

        test_data = get_test_parameters_var_two(pcap_service, filtering_data)

        return [
            TestCheck(
                test_name="Validate if ECRF does not apply policies provided in incorrect JWS (signed with RSA certificate).",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": "2xx",
                    "response_code": test_data.ecrf_response_code,
                },
            ),
        ]

    else:

        filtering_data = get_filter_parameters_var_other(lab_config, filtering_options)

        test_data = get_test_parameters_var_three(pcap_service, filtering_data)

        return [
            TestCheck(
                test_name="Validate if ECRF applies policies provided in correct JWS (signed with EdDSA certificate) - block services for 15sec.",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": "4xx",
                    "response_code": test_data.ecrf_response_code,
                },
            ),
            TestCheck(
                test_name="Validate if ECRF received 2xx response after blocked services for 15sec.",
                test_method=validate_response_code_class,
                test_params={
                    "expected_response_code_class": "2xx",
                    "response_code": test_data.ecrf_response_code_after_block,
                },
            ),
        ]
