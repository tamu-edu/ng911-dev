import copy
import ipaddress
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from test_suite.enums.packet_types import PacketTypeEnum, TransportProtocolEnum
from test_suite.services.config.types.config import Config
from test_suite.services.config.config_enum import EntityMode, EntityFunction
from test_suite.services.stub_server.enums import StubServerRole


@dataclass
class PortMapping:
    name: str
    protocol: str  # Should match PacketTypeEnum or TransportProtocolEnum
    port: int
    transport_protocol: TransportProtocolEnum


@dataclass
class Interface:
    name: str
    fqdn: Optional[str] = None
    ip: Optional[str] = None
    mask: Optional[str] = None
    gateway: Optional[str] = None
    dns: Optional[List[str]] = field(default_factory=list)
    port_mapping: Optional[List[PortMapping]] = field(default_factory=list)


@dataclass
class Entity:
    name: str
    role: List[StubServerRole]
    mode: EntityMode
    function: EntityFunction
    ip: Optional[str] = None
    fqdn: Optional[str] = None
    certificate_file: Optional[str] = None
    certificate_key: Optional[str] = None
    interfaces: Optional[List[Interface]] = field(default_factory=list)
    api: Optional[dict] = None
    api_http_url_prefix: Optional[str] = None


@dataclass
class LabConfig(Config):
    entities: List[Entity]
    test_suite_host_ip: str
    pca_certificate_file: Optional[str] = None
    pca_certificate_key: Optional[str] = None

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "LabConfig":
        """Create a LabConfig instance from a dictionary."""
        return cls(
            test_suite_host_ip=config_dict["lab_config"]["test_suite_host_ip"],
            pca_certificate_key=config_dict["lab_config"]["pca_certificate_key"],
            pca_certificate_file=config_dict["lab_config"]["pca_certificate_file"],
            entities=[
                Entity(
                    name=entity["name"],
                    mode=entity["mode"],
                    role=entity["role"],
                    function=entity["function"],
                    fqdn=entity.get("fqdn"),
                    certificate_file=entity.get("certificate_file"),
                    certificate_key=entity.get("certificate_key"),
                    api_http_url_prefix=entity.get("api_http_url_prefix") or "",
                    api=copy.deepcopy(entity.get("api")),
                    interfaces=[
                        Interface(
                            name=interface["name"],
                            fqdn=interface.get("fqdn"),
                            ip=interface.get("ip"),
                            mask=interface.get("mask"),
                            gateway=interface.get("gateway"),
                            dns=interface.get("dns", []),
                            port_mapping=[
                                PortMapping(**mapping)
                                for mapping in interface.get("port_mapping", [])
                            ],
                        )
                        for interface in entity.get("interfaces", [])
                    ],
                )
                for entity in config_dict["lab_config"]["entities"] or []
            ],
        )

    def validate(self) -> bool:
        """Validate the configuration."""
        errors = []

        for entity in self.entities:
            if not entity.name:
                errors.append("Entity name cannot be empty.")
            if not entity.function:
                errors.append(f"Entity type for {entity.name} cannot be empty.")
            if not entity.mode:
                errors.append(f"Entity type for {entity.name} cannot be empty.")

            for interface in entity.interfaces or []:
                if not interface.name:
                    errors.append(
                        f"Interface name in entity {entity.name} cannot be empty."
                    )
                if interface.ip and not self.is_valid_ip(interface.ip):
                    errors.append(
                        f"Invalid IP address: {interface.ip} in interface {interface.name}."
                    )
                if interface.mask and not self.is_valid_subnet_mask(interface.mask):
                    errors.append(
                        f"Invalid subnet mask: {interface.mask} in interface {interface.name}."
                    )
                if interface.gateway and not self.is_valid_ip(interface.gateway):
                    errors.append(
                        f"Invalid gateway: {interface.gateway} in interface {interface.name}."
                    )

                for mapping in interface.port_mapping or []:
                    if (
                        mapping.protocol not in PacketTypeEnum.list()
                        and mapping.protocol not in TransportProtocolEnum.list()
                    ):
                        errors.append(
                            f"Invalid protocol: {mapping.protocol} in interface {interface.name}."
                        )
                    if not (0 <= mapping.port <= 65535):
                        errors.append(
                            f"Invalid port: {mapping.port} in interface {interface.name}."
                        )

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
            "lab_config": {
                "test_suite_host_ip": self.test_suite_host_ip,
                "pca_certificate_key": self.pca_certificate_key,
                "pca_certificate_file": self.pca_certificate_file,
                "entities": [
                    {
                        "name": entity.name,
                        "mode": entity.mode,
                        "role": entity.role,
                        "function": entity.function,
                        "fqdn": entity.fqdn,
                        "certificate_file": entity.certificate_file,
                        "certificate_key": entity.certificate_key,
                        "api_http_url_prefix": entity.api_http_url_prefix or "",
                        "api": copy.deepcopy(entity.api),
                        "interfaces": [
                            {
                                "name": interface.name,
                                "fqdn": interface.fqdn,
                                "ip": interface.ip,
                                "mask": interface.mask,
                                "gateway": interface.gateway,
                                "dns": interface.dns,
                                "port_mapping": [
                                    {
                                        "name": mapping.name,
                                        "protocol": mapping.protocol,
                                        "port": mapping.port,
                                        "transport_protocol": mapping.transport_protocol,
                                    }
                                    for mapping in interface.port_mapping or []
                                ],
                            }
                            for interface in entity.interfaces or []
                        ],
                    }
                    for entity in self.entities or []
                ],
            }
        }

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Validate IP address format."""
        import re

        ip_regex = re.compile(
            r"^((25[0-5]|2[0-4][0-9]|1[0-9]{1,2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{1,2}|[1-9]?[0-9])$"
        )
        return bool(ip_regex.match(ip))

    @staticmethod
    def is_valid_subnet_mask(mask: str) -> bool:
        """Validate subnet mask."""
        try:
            ipaddress.IPv4Network(f"0.0.0.0/{mask}")
            return True
        except ValueError:
            return False

    def get_interfaces_data(self) -> dict:
        interfaces_data_list = {}
        for entity in self.entities or []:
            for interface in entity.interfaces or []:
                interfaces_data_list[interface.name] = {
                    "fqdn": interface.fqdn,
                    "ip": interface.ip,
                }

        return interfaces_data_list
