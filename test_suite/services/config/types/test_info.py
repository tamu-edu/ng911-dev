from dataclasses import dataclass
from typing import Dict
from services.config.types.config import Config


@dataclass
class TestInfo(Config):
    spec_name: str
    spec_version: str

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "TestInfo":
        """Create a LabConfig instance from a dictionary."""
        return cls(
            spec_name=config_dict["test_info"]["spec_name"],
            spec_version=config_dict["test_info"]["spec_version"]
        )

    def validate(self) -> bool:
        """Validate the configuration."""
        errors = []

        if not isinstance(self.spec_name, str) or not self.spec_name:
            errors.append(f"Specification Name must be str and cannot be empty.")

        if not isinstance(self.spec_version, str) or not self.spec_version:
            errors.append(f"Specification Version must be str and cannot be empty.")

        self._is_validated = len(errors) == 0
        if errors:
            for error in errors:
                print(f"Validation Error: {error}")
            return False
        return True

    def to_dict(self) -> Dict:
        """Convert the configuration object to a dictionary."""
        # TODO update
        return {
            "test_info": {
                "spec_name": self.spec_name,
                "spec_version": self.spec_version,
            }
        }
