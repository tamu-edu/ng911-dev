from dataclasses import dataclass, field
from typing import List

from services.test_services.test_conduction_service import TestConductionService
from services.test_services.types.test_verdict import VerdictType, TestVerdict


@dataclass
class OracleTestScenario:
    name: str
    scenario_verdict: TestVerdict | None = None
    tests: List[TestConductionService] = field(default_factory=list)
    intermediate_verdicts: List[TestVerdict] = field(default_factory=list)

    def __init__(
            self,
            name: str,
            tests: List[TestConductionService]
    ):
        self.name = name
        self.tests = tests
        self.intermediate_verdicts = []

    def add_intermediate_verdicts(self, verdicts: List[TestVerdict]):
        self.intermediate_verdicts.extend(verdicts)

    def calculate_scenario_verdict(self):
        for _verdict in self.intermediate_verdicts:
            if VerdictType.FAILED in str(_verdict.test_verdict):
                self.scenario_verdict = TestVerdict(
                    test_name=self.name,
                    test_verdict=VerdictType.FAILED
                )
                return self
        self.scenario_verdict = TestVerdict(
            test_name=self.name,
            test_verdict=VerdictType.PASSED
        )

    def get_scenario_verdict(self):
        return self.scenario_verdict

    def print_scenario_verdict(self):
        print(f"Variation: {self.name}, Test verdict: {self.scenario_verdict.test_verdict.value}")
        print("-" * 50)
        for _verdict in self.intermediate_verdicts:
            print(f"{_verdict.test_verdict.value} - Test: {_verdict.test_name} -> Result: {_verdict.error or VerdictType.PASSED}")
        print("=" * 50)
