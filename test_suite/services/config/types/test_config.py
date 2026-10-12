import copy
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from .config import Config
from services.config.config_enum import FilterMessageType


@dataclass
class MessageFilter:
    message_type: FilterMessageType
    src_interface: str
    dst_interface: str
    sip_method: Optional[str] = ""
    http_request_method: Optional[str] = ""
    response_status_code: Optional[str] = ""
    body_contains: Optional[str] = ""
    header_contains: Optional[str] = ""
    packet_type: Optional[str] = ""


@dataclass
class VarInterfaces:
    name: str
    port_names: List[str]


@dataclass
class Variation:
    name: str
    description: str
    interfaces: List[VarInterfaces]
    params: Dict[str, Any]
    filtering_options: Optional[List[MessageFilter]] = None


@dataclass
class Requirement:
    name: str
    variations: List[str]


@dataclass
class Preamble:
    method_name: str
    required_for: List[str]
    kwargs: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "required_for": self.required_for,
            "kwargs": copy.deepcopy(self.kwargs),
        }


@dataclass
class Postamble:
    method_name: str
    kwargs: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"method_name": self.method_name, "kwargs": copy.deepcopy(self.kwargs)}


@dataclass
class Test:
    name: str
    variations: List[Variation]
    requirements: List[Requirement]
    preamble_list: List[Preamble]
    postamble_list: List[Postamble]


@dataclass
class Conformance:
    tests: List[Test]


@dataclass
class TestConfig(Config):
    conformance: Conformance

    @classmethod
    def from_dict(cls, config_dict: dict) -> "TestConfig":
        return cls(
            conformance=Conformance(
                tests=[
                    Test(
                        name=test["name"],
                        variations=[
                            Variation(
                                name=var.get("name"),
                                description=var.get("description"),
                                interfaces=[
                                    VarInterfaces(
                                        name=_if.get("name"),
                                        port_names=_if.get("port_names"),
                                    )
                                    for _if in var.get("interfaces")
                                ],
                                params=copy.deepcopy(var.get("params")),
                                filtering_options=copy.deepcopy(
                                    var.get("filtering_options")
                                ),
                            )
                            for var in test["variations"]
                        ],
                        requirements=[
                            Requirement(**req) for req in test["requirements"]
                        ],
                        preamble_list=[
                            Preamble(
                                method_name=preamble.get("method_name"),
                                required_for=preamble.get("required_for"),
                                kwargs=copy.deepcopy(preamble.get("kwargs")),
                            )
                            for preamble in (test.get("preamble_list") or [])
                        ],
                        postamble_list=[
                            Postamble(
                                method_name=postamble.get("method_name"),
                                kwargs=copy.deepcopy(postamble.get("kwargs")),
                            )
                            for postamble in (test.get("postamble_list") or [])
                        ],
                    )
                    for test in config_dict["test_config"]["conformance"]["tests"]
                ]
            )
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def validate(self):
        errors: List[Any] = []
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
