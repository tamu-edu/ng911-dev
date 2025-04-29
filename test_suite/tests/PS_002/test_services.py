from enum import Enum

from checks.http.checks import validate_response_code, validate_response_code_class
from enums import PacketTypeEnum
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.test_config import Test as TestConfig
from services.aux.json_services import get_payload_data_from_file
from services.aux.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from services.pcap_service import PcapCaptureService, FilterConfig
from services.test_services.test_conduction_service import TestCheck


# TODO Read this from config
CERT_PS = "pcaps/PS_002/bcf.ng911.test_PCA.crt"
KEY_PS = "pcaps/PS_002/bcf.ng911.test.key"


class JWSPayloads(str, Enum):
    # TODO read JWS files from config
    NO_POLICY_OWNER = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_1_JWS_payload"
    INCORRECT_POLICY_OWNER_SPECIAL_CHAR = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_2_JWS_payload"
    INCORRECT_POLICY_OWNER_MISSING_AT = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_3_JWS_payload"
    INCORRECT_POLICY_OWNER_DOUBLE_AT = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_4_JWS_payload"
    INCORRECT_POLICY_OWNER_LEADING_PERIOD = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_5_JWS_payload"
    INCORRECT_POLICY_OWNER_TOO_LONG = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_6_JWS_payload"
    NO_POLICY_TYPE = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_7_JWS_payload"
    INCORRECT_POLICY_TYPE_PARAM = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_8_JWS_payload"
    NO_POLICY_RULE = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_9_JWS_payload"
    NO_POLICY_ID_OTHER_ROUTE_POLICY = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_10_JWS_payload"
    INCORRECT_POLICY_ID_INTEGER = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_11_JWS_payload"
    INCORRECT_POLICY_ID_NEWLINE = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_12_JWS_payload"
    INCORRECT_POLICY_ID_SINGLE_QUOTE = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_13_JWS_payload"
    INCORRECT_POLICY_ID_PARENTHESES = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_14_JWS_payload"
    INCORRECT_POLICY_ID_ORIGINATION_ROUTE_POLICY = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_15_JWS_payload"
    NO_POLICY_QUEUE_NAME_ORIGINATION_OR_NORMAL_NEXT_HOP = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_16_JWS_payload"
    INCORRECT_POLICY_QUEUE_NAME_OTHER_ROUTE_POLICY = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_17_JWS_payload"
    INCORRECT_POLICY_EXPIRATION_YEAR = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_18_JWS_payload"
    INCORRECT_POLICY_EXPIRATION_MONTH = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_19_JWS_payload"
    INCORRECT_POLICY_EXPIRATION_DAY = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_20_JWS_payload"
    INCORRECT_POLICY_EXPIRATION_HOUR = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_21_JWS_payload"
    INCORRECT_POLICY_EXPIRATION_MINUTE = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_22_JWS_payload"
    INCORRECT_POLICY_EXPIRATION_SECOND = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_23_JWS_payload"
    INCORRECT_POLICY_EXPIRATION_OFFSET = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_24_JWS_payload"
    INCORRECT_POLICY_EXPIRATION_FEBRUARY_DAY = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_25_JWS_payload"
    POLICY_EXPIRATION_DATE_IN_PAST = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_26_JWS_payload"
    INCORRECT_DESCRIPTION_INTEGER = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_27_JWS_payload"
    INCORRECT_DESCRIPTION_NEWLINE = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_28_JWS_payload"
    INCORRECT_DESCRIPTION_SINGLE_QUOTE = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_29_JWS_payload"
    INCORRECT_DESCRIPTION_PARENTHESES = "pcaps/PS_002/TC_PS_002_JWS/TC_PS_002_variation_30_JWS_payload"


def get_filter_parameters(test_config: TestConfig, lab_config: LabConfig) -> tuple[str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param test_config: TestConfig instance
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = test_config.stimulus_message
    stimulus_src_ip = None
    stimulus_dst_ip = None
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            if interface.name == stimulus.src_interface:
                stimulus_src_ip = interface.ip
            elif interface.name == stimulus.dst_interface:
                stimulus_dst_ip = interface.ip
    if stimulus_src_ip is None or stimulus_dst_ip is None:
        raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                      "parameters for osp_ip, bcf_ip, esrp_ip addresses")
    else:
        return stimulus_src_ip, stimulus_dst_ip


def get_test_parameters(pcap_service: PcapCaptureService, test_config: TestConfig, lab_config: LabConfig) -> list:
    stimulus_src_ip, stimulus_dst_ip = get_filter_parameters(test_config, lab_config)
    requests = {}
    for scenario in JWSPayloads:
        requests[scenario.name] = get_payload_data_from_file(scenario.value, 'plain')
    responses = {}
    for scenario in JWSPayloads:
        message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP
            ),
            string_in_message=requests[scenario.name]
        )
        try:
            responses[scenario.name] = message.http.response_code
        except IndexError:
            responses[scenario] = ""

    return responses


def get_test_list(pcap_service: PcapCaptureService, test_config: TestConfig, lab_config: LabConfig) -> list:
    (
        http_response__data
    ) = get_test_parameters(pcap_service, test_config, lab_config)
    return [
        TestCheck(
            test_name="Validate 4xx error response for request without 'policyOwner' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.NO_POLICY_OWNER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'policyOwner' parameter"
                      "(special characters not allowed in FQDN): \"policyOwner\": \"tester@ng911.te$t\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_OWNER_SPECIAL_CHAR.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'policyOwner' parameter"
                      "(missing '@'): \"policyOwner\": \"testerng911.test\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_OWNER_MISSING_AT.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'policyOwner' parameter"
                      "(double '@'): \"policyOwner\": \"tester@@ng911.test\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_OWNER_DOUBLE_AT.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'policyOwner' parameter"
                      "(leading period): \"policyOwner\": \".tester@ng911.test\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_OWNER_LEADING_PERIOD.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'policyOwner' parameter"
                      "(length exceeded): \"policyOwner\": \"tester@ng911.test...\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_OWNER_TOO_LONG.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'policyType' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.NO_POLICY_TYPE.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect"
                      "'policyType' parameter: \"policyType\": \"OtherRoutePolicyy\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_TYPE_PARAM.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'policyRules' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.NO_POLICY_RULE.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with \"policyType\": \"OtherRoutePolicy\" and without 'policyId' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.NO_POLICY_ID_OTHER_ROUTE_POLICY.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with \"policyType\": \"OtherRoutePolicy\" and"
                      "with incorrect 'policyId' parameter (send integer): \"policyId\": 123",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_ID_INTEGER.name]
            }
        ),
        TestCheck(
            test_name="Validate 201 created response for request"
                      "with \"policyType\": \"OtherRoutePolicy\" and with incorrect 'policyId'"
                      "parameter: \"policyId\": \"\\n\"",
            test_method=validate_response_code,
            test_params={
                "expected_response_code": 201,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_ID_NEWLINE.name]
            }
        ),
        TestCheck(
            test_name="Validate 201 created response for request with \"policyType\": \"OtherRoutePolicy\""
                      "and with incorrect 'policyId' parameter: \"policyId\": \"'\"",
            test_method=validate_response_code,
            test_params={
                "expected_response_code": 201,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_ID_SINGLE_QUOTE.name]
            }
        ),
        TestCheck(
            test_name="Validate 201 created response for request with \"policyType\": \"OtherRoutePolicy\""
                      "and with incorrect 'policyId' parameter: \"policyId\": \"(\"",
            test_method=validate_response_code,
            test_params={
                "expected_response_code": 201,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_ID_PARENTHESES.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with \"policyType\": \"OriginationRoutePolicy\""
                      "and with \"policyId\": \"test_123\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_ID_ORIGINATION_ROUTE_POLICY.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with \"policyType\": \"OriginationRoutePolicy\" or"
                      "\"policyType\": \"NormalNextHopRoutePolicy\" and without 'policyQueueName'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.NO_POLICY_QUEUE_NAME_ORIGINATION_OR_NORMAL_NEXT_HOP.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with \"policyType\": \"OtherRoutePolicy\" and"
                      "with \"policyQueueName\": \"test\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_QUEUE_NAME_OTHER_ROUTE_POLICY.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect year)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_EXPIRATION_YEAR.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime'parameter (incorrect month)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_EXPIRATION_MONTH.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect day)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_EXPIRATION_DAY.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect hour)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_EXPIRATION_HOUR.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect minute)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_EXPIRATION_MINUTE.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect second)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_EXPIRATION_SECOND.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect time offset)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_EXPIRATION_OFFSET.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect day in February)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_POLICY_EXPIRATION_FEBRUARY_DAY.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (date in the past):"
                      "\"policyExpirationTime\": \"2015-04-30T12:58:03.01-05:00\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.POLICY_EXPIRATION_DATE_IN_PAST.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'description' parameter (send integer): \"description\": 123",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_DESCRIPTION_INTEGER.name]
            }
        ),
        TestCheck(
            test_name="Validate 201 created response for request"
                      "with incorrect 'description' parameter: \"description\": \"\n\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_DESCRIPTION_NEWLINE.name]
            }
        ),
        TestCheck(
            test_name="Validate 201 created response for request"
                      "with incorrect 'description' parameter: \"description\": \"'\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_DESCRIPTION_SINGLE_QUOTE.name]
            }
        ),
        TestCheck(
            test_name="Validate 201 created response for request"
                      "with incorrect 'description' parameter: \"description\": \"(\"",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response__data[JWSPayloads.INCORRECT_DESCRIPTION_PARENTHESES.name]
            }
        ),

    ]




