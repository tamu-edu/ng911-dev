from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from .config import Config


@dataclass
class Variation:
    name: str
    description: str
    params: Dict[str, any]


@dataclass
class Requirement:
    name: str
    variations: List[str]


@dataclass
class Test:
    name: str
    variations: List[Variation]
    requirements: List[Requirement]


@dataclass
class Conformance:
    tests: List[Test]


@dataclass
class TestConfig(Config):
    conformance: Conformance

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'TestConfig':
        return cls(
            conformance=Conformance(
                tests=[Test(
                    name=test["name"],
                    variations=[Variation(**var) for var in test["variations"]],
                    requirements=[Requirement(**req) for req in test["requirements"]]
                ) for test in config_dict["test_config"]["conformance"]["tests"]]
            )
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def validate(self):
        errors = []
        for test in self.conformance.tests:
            if not test.name:
                errors.append("Test name cannot be empty.")
            for var in test.variations:
                if not var.name:
                    errors.append("Variation name cannot be empty.")
                if not var.description:
                    errors.append("Variation description cannot be empty.")
            for req in test.requirements:
                if not req.name:
                    errors.append("Requirement name cannot be empty.")
                if not req.variations:
                    errors.append("Requirement variations list cannot be empty.")

        if errors:
            raise ValueError(errors)
