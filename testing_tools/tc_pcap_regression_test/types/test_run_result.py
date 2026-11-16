from dataclasses import dataclass
from enum import Enum

from testing_tools.base.run_result import BaseResult


class RunStatus(str, Enum):
    FINISHED = "finished"
    ABORTED = "aborted"
    MISSING_LAB_CONFIG = "missing_lab_config"
    MISSING_TEST_CONFIG = "missing_test_config"
    MISSING_PCAP = "missing_pcap"


@dataclass
class TCPRResult(BaseResult):
    test_id: str
    status: RunStatus
    verdict: str | None = None
    error: str | None = None
    error_category: str | None = None
    warnings: list[str] | None = None
