from dataclasses import dataclass, fields
from typing import Dict
from test_suite.services.config.types.config import Config


@dataclass
class LabInfo(Config):
    name: str
    accred_status: str
    accred_ref: str
    accred_auth: str
    addr_line_1: str
    addr_line_2: str
    city: str
    state: str
    country: str
    zip: str
    url: str

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "LabInfo":
        """Create a LabConfig instance from a dictionary."""
        return cls(
            name=config_dict["lab_info"]["name"],
            accred_status=config_dict["lab_info"]["accred_status"],
            accred_ref=config_dict["lab_info"]["accred_ref"],
            accred_auth=config_dict["lab_info"]["accred_auth"],
            addr_line_1=config_dict["lab_info"]["addr_line_1"],
            addr_line_2=config_dict["lab_info"]["addr_line_2"],
            city=config_dict["lab_info"]["city"],
            state=config_dict["lab_info"]["state"],
            country=config_dict["lab_info"]["country"],
            zip=config_dict["lab_info"]["zip"],
            url=config_dict["lab_info"]["url"],
        )

    def validate(self) -> bool:
        """Validate the configuration."""
        errors = []

        for field in fields(self):
            value = getattr(self, field.name)

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
        # TODO update
        return {
            "lab_info": {
                "name": self.name,
                "accred_status": self.accred_status,
                "accred_ref": self.accred_ref,
                "accred_auth": self.accred_auth,
                "addr_line_1": self.addr_line_1,
                "addr_line_2": self.addr_line_2,
                "city": self.city,
                "state": self.state,
                "country": self.country,
                "zip": self.zip,
                "url": self.url,
            }
        }
