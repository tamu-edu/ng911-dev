import os
import glob
from typing import cast

from test_suite.services.config.schemas.requirements_schema import REQUIREMENTS_SCHEMA


class TestDiscoveryService:
    PCAPS_DIR = "test_suite/pcaps"
    TEST_CONF_DIR = "test_configs"

    @classmethod
    def discover_all_test_ids(cls) -> list[str]:
        # REQUIREMENTS_SCHEMA is an untyped dict literal in test_suite mixing
        # str values (test_id) and list[str] values (subtests) — mypy infers
        # the join type as Sequence[str], so entry["test_id"] needs an
        # explicit cast back to str (it is one at runtime; test_suite's
        # schema files are off-limits to annotate).
        return sorted(
            {
                cast(str, entry["test_id"])
                for entry in REQUIREMENTS_SCHEMA.values()
                if isinstance(entry, dict) and entry.get("test_id")
            }
        )

    @classmethod
    def get_lab_config_path(cls, test_id: str) -> str | None:
        matches = glob.glob(os.path.join(cls.PCAPS_DIR, test_id, "*lab_config*.yaml"))
        return matches[0] if matches else None

    @classmethod
    def get_pcap_files(cls, test_id: str) -> list[str]:
        test_dir = os.path.join(cls.PCAPS_DIR, test_id)
        if not os.path.isdir(test_dir):
            return []
        return sorted(f for f in os.listdir(test_dir) if f.lower().endswith(".pcap"))

    @classmethod
    def get_test_config_path(cls, test_id: str) -> str | None:
        path = os.path.join(cls.TEST_CONF_DIR, f"test_config_{test_id.lower()}.yaml")
        return path if os.path.isfile(path) else None
