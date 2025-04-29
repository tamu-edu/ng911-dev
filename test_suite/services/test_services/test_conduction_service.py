from logger.logger_service import LoggingMeta
from services.pcap_service import PcapCaptureService
from services.test_services.types.test_verdict import TestVerdict


class TestCheck:
    test_name: str

    def __init__(self, test_name: str, test_params: dict, test_method):
        self.test_name = test_name
        self.test_params = test_params
        self.test_method = test_method


class TestConductionService(metaclass=LoggingMeta):
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
        self.tests_list = tests_list
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

    def calculate_general_verdict(self):
        """
        TODO to be deprecated
        """
        for _verdict in self.intermediate_verdicts:
            if "FAILED" in str(_verdict.test_verdict):
                self.general_verdict = "FAILED"
                return self
        self.general_verdict = "PASSED"
        return self

    def get_general_verdict(self):
        """
        TODO to be deprecated
        """
        return self.general_verdict

    def print_general_verdict(self):
        """
        TODO to be deprecated
        """
        print(f"Scenario: {self.name}")
        print("-" * 50)
        print(f"General verdict: {self.general_verdict}")
        print("-" * 50)
        for _verdict in self.intermediate_verdicts:
            print(f"{_verdict.test_name} -> {_verdict.test_verdict.value}")
        print("=" * 50)


