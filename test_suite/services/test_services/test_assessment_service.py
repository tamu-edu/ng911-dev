from logger.logger_service import LoggingMeta
from services.pcap_service import PcapCaptureService
from services.test_services.types.test_verdict import TestVerdict


class TestCheck:
    test_name: str

    def __init__(self, test_name: str, test_params: dict, test_method):
        self.test_name = test_name
        self.test_params = test_params
        self.test_method = test_method


class TestAssessmentService(metaclass=LoggingMeta):
    general_verdict: str
    intermediate_verdicts: list[TestVerdict]
    pcap_service: PcapCaptureService | None

    def __init__(
            self,
            name: str,
            tests_list: list[TestCheck],
            subtests_list: list[str] | None = None
    ):
        self.name = name
        self.tests_list = tests_list or []
        self.intermediate_verdicts = []
        self.subtests_list = subtests_list

    def prepare_verdicts_of_certain_subtests(self):
        for subtest in self.subtests_list:
            for test in self.tests_list:
                if test.test_name == subtest:
                    self.intermediate_verdicts.append(
                        TestVerdict(
                            test_name=test.test_name,
                            test_verdict=test.test_method(**test.test_params),
                        )
                    )

    def prepare_intermediate_verdicts(self):
        if self.subtests_list:
            self.prepare_verdicts_of_certain_subtests()
        else:
            for test in self.tests_list:
                self.intermediate_verdicts.append(
                    TestVerdict(
                        test_verdict=test.test_method(**test.test_params),
                        test_name=test.test_name
                    )
                )

    def get_intermediate_verdicts(self) -> list[TestVerdict]:
        return self.intermediate_verdicts

