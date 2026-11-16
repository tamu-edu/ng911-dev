from dataclasses import dataclass

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present, is_test_data_the_same
from checks.http.checks import validate_response_code_class
from checks.jws.checks import is_valid_algorithm
from services.aux_services.message_services import (
    extract_json_data_from_http,
    get_http_messages_by_log_event_type,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig

from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_021.constants import (
    NOT_RUN,
    EVENT_TYPE,
    SUBSCRIBE_SIP_EVENT,
    POLICY_QUERY,
    NOT_RUN_NO_PS_RESPONSE,
)
from tests.CHFE_021.checks import (
    validate_jws_protection_and_format,
)
from tests.CHFE_021.variations.param_filter_var_one import (
    get_filter_parameters_var_one,
)
from tests.CHFE_021.variations.param_filter_var_other import (
    get_filter_parameters_var_other,
)


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Packet | None = None
    is_chfe_logger_post_messages: bool = False
    is_post_message_found_by_event_type: bool = False
    chfe_logger_body: str | None = None
    chfe_logger_body_dict: dict | None = None
    key_filepath: str | None = None
    cert_filepath: str | None = None
    chfe_response_code: int | None = None
    expected_status_code: str | None = None
    is_notify_sent: bool = False
    is_chfe_ps_get_request: bool = False
    is_ps_chfe_get_response: bool = False


def _check_policy_query_request_response(
    fetcher: PacketFetcher, policy_query: str
) -> tuple[bool, bool]:
    """
    Checks whether a ServiceState policy query (HTTP GET) was sent from
    CHFE to PS, and if so, whether PS responded with HTTP 200.

    :param fetcher: PacketFetcher with "chfe_ps"/"ps_chfe" routes already added.
    :param policy_query: Substring to match in the GET request's target
        URL (e.g. POLICY_QUERY).
    :return: (is_request_found, is_response_found)
    """
    chfe_ps_get_request, chfe_ps_get_request_ts = fetcher.get_first_http_get(
        "chfe_ps", url_contains=policy_query, return_timestamp=True
    )
    if not chfe_ps_get_request:
        return False, False

    ps_chfe_response = fetcher.get_first_http_200(
        "ps_chfe", after_timestamp=chfe_ps_get_request_ts
    )
    return True, bool(ps_chfe_response)


def get_test_parameters_var_one(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
):

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        key_filepath,
        cert_filepath,
    ) = filtering_data

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("chfe_logger", out_src_ip, out_dst_ip)

    data: dict = {"key_filepath": key_filepath, "cert_filepath": cert_filepath}

    # Get ESRP to CHFE stimulus message
    stimulus_message, stimulus_ts = fetcher.get_first_sip_invite(
        "esrp_chfe", return_timestamp=True
    )

    data["stimulus_message"] = stimulus_message

    if not stimulus_message:
        return TestData(**data)

    # Get CHFE to LOGGER HTTP POST requests
    chfe_logger_http_posts = fetcher.get_http_messages(
        "chfe_logger", after_timestamp=stimulus_ts
    )

    # Get first POST in list with CallSignalingMessageLogEvent and extract body
    if chfe_logger_http_posts:
        data["is_chfe_logger_post_messages"] = True
        matched_http_messages = get_http_messages_by_log_event_type(
            chfe_logger_http_posts, EVENT_TYPE
        )

        chfe_logger_post = matched_http_messages[0] if matched_http_messages else None

        if chfe_logger_post:
            data["is_post_message_found_by_event_type"] = True
            data["chfe_logger_body"] = HttpMessage.from_packet(chfe_logger_post).body
            data["chfe_logger_body_dict"] = extract_json_data_from_http(
                chfe_logger_post
            )

    return TestData(**data)


def get_test_parameters_var_two(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        other_src_ip,
        other_dst_ip,
        response_status_code,
    ) = filtering_data

    data: dict = {"expected_status_code": response_status_code}
    subscribe_call_id = None

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("chfe_ps", other_src_ip, other_dst_ip)

    # Get ServiceState policy request\response from CHFE to PS
    data["is_chfe_ps_get_request"], data["is_ps_chfe_get_response"] = (
        _check_policy_query_request_response(fetcher, POLICY_QUERY)
    )

    # Get timestamp and Call-ID of First SUBSCRIBE from ESRP to CHFE
    subscribe_message, subscribe_ts = fetcher.get_first_sip_subscribe(
        "esrp_chfe", return_timestamp=True, event=SUBSCRIBE_SIP_EVENT
    )
    if subscribe_message:
        subscribe_call_id = SipMessage.from_packet(subscribe_message).call_id

    # Get response and response code from CHFE
    if subscribe_message and subscribe_call_id:
        chfe_response = fetcher.get_first_sip(
            "chfe_esrp", after_timestamp=subscribe_ts, call_id=subscribe_call_id
        )
        if chfe_response:
            data["chfe_response_code"] = SipMessage.from_packet(
                chfe_response
            ).status_code

    return TestData(**data)


def get_test_parameters_var_three(
    pcap_service: PcapCaptureService,
    filtering_data: tuple,
):

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        other_src_ip,
        other_dst_ip,
        response_status_code,
    ) = filtering_data

    data: dict = {"expected_status_code": response_status_code}
    subscribe_call_id = None

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_chfe", stimulus_src_ip, stimulus_dst_ip)
    fetcher.add_route("chfe_ps", other_src_ip, other_dst_ip)

    # Get ServiceState policy request\response from CHFE to PS
    data["is_chfe_ps_get_request"], data["is_ps_chfe_get_response"] = (
        _check_policy_query_request_response(fetcher, POLICY_QUERY)
    )

    # Get timestamp and Call-ID of First SUBSCRIBE from ESRP to CHFE
    subscribe_message, subscribe_ts = fetcher.get_first_sip_subscribe(
        "esrp_chfe", return_timestamp=True, event=SUBSCRIBE_SIP_EVENT
    )
    if subscribe_message:
        subscribe_call_id = SipMessage.from_packet(subscribe_message).call_id

    # Get first SIP response from CHFE after SUBSCRIBE and response code
    chfe_subscribe_response, chfe_subscribe_response_ts = fetcher.get_first_sip(
        "chfe_esrp",
        return_timestamp=True,
        after_timestamp=subscribe_ts,
        call_id=subscribe_call_id,
    )
    if chfe_subscribe_response:
        data["chfe_response_code"] = SipMessage.from_packet(
            chfe_subscribe_response
        ).status_code

    # Get CHFE to ESRP Notify message
    chfe_notify_message = fetcher.get_first_sip_notify(
        "chfe_esrp",
        after_timestamp=chfe_subscribe_response_ts,
        call_id=subscribe_call_id,
    )
    if chfe_notify_message:
        data["is_notify_sent"] = True

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Validate CHFE to LOGGER HTTP POST requests is present",
        "Validate CHFE to LOGGER HTTP POST JWS payload event data is accessible",
        "Validate that the JWS uses 'EdDSA' algorithm when Signed and 'none' when Unsigned",
        "Validate Signed or Unsigned JWS, Including Payload, Algorithm, and Certificates",
        "Validate if CHFE does not apply policies provided in incorrect JWS (signed with RSA certificate)",
        "Validate if SIP SUBSCRIBE request from ESRP is accepted by CHFE after applied policies",
        "Validate if SIP NOTIFY message sent back from CHFE to ESRP after SIP SUBSCRIBE",
        "Validate if CHFE GET ServiceState request was sent to the Policy Store",
        "Validate if Policy Store responded with 200 on CHFE GET ServiceState request",
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

    tests_list = []

    if variation_number == 1:

        filtering_data = get_filter_parameters_var_one(lab_config, filtering_options)
        test_data = get_test_parameters_var_one(pcap_service, filtering_data)

        tests_list.extend(
            [
                TestCheck(
                    test_name="Validate CHFE to LOGGER HTTP POST requests is present",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_chfe_logger_post_messages,
                        "error": "FAILED -> CHFE to LOGGER HTTP POST requests not found",
                    },
                ),
                TestCheck(
                    test_name="Validate CHFE to LOGGER HTTP POST JWS payload event data is accessible",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data.is_post_message_found_by_event_type,
                        "error": "FAILED -> Can't extract JWS payload data of event type 'CallSignalingMessageLogEvent' from CHFE to LOGGER HTTP POST",
                    },
                ),
                TestCheck(
                    test_name="Validate that the JWS uses 'EdDSA' algorithm when Signed and 'none' when Unsigned",
                    test_method=is_data_present,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": is_valid_algorithm(test_data.chfe_logger_body),
                        "error": "FAILED -> Wrong protected header algorithm for JWS.",
                    },
                ),
                TestCheck(
                    test_name="Validate Signed or Unsigned JWS, Including Payload, Algorithm, and Certificates",
                    test_method=validate_jws_protection_and_format,
                    precondition=test_data.stimulus_message,
                    precondition_error=NOT_RUN,
                    test_params={
                        "test_data": test_data,
                    },
                ),
            ]
        )
    elif variation_number == 2:

        filtering_data = get_filter_parameters_var_other(lab_config, filtering_options)
        test_data = get_test_parameters_var_two(pcap_service, filtering_data)

        tests_list.extend(
            [
                TestCheck(
                    test_name="Validate if CHFE does not apply policies provided in incorrect JWS (signed with RSA certificate)",
                    test_method=validate_response_code_class,
                    precondition=test_data.is_ps_chfe_get_response,
                    precondition_error=NOT_RUN_NO_PS_RESPONSE,
                    test_params={
                        "expected_response_code_class": test_data.expected_status_code,
                        "response_code": str(test_data.chfe_response_code),
                    },
                ),
            ]
        )

    else:

        filtering_data = get_filter_parameters_var_other(lab_config, filtering_options)
        test_data = get_test_parameters_var_three(pcap_service, filtering_data)

        tests_list.extend(
            [
                TestCheck(
                    test_name="Validate if SIP SUBSCRIBE request from ESRP is accepted by CHFE after applied policies",
                    test_method=is_test_data_the_same,
                    precondition=test_data.is_ps_chfe_get_response,
                    precondition_error=NOT_RUN_NO_PS_RESPONSE,
                    test_params={
                        "expected_data": test_data.expected_status_code,
                        "actual_data": str(test_data.chfe_response_code),
                    },
                ),
                TestCheck(
                    test_name="Validate if SIP NOTIFY message sent back from CHFE to ESRP after SIP SUBSCRIBE",
                    test_method=is_data_present,
                    precondition=test_data.is_ps_chfe_get_response,
                    precondition_error=NOT_RUN_NO_PS_RESPONSE,
                    test_params={
                        "test_data": test_data.is_notify_sent,
                        "error": "FAILED -> No SIP NOTIFY message from CHFE to ESRP after SIP SUBSCRIBE found",
                    },
                ),
            ]
        )

    if variation_number in (
        2,
        3,
    ):
        tests_list.extend(
            [
                TestCheck(
                    test_name="Validate if CHFE GET ServiceState request was sent to the Policy Store",
                    test_method=is_data_present,
                    test_params={
                        "test_data": test_data.is_chfe_ps_get_request,
                        "error": "FAILED -> GET ServiceState request from CHFE to the Policy Store not found",
                    },
                ),
                TestCheck(
                    test_name="Validate if Policy Store responded with 200 on CHFE GET ServiceState request",
                    test_method=is_data_present,
                    test_params={
                        "test_data": test_data.is_ps_chfe_get_response,
                        "error": "FAILED -> Policy Store response with 200 on CHFE GET ServiceState request not found",
                    },
                ),
            ]
        )

    return tests_list
