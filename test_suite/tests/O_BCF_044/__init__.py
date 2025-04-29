from services.pcap_service import PcapCaptureService
from services.test_services.test_conduction_service import TestConductionService
from .test_services import get_test_list


def run(pcap_service: PcapCaptureService):
    """
    Run the test scenario here
    :param pcap_service: PcapCaptureService instance to work with previously recorded pcap file for this test
    :return: None
    """""

    test_scenario = TestConductionService(
        name="O_BCF_044",
        tests_list=get_test_list(pcap_service)
    )
    test_scenario.prepare_intermediate_verdicts().calculate_general_verdict().print_general_verdict()

