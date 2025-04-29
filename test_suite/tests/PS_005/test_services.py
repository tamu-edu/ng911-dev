from enum import Enum

from checks.http.checks import validate_response_code_class
from services.aux.json_services import get_payload_data_from_file
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.test_config import Test as TestConfig
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_conduction_service import TestCheck


class RequestVariations(Enum):
    try:
        MISSING_POLICY_TYPE = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        MISSING_POLICY_OWNER = ("/Policies?policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        MISSING_POLICY_ID_OTHER_ROUTE_POLICY = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        MISSING_POLICY_QUEUE_NAME_ORIGINATION_ROUTE_POLICY = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_OWNER_SPECIAL_CHAR = ("/Policies?policyOwner=te$t%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_OWNER_MISSING_AT = ("/Policies?policyOwner=testexample%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_OWNER_DOUBLE_AT = ("/Policies?policyOwner=test%40%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_OWNER_LEADING_PERIOD = ("/Policies?policyOwner=%2Etest%40example%2Ecom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_OWNER_TOO_LONG = ("/Policies?policyOwner=test%40example%2Ecomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcomcom&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example.com", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_TYPE = ("/Policies?policyType=OtherRoutePolicyy&policyOwner=TEST_SYSTEM_POLICY_OWNER&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        INCORRECT_POLICY_QUEUE_NAME_NO_USERNAME = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3A%40example%2Ecom%3A5060", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_QUEUE_NAME_NO_DOMAIN = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40%3A5060", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_QUEUE_NAME_INVALID_CHARACTERS = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example$%2Ecom%3A5060", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_QUEUE_NAME_INVALID_PORT = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=sip%3Atest%40example$%2Ecom%3A65536", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_QUEUE_NAME_INVALID_SCHEME = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OriginationRoutePolicy&policyQueueName=zip%3Atest%40example$%2Ecom%3A5060", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_4-9_11-15_JWS_payload.txt',
                                                                   'plain'))
        INCORRECT_POLICY_ID_STRING =( "/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        INCORRECT_POLICY_ID_EMPTY = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        INCORRECT_POLICY_ID_SPACE = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=%20", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        INCORRECT_POLICY_ID_EXCEED_64BIT_UINT = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=18446744073709551616", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        INCORRECT_POLICY_ID_NEGATIVE_EXCEED_64BIT_INT = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=-9223372036854775809", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_1-3_10_16-20_JWS_payload.txt',
                                                     'plain'))
        INCORRECT_POLICY_EXPIRATION_YEAR = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_21_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_POLICY_EXPIRATION_MONTH = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_22_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_POLICY_EXPIRATION_DAY = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_23_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_POLICY_EXPIRATION_HOUR = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_24_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_POLICY_EXPIRATION_MINUTE = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_25_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_POLICY_EXPIRATION_SECOND = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_26_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_POLICY_EXPIRATION_TIME_OFFSET = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_27_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_POLICY_EXPIRATION_FEBRUARY_DAY = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_28_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_POLICY_EXPIRATION_DATE_PAST = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_29_JWS_payload.txt',
                                                               'plain'))
        INCORRECT_SIGNATURE_TEST_PREAMBLE = ("/Policies?policyOwner=TEST_SYSTEM_POLICY_OWNER&policyType=OtherRoutePolicy&policyId=test_example_1", get_payload_data_from_file('pcaps/PS_005/TC_PS_005_JWS/TC_PS_005_variation_30_JWS_payload.txt',
    'plain'))
    except Exception:
        pass


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


def get_test_parameters(pcap_service: PcapCaptureService, test_config: TestConfig, lab_config: LabConfig) -> dict:
    response_codes_or_response_data = {}
    stimulus_src_ip, stimulus_dst_ip = get_filter_parameters(test_config, lab_config)
    for request in RequestVariations:
        uri, payload = request.value
        out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.PUT, ]
            ),
            payload,
            uri
        )
        response_codes_or_response_data[request.name] = out_message.http.response_code

    return response_codes_or_response_data


def get_test_list(pcap_service: PcapCaptureService, test_config: TestConfig, lab_config: LabConfig) -> list:
    (
        http_response_codes_or_response_data
    ) = get_test_parameters(pcap_service, test_config, lab_config)
    return [
        TestCheck(
            test_name="Validate 4xx error response for request without 'policyOwner'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.MISSING_POLICY_OWNER.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request without 'policyType'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.MISSING_POLICY_TYPE.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with 'policyType': 'OtherRoutePolicy' and without 'policyId'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.MISSING_POLICY_ID_OTHER_ROUTE_POLICY.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with 'policyType': 'OriginationRoutePolicy' and without 'policyQueueName'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.MISSING_POLICY_QUEUE_NAME_ORIGINATION_ROUTE_POLICY.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyOwner' parameter (special characters not allowed in FQDN):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_OWNER_SPECIAL_CHAR.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyOwner' parameter (missing '@'):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_OWNER_MISSING_AT.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyOwner' parameter (double '@'):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_OWNER_DOUBLE_AT.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyOwner' parameter (leading period):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_OWNER_LEADING_PERIOD.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyOwner' parameter (length exceeded):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.INCORRECT_POLICY_OWNER_TOO_LONG.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyType' parameter:",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.INCORRECT_POLICY_TYPE.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyQueueName' (send without username), URL:",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_QUEUE_NAME_NO_USERNAME.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyQueueName' (send without domain), URL:",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_QUEUE_NAME_NO_DOMAIN.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyQueueName' (send with not allowed characters), URL:",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_QUEUE_NAME_INVALID_CHARACTERS.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyQueueName' (send invalid port), URL:",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_QUEUE_NAME_INVALID_PORT.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyQueueName' (send invalid scheme), URL:",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_QUEUE_NAME_INVALID_SCHEME.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyId' parameter (send string):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.INCORRECT_POLICY_ID_STRING.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyId' parameter (send empty):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.INCORRECT_POLICY_ID_EMPTY.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyId' parameter (send space):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.INCORRECT_POLICY_ID_SPACE.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyId' parameter (send value exceeding 64bit unsigned int):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_ID_EXCEED_64BIT_UINT.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyId' parameter (send negative value exceeding 64bit int):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_ID_NEGATIVE_EXCEED_64BIT_INT.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect year):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_EXPIRATION_YEAR.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect month):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_EXPIRATION_MONTH.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect day):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.INCORRECT_POLICY_EXPIRATION_DAY.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect hour):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_EXPIRATION_HOUR.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect minute):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_EXPIRATION_MINUTE.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect second):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_EXPIRATION_SECOND.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect time offset):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_EXPIRATION_TIME_OFFSET.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (incorrect day in February):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_EXPIRATION_FEBRUARY_DAY.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request"
                      "with incorrect 'policyExpirationTime' parameter (date in the past):",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_POLICY_EXPIRATION_DATE_PAST.name]
            }
        ),

        TestCheck(
            test_name="Validate 4xx error response for request with incorrect signature (check Test Preamble)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.INCORRECT_SIGNATURE_TEST_PREAMBLE.name]
            }
        )
    ]
