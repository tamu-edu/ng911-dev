import inspect
import json

import yaml
import os
from . import extra_checks as checks
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
    def _if_required_has_exception(cls, field: str, data: dict) -> bool:
        if data.get("action") == "manual" and field in ["type", "method"]:  # add other NOT REQUIRED FOR MANUAL
            return True
        return False

    @classmethod
    def __validate_with_schema(cls, data: dict, schema: dict, prefix="") -> Tuple[bool, List[str]]:
        errors = []
        for field, rules in schema.items():
            field_name = f"{prefix}{field}"

            if rules.get('required') and field not in data:
                if not cls._if_required_has_exception(field, data):
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
                if isinstance(data[field], list) and allowed_values:
                    invalid = [item for item in data[field] if item not in allowed_values]
                    if invalid:
                        errors.append(
                            f"Invalid values [{invalid}], for field '{field_name}'. Allowed values: {allowed_values}."
                        )
                else:
                    if allowed_values and data[field] not in allowed_values:
                        errors.append(
                            f"Invalid value '{data[field]}' for field '{field_name}'. Allowed values: {allowed_values}."
                        )

                extra_checks = rules.get('extra_checks', [])

                for extra_check in extra_checks:
                    if hasattr(checks, extra_check):
                        if not rules.get('required') and not data[field]:
                            continue
                        ec = getattr(checks, extra_check)

                        kwargs = {
                            "field_name": field_name,
                            "field_value": data[field]
                        }

                        signature = inspect.signature(ec)

                        # TODO MAYBE we need more elegant solution or create smth like ExtraValidator class
                        for arg in signature.parameters.keys():
                            if arg not in kwargs.keys():
                                if arg == "data_dict":
                                    kwargs[arg] = data

                        is_validated, error = ec(**kwargs)

                        if not is_validated:
                            errors.append(error)

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
            content = f.read().strip()
            if not content:
                raise ValueError(f"Error parsing '{path}': file is empty")
            config_data = None
            errors = []
            try:
                config_data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                errors.append(f"❌ YAML parsing error: {e}")
            if not config_data:
                try:
                    config_data = json.loads(content)
                except json.JSONDecodeError as e:
                    errors.append(f"❌ JSON parsing error: {e}")
            if not config_data:
                raise ValueError(f"Error parsing file '{path}':\n" + "\n".join(str(e) for e in errors))
            return config_data

    def get_test_config(self) -> dict:
        return self._test_config

    def get_lab_config(self) -> dict:
        return self._lab_config

    def get_run_config(self) -> dict:
        return self._run_config
