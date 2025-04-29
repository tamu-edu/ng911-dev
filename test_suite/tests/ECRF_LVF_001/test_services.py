from checks.http.lost_checks.checks import test_http_lost_list_services_response
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.aux_services import get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_conduction_service import TestCheck
from services.aux.xml_services import extract_xml_body_string_from_file, extract_all_xml_bodies_from_message
from .constants import (
    ESRP_IP,
    ECRF_LVF_IP,
    ListServicesScenarioFiles,
    ListServicesByLocationScenarioFiles
)


def get_test_parameters(pcap_service: PcapCaptureService) -> list:
    scenario_files = [
        ListServicesScenarioFiles.urn_service_sos,
        ListServicesScenarioFiles.urn_emergency_service_sos,
        ListServicesByLocationScenarioFiles.urn_service_sos,
        ListServicesByLocationScenarioFiles.urn_emergency_service_sos
    ]
    replacements = {
        "POINT_LAT": "1",
        "POINT_LON": "2"
    }
    xml_requests = {}
    for scenario in scenario_files:
        xml_requests[scenario] = extract_xml_body_string_from_file(scenario)
        for name, value in replacements.items():
            xml_requests[scenario] = xml_requests[scenario].replace(name, value)
    xml_responses = {}
    for scenario in scenario_files:
        message = get_http_response_containing_string_in_xml_body_for_message_matching_filter(
            pcap_service,
            FilterConfig(
                src_ip=ESRP_IP,
                dst_ip=ECRF_LVF_IP,
                packet_type=PacketTypeEnum.HTTP
            ),
            xml_requests[scenario]
        )
        try:
            xml_responses[scenario] = extract_all_xml_bodies_from_message(message)[0]
        except IndexError:
            xml_responses[scenario] = ""

    return [xml_requests, xml_responses]


def get_test_list(pcap_service: PcapCaptureService) -> list:
    (
        xml_requests,
        xml_responses
    ) = get_test_parameters(pcap_service)
    return [
        TestCheck(
            test_name="Response for listServices urn:service:sos",
            test_method=test_http_lost_list_services_response,
            test_params={
                "stimulus_xml": xml_requests[ListServicesScenarioFiles.urn_service_sos],
                "output_xml": xml_responses[ListServicesScenarioFiles.urn_service_sos],
                "service_urn": "urn:service:sos",
                "by_location": False
            }
        ),
        TestCheck(
            test_name="Response for listServices urn:emergency:service:sos",
            test_method=test_http_lost_list_services_response,
            test_params={
                "stimulus_xml": xml_requests[ListServicesScenarioFiles.urn_emergency_service_sos],
                "output_xml": xml_responses[ListServicesScenarioFiles.urn_emergency_service_sos],
                "service_urn": "urn:emergency:service:sos",
                "by_location": False
            }
        ),
        TestCheck(
            test_name="Response for listServicesByLocation urn:service:sos",
            test_method=test_http_lost_list_services_response,
            test_params={
                "stimulus_xml": xml_requests[ListServicesByLocationScenarioFiles.urn_service_sos],
                "output_xml": xml_responses[ListServicesByLocationScenarioFiles.urn_service_sos],
                "service_urn": "urn:service:sos"
            }
        ),
        TestCheck(
            test_name="Response for listServicesByLocation urn:emergency:service:sos",
            test_method=test_http_lost_list_services_response,
            test_params={
                "stimulus_xml": xml_requests[ListServicesByLocationScenarioFiles.urn_emergency_service_sos],
                "output_xml": xml_responses[ListServicesByLocationScenarioFiles.urn_emergency_service_sos],
                "service_urn": "urn:emergency:service:sos"
            }
        )
    ]
