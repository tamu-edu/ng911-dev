from dataclasses import dataclass, field
from typing import List

from services.test_services.test_assessment_service import TestAssessmentService
from services.test_services.types.test_verdict import VerdictType, TestVerdict


@dataclass
class OracleTestVariation:
    name: str
    scenario_verdict: TestVerdict | None = None
    tests: List[TestAssessmentService] = field(default_factory=list)
    intermediate_verdicts: List[TestVerdict] = field(default_factory=list)

    def __init__(
            self,
            name: str,
            tests: List[TestAssessmentService],
            description: str = None,
            variation_verdict: TestVerdict | None = None
    ):
        self.name = name
        self.tests = tests
        self.description = description
        self.intermediate_verdicts = []
        if variation_verdict:
            self.intermediate_verdicts.append(variation_verdict)

    @classmethod
    def from_not_run_var(
            cls,
            name: str,
            description: str = None
    ):
        return cls(
            name=name,
            description=description,
            tests=[],
            variation_verdict=TestVerdict(
                test_name=name,
                test_verdict=VerdictType.NOT_RUN,
                error=f"Variation {name} has not been conducted due to error, and has been finished with Not Run status."
            )
        )

    def add_intermediate_verdicts(self, verdicts: List[TestVerdict]):
        self.intermediate_verdicts.extend(verdicts)

    def summarise_error_messages(self) -> str:
        summ_err_msg = ""
        for _verdict in self.intermediate_verdicts:
            summ_err_msg += str(_verdict.error or "") + "; "
        return summ_err_msg

    def calculate_scenario_verdict(self):
        # Firstly we need to check if there are any FAILED
        for _verdict in self.intermediate_verdicts:
            if VerdictType.FAILED in str(_verdict.test_verdict):
                self.scenario_verdict = TestVerdict(
                    test_name=self.name,
                    test_verdict=VerdictType.FAILED,
                    error=self.summarise_error_messages()
                )
                return self
        # Then we can check on other variants
        for _verdict in self.intermediate_verdicts:
            if VerdictType.INC in str(_verdict.test_verdict):
                self.scenario_verdict = TestVerdict(
                    test_name=self.name,
                    test_verdict=VerdictType.INC,
                    error=self.summarise_error_messages()
                )
                return self
            if VerdictType.NOT_RUN in str(_verdict.test_verdict):
                self.scenario_verdict = TestVerdict(
                    test_name=self.name,
                    test_verdict=VerdictType.INC,
                    error=self.summarise_error_messages()
                )
                return self
        # if nothing is Failed or INC|NOT_RUN  => Passed
        self.scenario_verdict = TestVerdict(
            test_name=self.name,
            test_verdict=VerdictType.PASSED
        )

    def get_scenario_verdict(self):
        return self.scenario_verdict

    def print_scenario_verdict(self):
        print(f"Variation: {self.name}, Test verdict: {self.scenario_verdict.test_verdict.value}")
        print(f"Description: {self.description}")
        print("-" * 50)
        for _verdict in self.intermediate_verdicts:
            print(f"{_verdict.test_verdict.value} - Test: {_verdict.test_name} -> "
                  f"Result: {_verdict.error or VerdictType.PASSED}")
        print("=" * 50)
