import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enums.packet_types import PacketTypeEnum, TransportProtocolEnum
from services.config.types.config import Config
from services.config.config_enum import EntityMode, EntityFunction
from services.stub_server.enums import StubServerRole


@dataclass
class PortMapping:
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
    role: StubServerRole
    mode: EntityMode
    function: EntityFunction
    ip: Optional[str] = None
    fqdn: Optional[str] = None
    certificate_file: Optional[str] = None
    certificate_key: Optional[str] = None
    interfaces: Optional[List[Interface]] = field(default_factory=list)


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
            entities=[
                Entity(
                    name=entity["name"],
                    mode=entity["mode"],
                    role=entity["role"],
                    function=entity["function"],
                    fqdn=entity.get("fqdn"),
                    certificate_file=entity.get("certificate_file"),
                    certificate_key=entity.get("certificate_key"),
                    interfaces=[
                        Interface(
                            name=interface["name"],
                            fqdn=interface.get("fqdn"),
                            ip=interface.get("ip"),
                            mask=interface.get("mask"),
                            gateway=interface.get("gateway"),
                            dns=interface.get("dns", []),
                            port_mapping=[
                                PortMapping(**mapping) for mapping in interface.get("port_mapping", [])
                            ]
                        )
                        for interface in entity.get("interfaces", [])
                    ]
                )
                for entity in config_dict["lab_config"]["entities"]
            ]
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

            for interface in entity.interfaces:
                if not interface.name:
                    errors.append(f"Interface name in entity {entity.name} cannot be empty.")
                if interface.ip and not self.is_valid_ip(interface.ip):
                    errors.append(f"Invalid IP address: {interface.ip} in interface {interface.name}.")
                if interface.mask and not self.is_valid_subnet_mask(interface.mask):
                    errors.append(f"Invalid subnet mask: {interface.mask} in interface {interface.name}.")
                if interface.gateway and not self.is_valid_ip(interface.gateway):
                    errors.append(f"Invalid gateway: {interface.gateway} in interface {interface.name}.")

                for mapping in interface.port_mapping:
                    if mapping.protocol not in PacketTypeEnum.list() and mapping.protocol not in TransportProtocolEnum.list():
                        errors.append(f"Invalid protocol: {mapping.protocol} in interface {interface.name}.")
                    if not (0 <= mapping.port <= 65535):
                        errors.append(f"Invalid port: {mapping.port} in interface {interface.name}.")

        self._is_validated = len(errors) == 0
        if errors:
            for error in errors:
                print(f"Validation Error: {error}")
            return False
        return True

    @Config.validated
    def to_dict(self) -> Dict:
        """Convert the configuration object to a dictionary."""
        return {
            "lab_config": {
                "entities": [
                    {
                        "name": entity.name,
                        "mode": entity.mode,
                        "role": entity.role,
                        "fqdn": entity.fqdn,
                        "certificate_file": entity.certificate_file,
                        "certificate_key": entity.certificate_key,
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
                                        "protocol": mapping.protocol,
                                        "port": mapping.port,
                                        "transport_protocol": mapping.transport_protocol
                                    }
                                    for mapping in interface.port_mapping
                                ]
                            }
                            for interface in entity.interfaces
                        ]
                    }
                    for entity in self.entities
                ]
            }
        }

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Validate IP address format."""
        import re
        ip_regex = re.compile(
            r'^((25[0-5]|2[0-4][0-9]|1[0-9]{1,2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{1,2}|[1-9]?[0-9])$'
        )
        return bool(ip_regex.match(ip))

    @staticmethod
    def is_valid_subnet_mask(mask: str) -> bool:
        """Validate subnet mask."""
        valid_masks = [
            "255.255.255.255", "255.255.255.254", "255.255.255.252",
            "255.255.255.248", "255.255.255.240", "255.255.255.224",
            "255.255.255.192", "255.255.255.128", "255.255.255.0",
            "255.255.254.0", "255.255.252.0", "255.255.248.0",
            "255.255.240.0", "255.255.224.0", "255.255.192.0",
            "255.255.128.0", "255.255.0.0", "255.254.0.0",
            "255.252.0.0", "255.248.0.0", "255.240.0.0",
            "255.224.0.0", "255.192.0.0", "255.128.0.0",
            "255.0.0.0", "254.0.0.0", "252.0.0.0", "248.0.0.0",
            "240.0.0.0", "224.0.0.0", "192.0.0.0", "128.0.0.0", "0.0.0.0"
        ]
        return mask in valid_masks