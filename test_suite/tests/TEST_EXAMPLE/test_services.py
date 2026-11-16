from checks.general.checks import is_data_present
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation
from services.config.types.test_config import MessageFilter
from services.pcap_service import PcapCaptureService
from services.test_services.test_assessment_service import TestCheck


def get_test_names() -> list:
    return [
        "Test Example Check",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:

    return [
        TestCheck(
            test_name="Test Example Check",
            test_method=is_data_present,
            test_params={
                "test_data": True,
            },
        ),
    ]
