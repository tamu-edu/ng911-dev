import copy
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from .config import Config
from services.report.report_enums import ReportType
from logger.log_enum import LogLevel
from services.config.config_enum import ScenarioMode, FilterMessageType
from services.config.types.test_config import VarInterfaces


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
    interfaces: List[VarInterfaces]
    description: Optional[str] = None
    pcap_file: Optional[str] = None
    params: Optional[Dict[str, any]] = None
    filtering_options: Optional[List[MessageFilter]] = None


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
    output_folder_path: str
    prefix: str
    suffix: str
    detailed_view: bool
    types: List[ReportType]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LabSummary:
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
    eng_name: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SupplierSummary:
    name: str
    addr_line_1: str
    addr_line_2: str
    city: str
    state: str
    country: str
    zip: str
    url: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IUTSummary:
    type: str
    name: str
    version: str
    test_period: str
    date_of_receipt: str
    location: str
    cs_id: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TestEnvSummary:
    ixit_id: str
    spec_name: str
    spec_version: str
    ts_version: str
    test_period_start: str
    test_period_end: str
    log_ref: str
    log_ret_date: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class IdSummary:
    lab: LabSummary
    supplier: SupplierSummary
    iut: IUTSummary
    test_env: TestEnvSummary

    def to_dict(self) -> dict:
        return {
            "lab": self.lab.to_dict(),
            "supplier": self.supplier.to_dict(),
            "iut": self.iut.to_dict(),
            "test_env": self.test_env.to_dict()
        }


@dataclass
class Comment:
    author: str
    comment: str


@dataclass
class GlobalConfig:
    type: str
    report_files: ReportFile
    id_summary: IdSummary
    log: LogConfig
    comments: List[Comment]

    def to_dict(self):
        return {
            "type": self.type,
            "report_files": self.report_files.to_dict(),
            "id_summary": self.id_summary.to_dict(),
            "log": self.log.get_values(),
            "comments": [
                {
                    "author": c.author,
                    "comment": c.comment
                }
                for c in self.comments
            ]
        }


@dataclass
class RunConfig(Config):
    output_folder: str
    global_config: GlobalConfig
    tests: List[RunTest] = field(default_factory=list)

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'RunConfig':
        return cls(
            output_folder=config_dict["run_config"]["output_folder"],
            global_config=GlobalConfig(
                type=config_dict["run_config"]["global"]["type"],
                report_files=ReportFile(**config_dict["run_config"]["global"]["report_files"]),
                log=LogConfig(**config_dict["run_config"]["global"]["log"]),
                id_summary=IdSummary(
                    lab=LabSummary(**config_dict["run_config"]["global"]["id_summary"]["lab"]),
                    supplier=SupplierSummary(**config_dict["run_config"]["global"]["id_summary"]["supplier"]),
                    iut=IUTSummary(**config_dict["run_config"]["global"]["id_summary"]["iut"]),
                    test_env=TestEnvSummary(**config_dict["run_config"]["global"]["id_summary"]["test_env"]),
                ),
                comments=[
                    Comment(**comment) for comment in config_dict["run_config"]["global"]["comments"]
                ],
            ),
            tests=[RunTest(
                name=test["name"],
                requirements=[RunRequirement(**req) for req in test["requirements"]],
                variations=[RunVariation(
                    name=var["name"],
                    description=var.get("description"),
                    interfaces=[VarInterfaces(**v) for v in var.get("interfaces")],
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
        return {
            "run_config": {
                "output_folder": self.output_folder,
                "global": self.global_config.to_dict(),
                "tests": [
                    {
                        "name": test.name,
                        "requirements": [
                            {
                                "name": rq.name,
                                "variations": [v for v in rq.variations]
                            } for rq in test.requirements
                        ],
                        "variations": [
                            {
                                "name": var.name,
                                "description": var.description,
                                "interfaces": [
                                    {
                                        "name": _if.name,
                                        "port_names": [pn for pn in _if.port_names]
                                    } for _if in var.interfaces
                                ],
                                "mode": var.mode or "online",
                                "pcap_file": var.pcap_file or "",
                                "params": copy.deepcopy(var.params),
                                "filtering_options": [
                                    {
                                        "message_type": mf.message_type,
                                        "src_interface": mf.src_interface,
                                        "dst_interface": mf.dst_interface,
                                        "sip_method": mf.sip_method or "",
                                        "http_request_method": mf.http_request_method or "",
                                        "response_status_code": mf.response_status_code or "",
                                        "body_contains": mf.body_contains or "",
                                        "header_contains": mf.header_contains or "",
                                    } for mf in var.filtering_options
                                ]
                            } for var in test.variations
                        ]
                    } for test in self.tests
                ]
            }
        }

    def validate(self):
        errors = []
        if self.global_config.log.level not in LogLevel.list():
            errors.append("Invalid log level.")
        for _type in self.global_config.report_files.types:
            if _type not in ReportType.list():
                errors.append(f"Invalid report file type: {_type}")
        if errors:
            raise ValueError(errors)
