from services.pcap_service import PcapCaptureService
from services.test_services.test_assessment_service import TestAssessmentService
from .test_services import get_test_list


def run(pcap_service: PcapCaptureService):
    test_scenario = TestAssessmentService(
        name="LIS_002",
        tests_list=get_test_list(pcap_service)
    )
    test_scenario.prepare_intermediate_verdicts().calculate_general_verdict().print_general_verdict()
