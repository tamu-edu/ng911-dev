from services.config.types.lab_config import LabConfig
from services.config.types.test_config import Test
from services.pcap_service import PcapCaptureService
from services.test_services.test_conduction_service import TestConductionService
from tests.CHE_002 import get_test_list


def run(pcap_service: PcapCaptureService, test_config: Test, lab_config: LabConfig):
    test_scenario = TestConductionService(
        name="BRIDGE_001",
        tests_list=get_test_list(pcap_service, test_config, lab_config)
    )
    test_scenario.prepare_intermediate_verdicts().calculate_general_verdict().print_general_verdict()
