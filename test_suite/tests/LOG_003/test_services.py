from enum import Enum

from checks.http.checks import validate_response_code_class
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.test_config import Test as TestConfig
from services.aux.json_services import get_payload_data_from_file
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.message_services import \
    get_http_response_containing_string_in_http_body_for_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_conduction_service import TestCheck
from tests.LOG_003.checks import validate_logger_response_data


class RequestVariations(Enum):
    # TODO read data from config
    REQUEST_WITH_INCORRECT_CLIENTASSIGNED_IDENTIFIER_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_1_JWS_payload'
    REQUEST_WITH_INCORRECT_LOG_EVENT_TYPE_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_2_JWS_payload'
    REQUEST_WITHOUT_LOG_EVENT_TYPE = 'pcaps/LOG_003/TC_LOG_003_variarion_3_JWS_payload'
    REQUEST_WITH_INCORRECT_TIMESTAMP_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_4_JWS_payload'
    REQUEST_WITHOUT_TIMESTAMP = 'pcaps/LOG_003/TC_LOG_003_variarion_5_JWS_payload'
    REQUEST_WITH_INCORRECT_ELEMENTID_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_6_JWS_payload'
    REQUEST_WITHOUT_ELEMENTID = 'pcaps/LOG_003/TC_LOG_003_variarion_7_JWS_payload'
    REQUEST_WITH_INCORRECT_AGENCYID_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_8_JWS_payload'
    REQUEST_WITHOUT_AGENCYID = 'pcaps/LOG_003/TC_LOG_003_variarion_9_JWS_payload'
    REQUEST_WITH_INCORRECT_AGENCYAGENTID_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_10_JWS_payload'
    REQUEST_WITHOUT_AGENCYAGENTID_FOR_JWS_SIGNED_BY_AGENT = 'pcaps/LOG_003/TC_LOG_003_variarion_11_JWS_payload'
    REQUEST_WITH_INCORRECT_AGENCYPOSITIONID_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_12_JWS_payload'
    REQUEST_WITH_INCORRECT_CALLID_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_13_JWS_payload'
    REQUEST_WITHOUT_CALLID_FOR_LOG_EVENT_TYPE_CALL_STATE_CHANGE_LOG_EVENT = 'pcaps/LOG_003/TC_LOG_003_variarion_14_JWS_payload'
    REQUEST_WITH_INCORRECT_INCIDENTID_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_15_JWS_payload'
    REQUEST_WITHOUT_INCIDENTID_FOR_LOG_EVENT_TYPE_CALLSTATECHANGELOGEVENT = 'pcaps/LOG_003/TC_LOG_003_variarion_16_JWS_payload'
    REQUEST_WITH_INCORRECT_CALLIDSIP_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_17_JWS_payload'
    REQUEST_WITHOUT_CALLIDSIP_FOR_LOG_EVENT_TYPE = 'pcaps/LOG_003/TC_LOG_003_variarion_18_JWS_payload'
    REQUEST_WITH_INCORRECT_IPADDRESSPORT_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_19_JWS_payload'
    REQUEST_WITHOUT_IPADDRESSPORT_FOR_JWS_SIGNED_BY_AGENT_WITH_IP_ADDRESS_INFORMATION = 'pcaps/LOG_003/TC_LOG_003_variarion_20_JWS_payload'
    REQUEST_WITH_INCORRECT_EXTENSION_PARAMETER = 'pcaps/LOG_003/TC_LOG_003_variarion_21_JWS_payload'
    REQUEST_WITH_NO_TRACABLE_TO_PCA = 'pcaps/LOG_003/TC_LOG_003_variarion_22_JWS_payload'
    REQUEST_WITH_DIFF_THAN_AFENCY_AGENT_ID_OR_ELEMENT_ID = 'pcaps/LOG_003/TC_LOG_003_variarion_23_JWS_payload'
    REQUEST_WITH_CORRECT_JWS_LOGEVENT_OBJECT = 'pcaps/LOG_003/TC_LOG_003_variarion_24_JWS_payload'


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
        payload = get_payload_data_from_file(request.value, 'plain')
        out_message = get_http_response_containing_string_in_http_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.POST, ]
            ),
            str(payload),
        )
        if request.name == 'REQUEST_WITH_CORRECT_JWS_LOGEVENT_OBJECT':
            response_codes_or_response_data[request.name] = out_message
        else:
            response_codes_or_response_data[request.name] = out_message.http.response_code

    return response_codes_or_response_data


def get_test_list(pcap_service: PcapCaptureService, test_config: TestConfig, lab_config: LabConfig) -> list:
    (
        http_response_codes_or_response_data
    ) = get_test_parameters(pcap_service, test_config, lab_config)
    return [
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'clientAssignedIdentifier' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.REQUEST_WITH_INCORRECT_CLIENTASSIGNED_IDENTIFIER_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'logEventType' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.REQUEST_WITH_INCORRECT_LOG_EVENT_TYPE_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'logEventType'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[RequestVariations.REQUEST_WITHOUT_LOG_EVENT_TYPE.name]
            }
        ),
        TestCheck(
            test_name=(
                "Validate 4xx error response for request with incorrect 'timestamp' parameter"
            ),
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_TIMESTAMP_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'timestamp'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITHOUT_TIMESTAMP.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'elementId' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_ELEMENTID_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'elementId'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITHOUT_ELEMENTID.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'agencyId' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_AGENCYID_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'agencyId'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITHOUT_AGENCYID.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'agencyAgentId' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_AGENCYAGENTID_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'agencyAgentId'"
                      "for JWS signed by agent (f.e. CN=agency.example, "
                      "SubjectAltName email: agent@agency.example)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITHOUT_AGENCYAGENTID_FOR_JWS_SIGNED_BY_AGENT.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'agencyPositionId' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_AGENCYPOSITIONID_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'callId' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_CALLID_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'callId' "
                      "for 'logEventType': 'CallStateChangeLogEvent'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITHOUT_CALLID_FOR_LOG_EVENT_TYPE_CALL_STATE_CHANGE_LOG_EVENT.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'incidentId' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_INCIDENTID_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'incidentId'"
                      "for 'logEventType': 'CallStateChangeLogEvent'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITHOUT_INCIDENTID_FOR_LOG_EVENT_TYPE_CALLSTATECHANGELOGEVENT.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'callIdSIP' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_CALLIDSIP_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'callIdSIP'"
                      "for 'logEventType': 'CallStateChangeLogEvent'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITHOUT_CALLIDSIP_FOR_LOG_EVENT_TYPE.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'ipAddressPort' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_IPADDRESSPORT_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request without 'ipAddressPort'"
                      "for JWS signed by agent with IP address information"
                      "(f.e. CN=agency.example, SubjectAltName email=agent@agency.example, IP: 192.168.1.1:1234)",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITHOUT_IPADDRESSPORT_FOR_JWS_SIGNED_BY_AGENT_WITH_IP_ADDRESS_INFORMATION.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with incorrect 'extension' parameter",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_INCORRECT_EXTENSION_PARAMETER.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with JWS signed by credentials not traceable to PCA",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_NO_TRACABLE_TO_PCA.name]
            }
        ),
        TestCheck(
            test_name="Validate 4xx error response for request with JWS Agent signature"
                      "different than 'agencyAgentId' or 'elementId'",
            test_method=validate_response_code_class,
            test_params={
                "expected_response_code_class": 400,
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_DIFF_THAN_AFENCY_AGENT_ID_OR_ELEMENT_ID.name]
            }
        ),
        TestCheck(
            test_name="Validate JSON body from 201 Created response for request with correct JWS LogEvent object",
            test_method=validate_logger_response_data,
            test_params={
                "response": http_response_codes_or_response_data[
                    RequestVariations.REQUEST_WITH_CORRECT_JWS_LOGEVENT_OBJECT.name]
            }
        )
    ]
