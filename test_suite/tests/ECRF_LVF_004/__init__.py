from services.pcap_service import PcapCaptureService
from services.test_services.test_assessment_service import TestAssessmentService
from .test_services import get_test_list, get_test_names


def run(pcap_service: PcapCaptureService):
    test_scenario = TestAssessmentService(
        name="ECRF_LVF_004",
        tests_list=get_test_list(pcap_service)
    )
    test_scenario.prepare_intermediate_verdicts().calculate_general_verdict().print_general_verdict()


def get_additional_requirements() -> dict:
    return {
        "ixit_file": True  # or False
    }
