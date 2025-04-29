from dataclasses import dataclass
from enum import Enum


class VerdictType(str, Enum):
    """
    Enum for General Verdict variants.
    """
    FAILED = "FAILED"
    PASSED = "PASSED"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


@dataclass
class TestVerdict:
    test_name: str
    test_verdict: VerdictType
    error: str | None

    def __init__(self, test_verdict: VerdictType, test_name: str, error: str | None = None):
        self.test_name = test_name
        if VerdictType.FAILED in test_verdict:
            self.test_verdict = VerdictType.FAILED
        else:
            self.test_verdict = VerdictType.PASSED
        self.error = test_verdict