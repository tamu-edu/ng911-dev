import copy
import json
from datetime import datetime
from typing import Optional

import yaml

from test_suite.services.config.config_enum import EntityFunction, ScenarioMode, FilterMessageType
from test_suite.services.config.config_service import ConfigService
from test_suite.services.config.errors.run_config_generation_error import RunConfigGenerationError
from test_suite.services.config.types.lab_info import LabInfo
from test_suite.services.config.types.run_config import (
    RunConfig,
    GlobalConfig,
    IdSummary,
    LabSummary,
    SupplierSummary,
    IUTSummary,
    TestEnvSummary, RunTest, RunRequirement, RunVariation, MessageFilter
)
from test_suite.services.config.types.launch_config import LaunchConfig, LaunchTest
from test_suite.services.config.types.lab_config import LabConfig
from test_suite.services.config.types.test_config import TestConfig, VarInterfaces
from test_suite.services.config.types.test_info import TestInfo

from test_suite.services.config.schemas.requirements_schema import REQUIREMENTS_SCHEMA
from test_suite.services.stub_server.enums import StubServerRole, StubServerProtocol

TEST_CONF_FOLDER = "test_configs"


class QuotedStringDumper(yaml.SafeDumper):
    pass


def represent_str(self, data):
    return self.represent_scalar('tag:yaml.org,2002:str', data, style='"')


def represent_none(self, data):
    return self.represent_scalar('tag:yaml.org,2002:null', '')


class RunConfigService:
    run_config: RunConfig
    _run_config_filename: Optional[str]

    def __init__(self, run_config: RunConfig, run_config_filename: str = None):
        self.run_config = run_config
        self._run_config_filename = run_config_filename

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'RunConfigService':
        """Create a RunConfigService instance from a dictionary."""
        return cls(
            run_config=RunConfig.from_dict(config_dict)
        )

    @classmethod
    def from_launch_config(cls, launch_config: LaunchConfig,
                           test: LaunchTest, lab_config: LabConfig) -> "RunConfigService":
        """Create a RunConfigService instance from provided launch_config."""

        print(f"Validating and parsing LAB INFO -> {launch_config.global_config.lab_info}")
        if not ConfigService.validate_lab_info(launch_config.global_config.lab_info):
            print(f"❌ LAB INFO parsing failed.")
            raise RunConfigGenerationError(f"Impossible to generate run_config due to LAB INFO errors")
        print(f"✅ LAB INFO successfully parsed.")
        lab_info = LabInfo.from_dict(
            ConfigService.parse_config_file(launch_config.global_config.lab_info)
        )

        print(f"Parsing Test Info -> {TEST_CONF_FOLDER}/test__info.yaml")
        if not ConfigService.validate_test_info(f"{TEST_CONF_FOLDER}/test__info.yaml"):
            print(f"❌ TEST INFO parsing failed.")
            raise RunConfigGenerationError(f"Impossible to generate run_config due to TEST INFO errors")
        print(f"✅ TEST INFO successfully parsed.")
        test_info = TestInfo.from_dict(
            ConfigService.parse_config_file(f"{TEST_CONF_FOLDER}/test__info.yaml")
        )

        run_config_filename = f"run_config_{test.iut.name.lower()}_{datetime.now().strftime('%d_%B_%Y_%H:%M:%S')}"
        run_config = cls._generate_conformance_run_config(
            launch_config=launch_config,
            test_info=test_info,
            lab_config=lab_config,
            lab_info=lab_info,
            test=test
        )
        return cls(run_config=run_config, run_config_filename=run_config_filename)

    @staticmethod
    def extract_rq_test_id(rq_schema_key: str, test_ids_list: list) -> list:
        # TODO use this till each element in RQ schema would not have test_id
        _tid = REQUIREMENTS_SCHEMA.get(rq_schema_key)
        if _tid:
            _tid = _tid.get("test_id")
            if _tid and _tid not in test_ids_list:
                test_ids_list.append(_tid)
        else:
            print(f"ℹ️ {rq_schema_key} cannot be tested yet "
                  f"as we do not have implemented the tests for it.")
        return test_ids_list

    @staticmethod
    def __get_stimulus_src_interface_name(entities) -> str:
        from_name, to_name = None, None
        for entity in entities:
            if entity.role == StubServerRole.SENDER:
                from_name = entity.name
            if entity.role == StubServerRole.IUT:
                to_name = entity.name
        if from_name and to_name:
            return f"IF_{from_name}_{to_name}"
        return f""

    @staticmethod
    def __get_output_src_interface_name(entities) -> str:
        from_name, to_name = None, None
        for entity in entities:
            if entity.role == StubServerRole.RECEIVER:
                from_name = entity.name
            if entity.role == StubServerRole.IUT:
                to_name = entity.name
        if from_name and to_name:
            return f"IF_{to_name}_{from_name}"
        return f""

    @staticmethod
    def __get_dst_interface_name(src_interface_name: str) -> str:
        if_name_splited = src_interface_name.split("_")
        return f"IF_{if_name_splited[2]}_{if_name_splited[1]}"

    @classmethod
    def get_message_filtering_options(
            cls,
            message_type: FilterMessageType,
            params: dict,
            lab_config: LabConfig
    ) -> MessageFilter:
        entities = lab_config.entities
        src_if, dst_if = "", ""

        _kwargs = {}

        if message_type == FilterMessageType.STIMULUS.value:
            src_if = cls.__get_stimulus_src_interface_name(entities)
            dst_if = cls.__get_dst_interface_name(src_if)
            for message in params['messages']:
                if message['action'] == "send":
                    if message['type'] == StubServerProtocol.SIP.value:
                        _kwargs['sip_method'] = message.get('method') or ""
                    if message['type'] == StubServerProtocol.HTTP.value:
                        _kwargs['http_request_method'] = message.get('method') or ""
                        _kwargs['response_status_code'] = message.get('response_code') or ""
                    _kwargs['header_contains'] = message.get('header_contains') or ""
                    _kwargs['body_contains'] = message.get('body_contains') or ""

        elif message_type == FilterMessageType.OUTPUT.value:
            src_if = cls.__get_output_src_interface_name(entities)
            dst_if = cls.__get_dst_interface_name(src_if)
            for message in params['messages']:
                if message['action'] == "receive":
                    if message['type'] == StubServerProtocol.SIP.value:
                        _kwargs['sip_method'] = message.get('method') or ""
                    if message['type'] == StubServerProtocol.HTTP.value:
                        _kwargs['http_request_method'] = message.get('method') or ""
                        _kwargs['response_status_code'] = message.get('response_code') or ""
                    _kwargs['header_contains'] = message.get('header_contains') or ""
                    _kwargs['body_contains'] = message.get('body_contains') or ""

        message_filtering_options = MessageFilter(
            message_type=message_type,
            src_interface=src_if,
            dst_interface=dst_if,
            **_kwargs
        )

        return message_filtering_options

    @classmethod
    def get_filtering_options(
            cls,
            params: dict,
            lab_config: LabConfig
    ) -> [MessageFilter]:
        filter_options = [
            cls.get_message_filtering_options(
                FilterMessageType.STIMULUS.value,
                params,
                lab_config
            ),
        ]
        for message in params['messages']:
            if message['action'] == "receive":
                filter_options.append(
                    cls.get_message_filtering_options(
                        FilterMessageType.OUTPUT.value,
                        params,
                        lab_config
                    )
                )

        return filter_options

    @classmethod
    def __get_var_list_for_rq(cls, rq_vars: list, test_vars: list) -> list:
        var_list = []
        is_all = False
        if "all" in rq_vars:
            is_all = True
        for _var in test_vars:
            if _var.name in rq_vars or is_all:
                var_list.append(_var.name)
        return var_list

    @classmethod
    def _generate_conformance_run_config(
            cls,
            launch_config: LaunchConfig,
            test: LaunchTest,
            test_info: TestInfo,
            lab_info: LabInfo,
            lab_config: LabConfig
    ) -> RunConfig:
        global_config = GlobalConfig(
            type=launch_config.global_config.type,
            report_files=copy.deepcopy(launch_config.global_config.report_files),
            log=copy.deepcopy(launch_config.global_config.log),
            comments=copy.deepcopy(launch_config.global_config.comments),
            id_summary=IdSummary(
                lab=LabSummary(
                    name=lab_info.name,
                    accred_status=lab_info.accred_status,
                    accred_ref=lab_info.accred_ref,
                    accred_auth=lab_info.accred_auth,
                    addr_line_1=lab_info.addr_line_1,
                    addr_line_2=lab_info.addr_line_2,
                    city=lab_info.city,
                    state=lab_info.state,
                    country=lab_info.country,
                    zip=lab_info.zip,
                    url=lab_info.url,
                    eng_name=launch_config.global_config.id_summary.eng_name,
                ),
                supplier=copy.deepcopy(launch_config.global_config.id_summary.supplier),
                iut=IUTSummary(
                    type=test.iut.type,
                    name=test.iut.name,
                    version=test.iut.version,
                    test_period=test.iut.test_period,
                    date_of_receipt=test.iut.date_of_receipt,
                    location=test.iut.location,
                    cs_id=test.iut.cs_id
                ),
                test_env=TestEnvSummary(
                    ixit_id=launch_config.global_config.id_summary.test_env.ixit_id,
                    spec_name=test_info.spec_name,
                    spec_version=test_info.spec_version,
                    ts_version=launch_config.global_config.id_summary.test_env.ts_version,
                    test_period_start=launch_config.global_config.id_summary.test_env.test_period_start,
                    test_period_end=launch_config.global_config.id_summary.test_env.test_period_end,
                    log_ref=launch_config.global_config.id_summary.test_env.log_ref,
                    log_ret_date=launch_config.global_config.id_summary.test_env.log_ret_date,
                )
            )
        )

        test_ids_list = []
        test_configs = []

        for rq in test.requirements:
            _rq, _type, _num = rq.split("_")

            if test.iut.type != _type:
                raise RunConfigGenerationError(f"Unexpected RQ - {rq} for the test of {test.iut.type}")

            if _num == '*':
                for rq_schema_key in REQUIREMENTS_SCHEMA.keys():
                    if f"{_rq}_{_type}" in rq_schema_key:
                        print(rq_schema_key)
                        print(f"{_rq}_{_type}")
                        test_ids_list = cls.extract_rq_test_id(rq_schema_key, test_ids_list)

            else:
                test_ids_list = cls.extract_rq_test_id(rq, test_ids_list)

        for test_id in test_ids_list:
            test_config_path = f"{TEST_CONF_FOLDER}/test_config_{test_id.lower()}.yaml"
            print(f"Validating and parsing TEST CONFIG -> {test_config_path}")
            if not ConfigService.validate_test_config(test_config_path):
                print(f"❌ TEST CONFIG parsing failed.")
                raise RunConfigGenerationError(f"Impossible to generate run_config due to TEST CONFIG errors")
            print(f"✅ TEST CONFIG successfully parsed.")
            test_config = TestConfig.from_dict(
                ConfigService.parse_config_file(test_config_path)
            )
            test_configs.append(test_config)

        run_requirements = []
        run_variations = []

        for test_config in test_configs:
            for _test in test_config.conformance.tests:
                _var_name_list = []
                for _requirement in _test.requirements:
                    if _requirement.name in test.requirements:
                        run_requirements.append(
                            RunRequirement(
                                name=_requirement.name,
                                variations=cls.__get_var_list_for_rq(_requirement.variations, _test.variations)
                            )
                        )
                        for _v in _requirement.variations:
                            if _v not in _var_name_list:
                                _var_name_list.append(_v.lower())
                for _variation in _test.variations:
                    if _variation.name.lower() in _var_name_list or "all" in _var_name_list:
                        run_variations.append(
                            RunVariation(
                                name=_variation.name,
                                mode=ScenarioMode.CAPTURE.value,
                                description=_variation.description,
                                interfaces=_variation.interfaces,
                                params=copy.deepcopy(_variation.params),
                                filtering_options=cls.get_filtering_options(_variation.params, lab_config)
                            )
                        )

        return RunConfig(
            output_folder=launch_config.output_folder,
            global_config=global_config,
            tests=[RunTest(
                name=f"{test.iut.type}_{test.iut.cs_id}",
                requirements=run_requirements,
                variations=run_variations
            )]
        )

    def get_run_config(self) -> RunConfig:
        return self.run_config

    def generate_run_config_file(self, file_format: str, path: str) -> None:
        rc_data = self.run_config.to_dict()

        with open(path, 'w') as file:
            if file_format == 'yaml':
                QuotedStringDumper.add_representer(str, represent_str)
                QuotedStringDumper.add_representer(type(None), represent_none)
                yaml.dump(rc_data, file, Dumper=QuotedStringDumper, sort_keys=False, default_flow_style=False)
            elif file_format == 'json':
                json.dump(rc_data, file, indent=4)
            else:
                raise ValueError("Unsupported file format. Use 'yaml' or 'json'.")

