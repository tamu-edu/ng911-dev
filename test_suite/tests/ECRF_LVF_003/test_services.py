from checks.http.lost_checks.checks import test_http_lost_find_service_response_with_sip_uri_check
from services.aux.message_services import get_header_field_value
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.aux_services import get_http_response_containing_string_in_xml_body_for_message_matching_filter
from enums import PacketTypeEnum
from services.test_services.test_conduction_service import TestCheck
from services.aux.xml_services import extract_xml_body_string_from_file, extract_all_xml_bodies_from_message
from .constants import (
    ESRP_IP,
    ECRF_LVF_IP,
    FindServiceBoundariesCoverageScenarioFiles,
    ECRF_LVF_SERVICE_BOUNDARIES,
    ECRF_LVF_2_SERVICE_BOUNDARIES
)


def get_test_parameters(pcap_service: PcapCaptureService) -> list:
    scenario_files = [scenario.value for name, scenario in FindServiceBoundariesCoverageScenarioFiles.__dict__.items()
                      if isinstance(scenario, FindServiceBoundariesCoverageScenarioFiles)]
    xml_requests = {}
    for scenario in scenario_files:
        xml_requests[scenario] = extract_xml_body_string_from_file(scenario)
    xml_responses = {}
    ecrf_redirect_location_url = ""
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
        if scenario == FindServiceBoundariesCoverageScenarioFiles.none_iterative_mode:
            ecrf_redirect_location_url = get_header_field_value(message, "Location")
        else:
            try:
                xml_responses[scenario] = extract_all_xml_bodies_from_message(message)[0]
            except IndexError:
                xml_responses[scenario] = ""
    return [xml_requests, xml_responses, ecrf_redirect_location_url]


def get_test_list(pcap_service: PcapCaptureService) -> list:
    (
        xml_requests,
        xml_responses,
        ecrf_redirect_location_url
    ) = get_test_parameters(pcap_service)
    from checks.general.checks import test_if_url_is_valid
    return [
        TestCheck(
            test_name="(request=1x fully covered service boundary + 1x partially) returning service fully covered",
            test_method=test_http_lost_find_service_response_with_sip_uri_check,
            test_params={
                "stimulus_xml": xml_requests[FindServiceBoundariesCoverageScenarioFiles.one_fully_and_one_partially],
                "output_xml": xml_responses[FindServiceBoundariesCoverageScenarioFiles.one_fully_and_one_partially],
                "expected_sip_uri_list": [ECRF_LVF_SERVICE_BOUNDARIES[0]["POLICE"]["SIP_URI"]]
            }
        ),
        TestCheck(
            test_name="(request=2x fully covered service boundaries) returning one of service boundaries",
            test_method=test_http_lost_find_service_response_with_sip_uri_check,
            test_params={
                "stimulus_xml": xml_requests[FindServiceBoundariesCoverageScenarioFiles.two_fully],
                "output_xml": xml_responses[FindServiceBoundariesCoverageScenarioFiles.two_fully],
                "expected_sip_uri_list": [
                    ECRF_LVF_SERVICE_BOUNDARIES[0]["POLICE"]["SIP_URI"],
                    ECRF_LVF_SERVICE_BOUNDARIES[1]["POLICE"]["SIP_URI"]
                ]
            }
        ),
        TestCheck(
            test_name="returning service under another ECRF jurisdiction",
            test_method=test_http_lost_find_service_response_with_sip_uri_check,
            test_params={
                "stimulus_xml": xml_requests[FindServiceBoundariesCoverageScenarioFiles.none_recursive_mode],
                "output_xml": xml_responses[FindServiceBoundariesCoverageScenarioFiles.none_recursive_mode],
                "expected_sip_uri_list": [ECRF_LVF_2_SERVICE_BOUNDARIES[0]["POLICE"]["SIP_URI"]]
            }
        ),
        TestCheck(
            test_name="returning FQDN of next ECRF server",
            test_method=test_if_url_is_valid,
            test_params={
                "parameter_name": ecrf_redirect_location_url
            }
        )
    ]
