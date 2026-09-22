from dataclasses import dataclass, fields, asdict
from typing import Dict, List
from test_suite.services.config.types.config import Config


@dataclass
class Conduit:
    name: str
    from_if: str
    to_if: str
    proxy_if: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ForwardConduit(Config):
    forward_conduits: List[Conduit]

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "ForwardConduit":
        """Create a ForwardConduit instance from a dictionary."""
        return cls(
            forward_conduits=[
                Conduit(**conduit) for conduit in config_dict["forward_conduits"]
            ]
        )

    def validate(self) -> bool:
        """Validate the configuration."""
        errors = []

        for conduit in self.forward_conduits:
            for field in fields(conduit):
                value = getattr(conduit, field.name)

                if not isinstance(value, str) or not value.strip():
                    errors.append(f"Field '{field.name}' must be a non-empty string.")

        self._is_validated = len(errors) == 0
        if errors:
            for error in errors:
                print(f"Validation Error: {error}")
            return False
        return True

    def to_dict(self) -> Dict:
        """Convert the configuration object to a dictionary."""
        return asdict(self)
