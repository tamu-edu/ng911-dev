from checks.http.held_checks.checks import test_if_location_response_contains_correct_location_uri, \
    test_location_response_expiration_time
from services.aux.message_services import extract_all_contents_from_message_body
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.aux_services import get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_conduction_service import TestCheck
from services.aux.xml_services import extract_xml_body_string_from_file
from .constants import (
    HTTP_HELD_LOCATION_URI_REQUEST_SCENARIO_FILE,
    LIS_IP,
    TEST_SYSTEM_IP,
    LOCATION_REQUEST_DEVICE_URI
)


def get_test_parameters(pcap_service: PcapCaptureService) -> list:
    http_xml_request = extract_xml_body_string_from_file(HTTP_HELD_LOCATION_URI_REQUEST_SCENARIO_FILE)
    http_xml_request = http_xml_request.replace("DEVICE_URI",LOCATION_REQUEST_DEVICE_URI)
    http_output_message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=TEST_SYSTEM_IP,
                dst_ip=LIS_IP,
                packet_type=PacketTypeEnum.HTTP
            ),
            http_xml_request
    )
    response_bodies = extract_all_contents_from_message_body(http_output_message)
    http_xml_response = ""
    for body in response_bodies:
        if 'xml' in body['Content-Type']:
            http_xml_response = body['body']
            break
    http_held_message_timestamp = float(http_output_message.sniff_timestamp)
    return [http_xml_response, http_held_message_timestamp]


def get_test_list(pcap_service: PcapCaptureService) -> list:
    (
        http_xml_response,
        http_held_message_timestamp
    ) = get_test_parameters(pcap_service)
    return [
        TestCheck(
            test_name="locationResponse contains correct locationURI URL",
            test_method=test_if_location_response_contains_correct_location_uri,
            test_params={
                "output_xml": http_xml_response
            }
        ),
        TestCheck(
            test_name="locationResponse expiration time is between 30min and 24h",
            test_method=test_location_response_expiration_time,
            test_params={
                "output_xml": http_xml_response,
                "output_message_timestamp": http_held_message_timestamp
            }
        )
    ]
