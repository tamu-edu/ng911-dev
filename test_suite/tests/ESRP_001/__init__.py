from services.pcap_service import PcapCaptureService
from services.test_services.test_conduction_service import TestConductionService
from .test_services import get_test_list


def run(pcap_service: PcapCaptureService):
    test_scenario = TestConductionService(
        name="ESRP_001",
        tests_list=get_test_list(pcap_service)
    )
    test_scenario.prepare_intermediate_verdicts().calculate_general_verdict().print_general_verdict()
