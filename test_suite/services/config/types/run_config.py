from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from .config import Config
from services.report.report_enums import ReportType
from logger.log_enum import LogLevel
from services.config.config_enum import ScenarioMode, FilterMessageType


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


@dataclass
class RunVariation:
    name: str
    mode: ScenarioMode
    pcap_file: Optional[str] = None
    params: Optional[Dict[str, any]] = None
    filtering_options: Optional[MessageFilter] = None


@dataclass
class RunRequirement:
    name: str
    variations: List[str]


@dataclass
class RunTest:
    name: str
    requirements: List[RunRequirement]
    variations: List[RunVariation]


@dataclass
class LogConfig:
    level: LogLevel
    output_file: str

    def get_values(self) -> dict:
        """Return the LogConfig attributes as a dictionary."""
        return asdict(self)


@dataclass
class ReportFile:
    type: ReportType
    path: str


@dataclass
class GlobalConfig:
    response_timeout: int
    type: str
    report_files: List[ReportFile]
    log: LogConfig


@dataclass
class RunConfig(Config):
    global_config: GlobalConfig
    tests: List[RunTest] = field(default_factory=list)

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'RunConfig':
        return cls(
            global_config=GlobalConfig(
                response_timeout=config_dict["run_config"]["global"]["response_timeout"],
                type=config_dict["run_config"]["global"]["type"],
                report_files=[ReportFile(**rf) for rf in config_dict["run_config"]["global"]["report_files"]],
                log=LogConfig(**config_dict["run_config"]["global"]["log"])
            ),
            tests=[RunTest(
                name=test["name"],
                requirements=[RunRequirement(**req) for req in test["requirements"]],
                variations=[RunVariation(
                    name=var["name"],
                    mode=ScenarioMode(var["mode"]),
                    pcap_file=var.get("pcap_file"),
                    params=var.get("params"),
                    filtering_options=[
                        MessageFilter(**message_filter)
                        for message_filter in var["filtering_options"]
                    ] if "filtering_options" in var else None
                ) for var in test["variations"]]
            ) for test in config_dict["run_config"].get("tests", [])]
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def get_log_config(self) -> LogConfig:
        """Return the logging configuration."""
        return self.global_config.log

    def validate(self):
        errors = []
        if self.global_config.response_timeout <= 0:
            errors.append("Response timeout must be greater than 0.")
        if self.global_config.log.level not in LogLevel.list():
            errors.append("Invalid log level.")
        for rf in self.global_config.report_files:
            if rf.type not in ReportType.list():
                errors.append(f"Invalid report file type: {rf.type}")
        if errors:
            raise ValueError(errors)
