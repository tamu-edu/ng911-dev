from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from .config import Config
from services.report.report_enums import ReportType
from logger.log_enum import LogLevel
from services.config.types.run_config import ReportFile, LogConfig, SupplierSummary


@dataclass
class IUT:
    name: str
    type: str
    version: str
    test_period: str
    date_of_receipt: str
    location: str
    cs_id: str


@dataclass
class LaunchTest:
    iut: IUT
    lab_config: str
    requirements: List[str]


@dataclass
class LaunchTestEnvSummary:
    ixit_id: str
    ts_version: str
    test_period_start: str
    test_period_end: str
    log_ref: str
    log_ret_date: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LaunchIdSummary:
    eng_name: str
    supplier: SupplierSummary
    test_env: LaunchTestEnvSummary

    def to_dict(self) -> dict:
        return {
            "eng_name": self.eng_name,
            "supplier": self.supplier.to_dict(),
            "test_env": self.test_env.to_dict()
        }


@dataclass
class Comment:
    author: str
    comment: str


@dataclass
class LaunchGlobalConfig:
    lab_info: str
    type: str
    report_files: ReportFile
    id_summary: LaunchIdSummary
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
class LaunchConfig(Config):
    output_folder: str
    global_config: LaunchGlobalConfig
    tests: List[LaunchTest] = field(default_factory=list)

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'LaunchConfig':
        return cls(
            output_folder=config_dict["launch_config"]["output_folder"],
            global_config=LaunchGlobalConfig(
                lab_info=config_dict["launch_config"]["global_config"]["lab_info"],
                type=config_dict["launch_config"]["global_config"]["type"],
                report_files=ReportFile(**config_dict["launch_config"]["global_config"]["report_files"]),
                log=LogConfig(
                    level=config_dict["launch_config"]["global_config"]["log"]["level"],
                    output_file=cls._get_log_output_file_value(
                        config_dict["launch_config"]["output_folder"],
                        config_dict["launch_config"]["global_config"]["log"]["output_file"]
                    )
                ),
                id_summary=LaunchIdSummary(
                    eng_name=config_dict["launch_config"]["global_config"]["id_summary"]["eng_name"],
                    supplier=SupplierSummary(**config_dict["launch_config"]["global_config"]["id_summary"]["supplier"]),
                    test_env=LaunchTestEnvSummary(**config_dict["launch_config"]["global_config"]["id_summary"]["test_env"])
                ),
                comments=[
                    Comment(**comment) for comment in config_dict["launch_config"]["global_config"]["comments"]
                ],
            ),
            tests=[LaunchTest(
                iut=IUT(**test["iut"]),
                requirements=test["requirements"],
                lab_config=test["lab_config"]
            ) for test in config_dict["launch_config"].get("tests", [])]
        )

    @classmethod
    def _get_log_output_file_value(cls, output_folder: str = None, path: str = None) -> str:
        if path:
            if "/" in path:
                return path
            else:
                return output_folder + "/" + path
        else:
            return output_folder + "/tmp.log"

    def add_test_id_to_output_folder(self, test_id: str) -> None:
        if self.output_folder[-1] == "/":
            self.output_folder = self.output_folder + test_id
        else:
            self.output_folder = self.output_folder + "/" + test_id

    def add_test_id_to_log_output(self, test_id: str) -> None:
        split = self.global_config.log.output_file.split("/")
        value = ""
        for v in split[:-1]:
            value += v + "/"
        value += test_id + "/" + split[-1]
        self.global_config.log.output_file = value

    def to_dict(self) -> dict:
        return asdict(self)

    def get_log_config(self) -> LogConfig:
        """Return the logging configuration."""
        return self.global_config.log

    def validate(self):
        errors = []
        if self.global_config.log.level not in LogLevel.list():
            errors.append("Invalid log level.")
        for _type in self.global_config.report_files.types:
            if _type not in ReportType.list():
                errors.append(f"Invalid report file type: {_type}")
        if errors:
            raise ValueError(errors)
