import json

import yaml
import os
import copy
from typing import Any, Tuple, List, Dict

from .config_enum import FilterMessageType
from .schemas.config_schemas import BASE_CONFIG_SCHEMA
from .errors.wrong_configuration_error import WrongConfigurationError
from ..stub_server.enums import StubServerRole, StubServerProtocol


class QuotedStringDumper(yaml.SafeDumper):
    pass


def represent_str(self, data):
    return self.represent_scalar('tag:yaml.org,2002:str', data, style='"')


def represent_none(self, data):
    return self.represent_scalar('tag:yaml.org,2002:null', '')


class ConfigService:
    _test_config: Dict[str, Any] = {}
    _lab_config: Dict[str, Any] = {}
    _run_config: Dict[str, Any] = {}

    def __init__(self, base_config_file_path: str):
        base_config = self.__load_config_file(base_config_file_path)
        self._test_config = self.__load_config_file(base_config['test_config'])
        self._lab_config = self.__load_config_file(base_config['lab_config'])
        if 'run_config' in base_config.keys():
            self._run_config = self.__load_config_file(base_config['run_config'])
        else:
            raise WrongConfigurationError("Run_config is missing. "
                                          "Be sure to provide in base_config file once generated")

    @classmethod
    def validate(cls, config_file_path: str, output_file: str | None = None) -> bool:
        status, errors = cls.__validate_config_files(config_file_path)
        if status:
            print("Config files Validation Successful")
        else:
            print("Config files Validation Failed")
            if output_file:
                with open(output_file, "w") as file:
                    file.write("\n".join(errors))
                print(f"Errors successfully written to {output_file}")
            else:
                for error in errors:
                    print(error)
        return status

    @classmethod
    def __validate_config_files(cls, config_file_path: str) -> Tuple[bool, List[str]]:
        errors = []
        base_config = cls.__load_config_file(config_file_path)
        status, base_errors = cls.__validate_with_schema(base_config, BASE_CONFIG_SCHEMA)
        errors.extend(base_errors)

        # Nested YAML validations
        if status:
            for key in BASE_CONFIG_SCHEMA.keys():
                nested_path = base_config.get(key, '')
                if nested_path:
                    nested_yaml = cls.__load_config_file(nested_path)
                    if not nested_yaml:
                        errors.append(f"Cannot load or parse YAML for {key} from {nested_path}")
                    else:
                        nested_status, nested_errors = cls.__validate_with_schema(
                            nested_yaml, BASE_CONFIG_SCHEMA.get(key).get("schema")
                        )
                        errors.extend(nested_errors)

        return len(errors) == 0, errors

    @classmethod
    def __validate_with_schema(cls, data: dict, schema: dict, prefix="") -> Tuple[bool, List[str]]:
        errors = []
        for field, rules in schema.items():
            field_name = f"{prefix}{field}"

            if rules.get('required') and field not in data:
                errors.append(f"Missing required field: {field_name}")
                continue

            if field in data:
                expected_type = rules.get('type')
                if not isinstance(data[field], expected_type):
                    errors.append(
                        f"Incorrect type for field '{field_name}'. Expected {expected_type.__name__},"
                        f" got {type(data[field]).__name__}."
                    )

                allowed_values = rules.get('allowed')
                if allowed_values and data[field] not in allowed_values:
                    errors.append(
                        f"Invalid value '{data[field]}' for field '{field_name}'. Allowed values: {allowed_values}."
                    )

                if expected_type == dict and 'schema' in rules:
                    _, nested_errors = cls.__validate_with_schema(
                        data[field], rules['schema'], f"{field_name}."
                    )
                    errors.extend(nested_errors)

                elif expected_type == list and 'schema' in rules:
                    for idx, item in enumerate(data[field]):
                        _, nested_errors = cls.__validate_with_schema(
                            item, rules['schema'], f"{field_name}[{idx}]."
                        )
                        errors.extend(nested_errors)

        return len(errors) == 0, errors

    @classmethod
    def __load_config_file(cls, path: str) -> dict:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, 'r') as f:
            file_format = path.split('.')[-1].lower()
            if file_format == "yaml" or file_format == "yml":
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Error parsing YAML file '{path}': {e}")
            elif file_format == "json":
                try:
                    return json.load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Error parsing YAML file '{path}': {e}")

    @classmethod
    def generate_run_config_file(cls, config_file_path: str, file_format: str = 'yaml',
                                 file_path: str = "run_config.yaml"):
        base_config = cls.__load_config_file(config_file_path)
        test_config = cls.__load_config_file(base_config['test_config'])
        lab_config = cls.__load_config_file(base_config['lab_config'])
        run_config = cls.__generate_run_config_structure(test_config, lab_config)

        file_format = file_format.lower()

        print(file_format)
        print(file_path)

        with open(file_path, 'w') as file:
            if file_format == 'yaml':
                QuotedStringDumper.add_representer(str, represent_str)
                QuotedStringDumper.add_representer(type(None), represent_none)
                yaml.dump(run_config, file, Dumper=QuotedStringDumper, sort_keys=False, default_flow_style=False)
            elif file_format == 'json':
                json.dump(run_config, file, indent=4)
            else:
                raise ValueError("Unsupported file format. Use 'yaml' or 'json'.")

    @staticmethod
    def __get_stimulus_src_interface_name(entities: dict) -> str:
        from_name, to_name = None, None
        for entity in entities:
            if entity['role'] == StubServerRole.SENDER.value:
                from_name = entity['name']
            if entity['role'] == StubServerRole.IUT.value:
                to_name = entity['name']
        if from_name and to_name:
            return f"IF_{from_name}_{to_name}"
        return f""

    @staticmethod
    def __get_output_src_interface_name(entities: dict) -> str:
        from_name, to_name = None, None
        for entity in entities:
            if entity['role'] == StubServerRole.RECEIVER.value:
                from_name = entity['name']
            if entity['role'] == StubServerRole.IUT.value:
                to_name = entity['name']
        if from_name and to_name:
            return f"IF_{to_name}_{from_name}"
        return f""

    @staticmethod
    def __get_dst_interface_name(src_interface_name: str) -> str:
        if_name_splited = src_interface_name.split("_")
        return f"IF_{if_name_splited[2]}_{if_name_splited[1]}"

    @classmethod
    def __get_message_filtering_options(cls, params: dict, lab_config: dict, message_type: str) -> dict:
        """
       "filtering_options": [
                        {
                            "message_type": "",
                            "src_interface": "",
                            "dst_interface": "",
                            "sip_method": "",
                            "http_request_method": "",
                            "response_status_code": "",
                            "header_contains": "",
                            "body_contains": ""
                        }
       """
        message_filtering_options = {}
        entities = lab_config['lab_config']['entities']
        if message_type == FilterMessageType.STIMULUS.value:
            message_filtering_options['message_type'] = FilterMessageType.STIMULUS.value
            scr_if = cls.__get_stimulus_src_interface_name(entities)
            message_filtering_options['src_interface'] = scr_if
            message_filtering_options['dst_interface'] = cls.__get_dst_interface_name(scr_if)
            for message in params['messages']:
                if message['action'] == "send":
                    if message['type'] == StubServerProtocol.SIP.value:
                        message_filtering_options['sip_method'] = message.get('method')
                    if message['type'] == StubServerProtocol.HTTP.value:
                        message_filtering_options['http_request_method'] = message.get('method')
                        message_filtering_options['response_status_code'] = message.get('response_code')
                    message_filtering_options['header_contains'] = message.get('header_contains')
                    message_filtering_options['body_contains'] = message.get('body_contains')

        if message_type == FilterMessageType.OUTPUT.value:
            message_filtering_options['message_type'] = FilterMessageType.OUTPUT.value
            scr_if = cls.__get_output_src_interface_name(entities)
            message_filtering_options['src_interface'] = scr_if
            message_filtering_options['dst_interface'] = cls.__get_dst_interface_name(scr_if)
            for message in params['messages']:
                if message['action'] == "receive":
                    if message['type'] == StubServerProtocol.SIP.value:
                        message_filtering_options['sip_method'] = message.get('method')
                    if message['type'] == StubServerProtocol.HTTP.value:
                        message_filtering_options['http_request_method'] = message.get('method')
                        message_filtering_options['response_status_code'] = message.get('response_code')
                    message_filtering_options['header_contains'] = message.get('header_contains')
                    message_filtering_options['body_contains'] = message.get('body_contains')
        return message_filtering_options

    @classmethod
    def __generate_run_config_structure(cls, test_config: dict, lab_config: dict) -> dict:
        """
            Generate run_config based on provided test_config and lab_config.
            :param test_config: Loaded test configuration.
            :param lab_config: Loaded lab configuration.
            :return: Generated run_config dictionary.
            """
        run_config = {
            "run_config": {
                "global": {
                    "response_timeout": 30,
                    "type": "conformance",
                    "report_files": [
                        {"type": "pdf", "path": "CTR.pdf"},
                        {"type": "docx", "path": "CTR.docx"},
                        {"type": "xml", "path": "CTR.xml"},
                        {"type": "csv", "path": "CTR.csv"},
                        {"type": "json", "path": "CTR.json"}
                    ],
                    "log": {
                        "level": "DEBUG",
                        "output_file": "test_files/logs/logger.log"
                    },
                },
                "tests": []
            }
        }

        tests = test_config.get('test_config', {}).get("conformance", {}).get("tests", [])

        for test in tests:
            test_entry = {
                "name": test.get("name", ""),
                "requirements": [],
                "variations": []
            }

            # Fill requirements
            for req in test.get("requirements", []):
                requirement_entry = {
                    "name": req.get("name", ""),
                    "variations": copy.deepcopy(req.get("variations", []))
                }
                test_entry["requirements"].append(requirement_entry)

            # Fill variations
            for var in test.get("variations", []):
                variation_entry = {
                    "name": var.get("name", ""),
                    "mode": "# pcap/online to be manually filled",  # pcap/online to be manually filled
                    "pcap_file": "# OPTIONAL",  # Optional
                    "params": var.get("params"),
                    "filtering_options": [
                        cls.__get_message_filtering_options(var.get("params"), lab_config,
                                                            FilterMessageType.STIMULUS.value),
                        cls.__get_message_filtering_options(var.get("params"), lab_config,
                                                            FilterMessageType.OUTPUT.value)
                    ]
                }
                test_entry["variations"].append(variation_entry)
            run_config["run_config"]["tests"].append(test_entry)

        return run_config

    def get_test_config(self) -> dict:
        return self._test_config

    def get_lab_config(self) -> dict:
        return self._lab_config

    def get_run_config(self) -> dict:
        return self._run_config
