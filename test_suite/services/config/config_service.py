import json

import yaml
import os
from typing import Any, Tuple, List, Dict

from .schemas.config_schemas import (
    LAUNCH_CONFIG_SCHEMA,
    LAB_CONFIG_SCHEMA,
    LAB_INFO_SCHEMA,
    TEST_INFO_SCHEMA,
    TEST_CONFIG_SCHEMA, RUN_CONFIG_SCHEMA
)
from .errors.wrong_configuration_error import WrongConfigurationError


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
    def parse_config_file(cls, path: str) -> dict:
        return cls.__load_config_file(path)

    @classmethod
    def validate_launch_config(cls, config_file_path: str, output_file: str | None = None) -> bool:
        launch_config = cls.__load_config_file(config_file_path)
        status, errors = cls.__validate_with_schema(launch_config, LAUNCH_CONFIG_SCHEMA)
        if status:
            print("Launch Config file Validation Successful")
        else:
            print("Launch Config file Validation Failed")
            if output_file:
                with open(output_file, "w") as file:
                    file.write("\n".join(errors))
                print(f"Errors successfully written to {output_file}")
            else:
                for error in errors:
                    print(error)
        return status

    @classmethod
    def validate_lab_info(cls, config_file_path: str, output_file: str | None = None) -> bool:
        lab_info = cls.__load_config_file(config_file_path)
        status, errors = cls.__validate_with_schema(lab_info, LAB_INFO_SCHEMA)
        if status:
            print("Lab Info file Validation Successful")
        else:
            print("Lab Info file Validation Failed")
            if output_file:
                with open(output_file, "w") as file:
                    file.write("\n".join(errors))
                print(f"Errors successfully written to {output_file}")
            else:
                for error in errors:
                    print(error)
        return status

    @classmethod
    def validate_lab_config(cls, config_file_path: str, output_file: str | None = None) -> bool:
        lab_info = cls.__load_config_file(config_file_path)
        status, errors = cls.__validate_with_schema(lab_info, LAB_CONFIG_SCHEMA)
        if status:
            print("Lab Config file Validation Successful")
        else:
            print("Lab Config file Validation Failed")
            if output_file:
                with open(output_file, "w") as file:
                    file.write("\n".join(errors))
                print(f"Errors successfully written to {output_file}")
            else:
                for error in errors:
                    print(error)
        return status

    @classmethod
    def validate_test_info(cls, config_file_path: str, output_file: str | None = None) -> bool:
        test_info = cls.__load_config_file(config_file_path)
        status, errors = cls.__validate_with_schema(test_info, TEST_INFO_SCHEMA)
        if status:
            print("Test Info file Validation Successful")
        else:
            print("Test Info file Validation Failed")
            if output_file:
                with open(output_file, "w") as file:
                    file.write("\n".join(errors))
                print(f"Errors successfully written to {output_file}")
            else:
                for error in errors:
                    print(error)
        return status

    @classmethod
    def validate_test_config(cls, config_file_path: str, output_file: str | None = None) -> bool:
        test_config = cls.__load_config_file(config_file_path)
        status, errors = cls.__validate_with_schema(test_config, TEST_CONFIG_SCHEMA)
        if status:
            print("Test Config file Validation Successful")
        else:
            print("Test Config file Validation Failed")
            if output_file:
                with open(output_file, "w") as file:
                    file.write("\n".join(errors))
                print(f"Errors successfully written to {output_file}")
            else:
                for error in errors:
                    print(error)
        return status

    @classmethod
    def validate_run_config(cls, config_file_path: str, output_file: str | None = None) -> bool:
        test_config = cls.__load_config_file(config_file_path)
        status, errors = cls.__validate_with_schema(test_config, RUN_CONFIG_SCHEMA)
        if status:
            print("Run Config file Validation Successful")
        else:
            print("Run Config file Validation Failed")
            if output_file:
                with open(output_file, "w") as file:
                    file.write("\n".join(errors))
                print(f"Errors successfully written to {output_file}")
            else:
                for error in errors:
                    print(error)
        return status

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

    def get_test_config(self) -> dict:
        return self._test_config

    def get_lab_config(self) -> dict:
        return self._lab_config

    def get_run_config(self) -> dict:
        return self._run_config
