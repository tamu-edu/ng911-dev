import yaml
import os
import re

from logger.log_enum import LogLevel
from enums.method_types import SIPMethodEnum, HTTPMethodEnum, HTTPStatusCodeEnum
from enums.packet_types import PacketTypeEnum, TransportProtocolEnum
from logger.logger_service import LoggingMeta
from .config_enum import ScenarioMode, TestId, EntityType
from services.report.report_enums import ReportType


class ConfigService(metaclass=LoggingMeta):
    """
    ConfigService reads, validates, and parses configuration files for the TestSuite.

    TODO
    - ixit configs val  logic
    - use config logic
    - parallel exec logic
    - subtests logic
    - create Config types classes

    """
    test_config: dict
    lab_config: dict

    def __init__(self, base_config_file_path: str):
        self.load_config(base_config_file_path)

    def load_config(self, base_config_file_path: str):
        """
        Load and parse the YAML files for ConfigService instance.
        """
        base_config = self.__load_file(base_config_file_path)
        self.test_config = self.__load_file(
            self.__extract_field_from_config("test_config", base_config)
        )
        self.lab_config = self.__load_file(
            self.__extract_field_from_config("lab_config", base_config)
        )

        self.load_ixit_configs(base_config)

    def load_ixit_configs(self, base_config):
        pass

    def get_test_config(self) -> dict:
        """
        Get the test config
        :return: test_config as a dict
        """
        return self.test_config

    def get_lab_config(self) -> dict:
        """
        Get the lab config
        :return: lab_config as a dict
        """
        return self.lab_config

    @classmethod
    def __validate_file_exists(cls, file_path) -> tuple[bool, list[str]]:
        """
        Loads and validates the configuration file exists without creating an instance.
        :returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        if not os.path.exists(file_path):
            return False, [f"File not found: {file_path}", ]
        else:
            return True, []

    @classmethod
    def __validate_config_file_exists(cls, config_file_path) -> tuple[bool, list[str]] | tuple[bool, dict]:
        """
        Loads and validates the configuration file exists without creating an instance.
        :returns:
            (bool, list): Tuple of validity status and a list of error messages.
            (bool, dict): Tuple of validity status and loaded yaml file to dict for further validation.
        """
        if not os.path.exists(config_file_path):
            return False, [f"Configuration file not found: {config_file_path}", ]

        with open(config_file_path, "r") as file:
            try:
                return True, yaml.safe_load(file)
            except yaml.YAMLError as e:
                return False, [f"Error parsing YAML file: {e}", ]

    @classmethod
    def validate(cls, config_file_path: str, output_file: str | None = None) -> bool:
        """
        Public method to validate config file without creating an instance of ConfigService.
        :returns: None
        """
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
    def __validate_config_files(cls, config_file_path) -> tuple[bool, list[str]]:
        """
        Loads and validates the configuration files without creating an instance.
        :returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        status, result = cls.__validate_config_file_exists(config_file_path)
        if status:
            return cls.__validate_base_config(result)
        else:
            return status, result

    @classmethod
    def __validate_base_config(cls, config) -> tuple[bool, list[str]]:
        """
        Validates the given basic configuration.

        Returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        errors = []

        # Example validation checks
        if not isinstance(config, dict):
            errors.append("Configuration should be a dictionary.")
        else:
            # validate test config file
            if 'test_config' not in config:
                errors.append("Missing 'test_config' value.")
            else:
                status, result = cls.__validate_config_file_exists(
                    cls.__extract_field_from_config("test_config", config)
                )
                if status:
                    status, tc_errors = cls.__validate_test_config(result)
                    if not status:
                        errors.extend(tc_errors)
                else:
                    errors.extend(result)

            # validate lab config file
            if 'lab_config' not in config:
                errors.append("Missing 'lab_config' value.")
            else:
                status, result = cls.__validate_config_file_exists(
                    cls.__extract_field_from_config("lab_config", config)
                )
                if status:
                    status, tc_errors = cls.__validate_lab_config(result)
                    if not status:
                        errors.extend(tc_errors)
                else:
                    errors.extend(result)

        return len(errors) == 0, errors

    @classmethod
    def __validate_test_config(cls, config) -> tuple[bool, list[str]]:
        """
        Validates the given test configuration.

        Returns:
            (bool, list): TTuple of validity status and a list of error messages.
        """
        errors = []
        if not isinstance(config, dict):
            errors.append("Configuration should be a dictionary.")

        #  Main key check
        if 'test_config' not in config:
            errors.append("Missing 'test_config' value. Check your configuration structure.")
        else:
            test_config = config.get('test_config')

            if 'conformance' not in test_config:
                errors.append("Missing 'conformance' value. Check your configuration structure.")
            else:
                g_status, g_errors = cls.__validate_conformance_block(test_config.get('conformance'))
                if not g_status:
                    errors.extend(g_errors)

        return len(errors) == 0, errors

    @classmethod
    def __validate_conformance_block(cls, conformance_block: dict) -> tuple[bool, list[str]]:
        """
        Validates the given report block of test configuration.

        Returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        errors = []

        if 'tests' not in conformance_block:
            errors.append("Missing 'tests' value in 'conformance' block. Check your configuration structure.")
        else:
            tests = conformance_block.get('tests')
            if not isinstance(tests, list):
                errors.append("'Tests' in 'conformance' block should be a list.")
            else:
                for test in tests:
                    if not isinstance(test, dict):
                        errors.append("Each 'test' in 'conformance.tests' block should dictionaries.")
                    else:
                        if 'name' not in test:
                            errors.append("Missing 'name' value in 'test' element.")


        return len(errors) == 0, errors

    @classmethod
    def __validate_run_config(cls, config) -> tuple[bool, list[str]]:
        """
        Validates the given test configuration.

        Returns:
            (bool, list): TTuple of validity status and a list of error messages.
        """
        errors = []
        if not isinstance(config, dict):
            errors.append("Configuration should be a dictionary.")

        #  Main key check
        if 'run_config' not in config:
            errors.append("Missing 'run_config' value. Check your configuration structure.")
        else:
            run_config = config.get('run_config')

            #  Blocks validation
            if 'global' not in run_config:
                errors.append("Missing 'global' value. Check your configuration structure.")
            else:
                g_status, g_errors = cls.__validate_global_block(run_config.get('global'))
                if not g_status:
                    errors.extend(g_errors)

            if 'report_files' not in run_config:
                errors.append("Missing 'report_files' value. Check your configuration structure.")
            else:
                g_status, g_errors = cls.__validate_report_block(run_config.get('report_files'))
                if not g_status:
                    errors.extend(g_errors)

            if 'log' not in run_config:
                errors.append("Missing 'log' value. Check your configuration structure.")
            else:
                g_status, g_errors = cls.__validate_log_block(run_config.get('log'))
                if not g_status:
                    errors.extend(g_errors)

        return len(errors) == 0, errors

    @classmethod
    def __validate_global_block(cls, global_block: dict) -> tuple[bool, list[str]]:
        """
        Validates the given global block of test configuration.

        Returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        errors = []
        if not isinstance(global_block, dict):
            errors.append("Configuration should be a dictionary.")

        if 'response_timeout' not in global_block:
            errors.append("Missing 'response_timeout' value in 'global' block.")
        else:
            if not isinstance(global_block.get('response_timeout'), int):
                errors.append("'response_timeout' should be an INT")

        return len(errors) == 0, errors

    @classmethod
    def __validate_report_block(cls, report_block: list) -> tuple[bool, list[str]]:
        """
        Validates the given report block of test configuration.

        Returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        errors = []
        if not isinstance(report_block, list):
            errors.append("Configuration should be a List.")
        else:
            if len(report_block) == 0:
                errors.append("Configuration shouldn't be empty")
            r_index = 0
            for report in report_block:
                if 'type' not in report:
                    errors.append(f"Missing 'type' value in {r_index} element of 'report' block.")
                else:
                    report_type = report.get('type')
                    if not isinstance(report_type, str):
                        errors.append(f"Error - 'type' value in {r_index} element of 'report' block should be an STR")
                    else:
                        if report_type not in ReportType.list():
                            errors.append(
                                f"Error - 'type' value in {r_index} element of 'report' block should be one of"
                                f"{ReportType.list()}"
                            )

                if 'path' not in report:
                    errors.append(f"Missing 'path' value in {r_index} element of 'report' block.")
                else:
                    path = report.get('path')
                    if not isinstance(path, str):
                        errors.append(f"Error - 'path' value in {r_index} element of 'report' block should be an STR")
                    else:
                        if len(path) == 0:
                            errors.append(
                                f"Error - 'path' value in {r_index} element of 'report' block should contain a path or"
                                f" a desired filename at least"
                            )
                r_index += 1


        return len(errors) == 0, errors

    @classmethod
    def __validate_log_block(cls, log_block: dict) -> tuple[bool, list[str]]:
        """
        Validates the given report block of test configuration.

        Returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        errors = []
        if not isinstance(log_block, dict):
            errors.append("Configuration should be a dictionary.")

        if 'level' not in log_block:
            errors.append("Missing 'log.level' value in 'log' block.")
        else:
            log_level = log_block.get('level')
            if not isinstance(log_level, str):
                errors.append("'log.level' should be an STR")
            else:
                if log_level not in LogLevel.list():
                    errors.append(f"'log.level' value should be  one of {LogLevel.list()}")

        if 'output_file' not in log_block:
            errors.append("Missing 'output_file' value in 'log' block.")
        else:
            output_file = log_block.get('output_file')
            if not isinstance(output_file, str):
                errors.append("'log.output_file' should be an STR")
            # else:
            #     if len(output_file) == 0:
            #         errors.append("'log.output_file' should contain path to the log file")

        return len(errors) == 0, errors

    @classmethod
    def __validate_stimulus_or_output(cls, message: dict, prefix: str, test_index: int, sc_index: int) -> list:
        errors = []

        if 'src_interface' not in message:
            errors.append(f"Missing 'src_interface' value in {prefix} block of {test_index} element of 'test' block"
                          f"of {sc_index} element of 'scenarios' block.")
        else:
            if not isinstance(message.get('src_interface'), str):
                errors.append(f"Value 'src_interface' in {prefix} block of {test_index} element of 'test' block"
                              f"of {sc_index} element of 'scenarios' block SHOULD be str.")

        if 'dst_interface' not in message:
            errors.append(f"Missing 'dst_interface' value in {prefix} block of {test_index} element of 'test' block"
                          f"of {sc_index} element of 'scenarios' block.")
        else:
            if not isinstance(message.get('dst_interface'), str):
                errors.append(f"Value 'dst_interface' in {prefix} block of {test_index} element of 'test' block"
                              f"of {sc_index} element of 'scenarios' block SHOULD be str.")

        if 'sip_method' not in message:
            errors.append(f"Missing 'sip_method' value in {prefix} block of {test_index} element of 'test' block"
                          f"of {sc_index} element of 'scenarios' block.")
        else:
            if not isinstance(message.get('sip_method'), str):
                errors.append(f"Value 'sip_method' in {prefix} block of {test_index} element of 'test' block"
                              f"of {sc_index} element of 'scenarios' block SHOULD be str.")
            else:
                if len(message.get('sip_method')) > 0:
                    if message.get('sip_method') not in SIPMethodEnum.list():
                        errors.append(f"Value 'sip_method' in {prefix} block of {test_index} element of 'test' block "
                                      f"of {sc_index} element of 'scenarios' block SHOULD "
                                      f"be one of {SIPMethodEnum.list()}")

        if 'http_request_method' not in message:
            errors.append(f"Missing 'http_request_method' value in {prefix} block of {test_index} element of 'test'"
                          f"block of {sc_index} element of 'scenarios' block.")
        else:
            if not isinstance(message.get('http_request_method'), str):
                errors.append(f"Value 'http_request_method' in {prefix} block of {test_index} element of 'test' block"
                              f"of {sc_index} element of 'scenarios' block SHOULD be str.")
            else:
                if len(message.get('http_request_method')) > 0:
                    if message.get('http_request_method') not in HTTPMethodEnum.list():
                        errors.append(
                            f"Value 'http_request_method' in {prefix} block of {test_index} element of 'test' "
                            f"block of {sc_index} element of 'scenarios' block SHOULD "
                            f"be one of {HTTPMethodEnum.list()}")

        if 'response_status_code' not in message:
            errors.append(f"Missing 'response_status_code' value in {prefix} block of {test_index} element of 'test'"
                          f"block of {sc_index} element of 'scenarios' block.")
        else:
            if not isinstance(message.get('response_status_code'), str):
                errors.append(
                    f"Value 'response_status_code' in {prefix} block of {test_index} element of 'test' block"
                    f"of {sc_index} element of 'scenarios' block SHOULD be str.")
            else:
                if len(message.get('response_status_code')) > 0:
                    if int(message.get('response_status_code')) not in HTTPStatusCodeEnum.list():
                        errors.append(f"Value 'response_status_code' in {prefix} block of {test_index} element of "
                                      f" 'test' block of {sc_index} element of 'scenarios' block "
                                      f"SHOULD be one of {HTTPStatusCodeEnum.list()}")

        return errors

    @classmethod
    def __validate_scenarios_block(cls, scenarios_block: dict) -> tuple[bool, list[str]]:
        """
        Validates the given report block of test configuration.

        Returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        errors = []
        if not isinstance(scenarios_block, list):
            errors.append("Scenarios Configuration should be a list of dictionaries.")
        else:
            sc_index = 0
            for scenario in scenarios_block:
                if not isinstance(scenario, dict):
                    errors.append("Scenarios should be dictionaries.")

                if 'name' not in scenario:
                    errors.append(f"Missing 'name' value in {sc_index} element of 'scenarios' block.")
                else:
                    if not isinstance(scenario.get('name'), str):
                        errors.append(f"Value 'name' in {sc_index} element of 'scenarios' block should be a STR.")

                if 'mode' not in scenario:
                    errors.append(f"Missing 'mode' value in {sc_index} element of 'scenarios' block.")
                else:
                    if not isinstance(scenario.get('mode'), str):
                        errors.append(f"Value 'mode' in {sc_index} element of 'scenarios' block should be a STR.")
                    else:
                        if scenario.get('mode') not in ScenarioMode.list():
                            errors.append(f"Value 'mode' in {sc_index} element of 'scenarios' block "
                                          f"should be one of {ScenarioMode.list()}")
                        if scenario.get('mode') == ScenarioMode.PCAP:
                            if 'pcap_file' not in scenario:
                                errors.append(f"Missing 'pcap_file' value in {sc_index} element of 'scenarios' block.")
                            else:
                                if not isinstance(scenario.get('pcap_file'), str):
                                    errors.append(
                                        f"Value 'pcap_file' in {sc_index} element of 'scenarios' block "
                                        f"should be a STR.")
                                else:
                                    status, result = cls.__validate_file_exists(scenario.get('pcap_file'))
                                    if not status:
                                        errors.extend(result)
                        elif scenario.get('mode') == ScenarioMode.CAPTURE:
                            if 'stimulus_body' not in scenario:
                                errors.append(f"Missing 'stimulus_body' value in {sc_index} element of 'scenarios' block.")
                            else:
                                if not isinstance(scenario.get('stimulus_body'), str):
                                    errors.append(f"Value 'stimulus_body' in {sc_index} element of 'scenarios' block "
                                                  f"should be a STR.")
                                else:
                                    status, result = cls.__validate_file_exists(scenario.get('stimulus_body'))
                                    if not status:
                                        errors.extend(result)

                if 'tests' not in scenario:
                    errors.append(f"Missing 'tests' value in {sc_index} element of 'scenarios' block.")
                else:
                    tests = scenario.get('tests')
                    if not isinstance(tests, list):
                        errors.append(f"Value 'tests' in {sc_index} element of 'scenarios'"
                                      f" block should be a list.")
                    test_index = 0
                    for test in tests:
                        if not isinstance(test, dict):
                            errors.append(f"Tests int 'tests' list in {sc_index} element of 'scenarios' block "
                                          f"should be dictionaries.")
                        else:
                            if 'name' not in test:
                                errors.append(f"Missing 'name' value in {test_index} element of 'test' block"
                                              f"of {sc_index} element of 'scenarios' block.")
                            else:
                                if not isinstance(test.get('name'), str):
                                    errors.append(f"Value 'name' in {test_index} element of 'test' block"
                                                  f"of {sc_index} element of 'scenarios' block SHOULD be str.")

                            if 'test_id' not in test:
                                errors.append(f"Missing 'test_id' value in {test_index} element of 'test' block"
                                              f"of {sc_index} element of 'scenarios' block.")
                            else:
                                if not isinstance(test.get('test_id'), str):
                                    errors.append(f"Value 'test_id' in {test_index} element of 'test' block"
                                                  f"of {sc_index} element of 'scenarios' block SHOULD be str.")
                                else:
                                    if test.get('test_id') not in TestId.list():
                                        errors.append(f"Value 'test_id' in {sc_index} element of 'scenarios' block "
                                                      f"should be an exact name of required Test module")

                            if 'ixit_file_path' not in test:
                                errors.append(f"Missing 'ixit_file_path' value in {test_index} element of 'test' block"
                                              f"of {sc_index} element of 'scenarios' block.")
                            else:
                                if not isinstance(test.get('ixit_file_path'), str):
                                    errors.append(f"Value 'ixit_file_path' in {test_index} element of 'test' block"
                                                  f"of {sc_index} element of 'scenarios' block SHOULD be str.")
                                if len(test.get('ixit_file_path')) > 0:
                                    status, result = cls.__validate_file_exists(test.get('ixit_file_path'))
                                    if not status:
                                        errors.extend(result)

                            if 'stimulus_message' not in test:
                                errors.append(f"Missing 'stimulus_message' value in {test_index} element of 'test' block"
                                              f"of {sc_index} element of 'scenarios' block.")
                            else:
                                if not isinstance(test.get('stimulus_message'), dict):
                                    errors.append(f"Value 'stimulus_message' in {test_index} element of 'test' block"
                                                  f"of {sc_index} element of 'scenarios' block SHOULD be dictionary.")
                                message = test.get('stimulus_message')
                                errors.extend(cls.__validate_stimulus_or_output(
                                    message, "stimulus_message", test_index, sc_index
                                ))


                        test_index = test_index + 1
                sc_index = sc_index + 1

        return len(errors) == 0, errors

    @classmethod
    def __validate_entities_block(cls, entities_block: dict) -> tuple[bool, list[str]]:
        """
        Validates the given entities block of lab configuration.

        Returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        errors = []
        if not isinstance(entities_block, list):
            errors.append("Configuration should be a list.")
        else:
            entity_index = 0
            for entity in entities_block:
                if not isinstance(entity, dict):
                    errors.append("Each 'entity' block should be a list.")
                else:
                    if 'name' not in entity:
                        errors.append(f"Missing 'name' value in {entity_index} 'entity' block.")
                    else:
                        name = entity.get('name')
                        if not isinstance(name, str):
                            errors.append(f"'entities.name' of {entity_index} 'entity' block should be an STR")

                    if 'type' not in entity:
                        errors.append(f"Missing 'type' value in {entity_index} 'entity' block.")
                    else:
                        ent_type = entity.get('type')
                        if not isinstance(ent_type, str):
                            errors.append(f"'entities.type' of {entity_index} 'entity' block should be an STR")
                        else:
                            if ent_type not in EntityType.list():
                                errors.append(f"'entities.type' of {entity_index} 'entity' block"
                                              f" should be one of {EntityType.list()}")

                    if 'fqdn' not in entity:
                        errors.append(f"Missing 'fqdn' value in {entity_index} 'entity' block.")
                    else:
                        fqdn = entity.get('fqdn')
                        if not isinstance(fqdn, str):
                            errors.append(f"'entities.fqdn' of {entity_index} 'entity' should be an STR")
                        else:
                            if len(fqdn) > 0 and not cls.is_valid_fqdn(fqdn):
                                errors.append(f"'entities.fqdn' of {entity_index} 'entity' block"
                                              f" wrong format. Check possible FQDN formats.")

                    # if 'mac_address' not in entity:
                    #     errors.append(f"Missing 'mac_address' value in {entity_index} 'entity' block.")
                    # else:
                    #     mac_address = entity.get('mac_address')
                    #     if not isinstance(mac_address, str):
                    #         errors.append(f"'entities.mac_address' of {entity_index} 'entity' block should be an STR")
                    #     else:
                    #         if not cls.is_valid_mac(mac_address):
                    #             errors.append(f"'entities.mac_address' of {entity_index} 'entity' block"
                    #                           f" wrong format. Check possible MAC address formats.")

                    if 'certificate_file' not in entity:
                        errors.append(f"Missing 'certificate_file' value in {entity_index} 'entity' block.")
                    else:
                        certificate_file = entity.get('certificate_file')
                        if not isinstance(certificate_file, str):
                            errors.append(f"'entities.certificate_file' of {entity_index} 'entity' block"
                                          f" should be an STR")
                        else:
                            status, f_errors = cls.__validate_file_exists(certificate_file)
                            if len(certificate_file) > 0 and not status:
                                errors.append(f"'entities.certificate_file' of {entity_index} 'entity' block")
                                errors.extend(f_errors)

                    if 'certificate_key' not in entity:
                        errors.append(f"Missing 'certificate_key' value in {entity_index} 'entity' block.")
                    else:
                        certificate_key = entity.get('certificate_key')
                        if not isinstance(certificate_key, str):
                            errors.append(f"'entities.certificate_key' of {entity_index} 'entity' block"
                                          f" should be an STR")
                        else:
                            status, f_errors = cls.__validate_file_exists(certificate_key)
                            if len(certificate_key) > 0 and not status:
                                errors.append(f"'entities.certificate_key'of {entity_index} 'entity' block")
                                errors.extend(f_errors)

                    if 'interfaces' not in entity:
                        errors.append(f"Missing 'interfaces' value in {entity_index} 'entity' block.")
                    else:
                        interfaces = entity.get('interfaces')
                        if not isinstance(interfaces, list):
                            errors.append(f"'entities.certificate_key' of {entity_index} 'entity' block"
                                          f" should be an LIST")
                        else:
                            interface_index = 0
                            for interface in interfaces:
                                if 'name' not in interface:
                                    errors.append(f"Missing 'name' value in {interface_index} 'interface' block"
                                                  f"of {entity_index} 'entity' block.")
                                else:
                                    name = interface.get('name')
                                    if not isinstance(name, str):
                                        errors.append(f"'name' of {interface_index} 'interface' block"
                                                      f"of {entity_index} 'entity' block"
                                                      f" should be an STR")

                                if 'fqdn' not in interface:
                                    errors.append(f"Missing 'fqdn' value in {interface_index} 'interface' block"
                                                  f"of {entity_index} 'entity' block.")
                                else:
                                    fqdn = interface.get('fqdn')
                                    if not isinstance(fqdn, str):
                                        errors.append(f"'interface.fqdn' value in {interface_index} 'interface' block"
                                                      f"of {entity_index} 'entity' block should be an STR")
                                    else:
                                        if len(fqdn) > 0 and not cls.is_valid_fqdn(fqdn):
                                            errors.append(f"'interface.fqdn' value in {interface_index} 'interface' block"
                                                          f"of {entity_index} 'entity' block wrong format. "
                                                          f"Check possible FQDN formats.")

                                if 'ip' not in interface:
                                    errors.append(f"Missing 'ip' value in {interfaces} 'interface' block"
                                                  f"of {entity_index} 'entity' block.")
                                else:
                                    ip = interface.get('ip')
                                    if not isinstance(ip, str):
                                        errors.append(f"'ip' of {interface_index} 'interface' block"
                                                      f"of {entity_index} 'entity' block"
                                                      f" should be an STR")
                                    else:
                                        if not cls.is_valid_ip(ip):
                                            errors.append(f"'ip' of {interface_index} 'interface' block"
                                                          f"of {entity_index} 'entity' block"
                                                          f" should be correct format of IP address")

                                if 'mask' not in interface:
                                    errors.append(f"Missing 'mask' value in {interface_index} 'interface' block"
                                                  f"of {entity_index} 'entity' block.")
                                else:
                                    mask = interface.get('mask')
                                    if not isinstance(mask, str):
                                        errors.append(f"'mask' of {interface_index} 'interface' block"
                                                      f"of {entity_index} 'entity' block"
                                                      f" should be an STR")
                                    else:
                                        if len(mask) > 0 and not cls.is_valid_subnet_mask(mask):
                                            errors.append(f"'mask' of {interface_index} 'interface' block"
                                                          f"of {entity_index} 'entity' block"
                                                          f" should be correct format of Subnet mask")

                                if 'gateway' not in interface:
                                    errors.append(f"Missing 'gateway' value in {interface_index} 'interface' block"
                                                  f"of {entity_index} 'entity' block.")
                                else:
                                    gateway = interface.get('gateway')
                                    if not isinstance(gateway, str):
                                        errors.append(f"'gateway' of {interface_index} 'interface' block"
                                                      f"of {entity_index} 'entity' block"
                                                      f" should be an STR")
                                    else:
                                        if len(gateway) > 0 and not cls.is_valid_ip(gateway):
                                            errors.append(f"'gateway' of {interface_index} 'interface' block"
                                                          f"of {entity_index} 'entity' block"
                                                          f" should be correct format of IP address")

                                if 'dns' not in interface:
                                    errors.append(f"Missing 'dns' value in {interface_index} 'interface' block"
                                                  f"of {entity_index} 'entity' block.")
                                else:
                                    dns = interface.get('dns')
                                    if not isinstance(dns, list):
                                        errors.append(f"'dns' of {interface_index} 'interface' block"
                                                      f"of {entity_index} 'entity' block"
                                                      f" should be an LIST of strings")
                                    else:
                                        for dns_item in dns:
                                            if not isinstance(dns_item, str):
                                                errors.append(f"each 'dns' item in 'dns' list "
                                                              f"of {interface_index} 'interface' block "
                                                              f"of {entity_index} 'entity' block"
                                                              f" should be a string")
                                            else:
                                                if not cls.is_valid_ip(dns_item):
                                                    errors.append(f"each 'dns' item in 'dns' list "
                                                                  f"of {interface_index} 'interface' block "
                                                                  f"of {entity_index} 'entity' block"
                                                                  f" should be correct format of IP address")

                                if 'port_mapping' not in interface:
                                    errors.append(f"Missing 'port_mapping' value in {interface_index} 'interface' block"
                                                  f"of {entity_index} 'entity' block.")
                                else:
                                    port_mapping = interface.get('port_mapping')
                                    if not isinstance(port_mapping, list):
                                        errors.append(f"'port_mapping' of {interface_index} 'interface' block"
                                                      f"of {entity_index} 'entity' block"
                                                      f" should be an lIST")
                                    else:
                                        protocol_index = 0
                                        for entry in port_mapping:
                                            if not isinstance(entry, dict):
                                                errors.append(f"'{protocol_index} entry in 'port_mapping' list "
                                                              f"of {interface_index} 'interface' block"
                                                              f"of {entity_index} 'entity' block"
                                                              f" should be an dict")
                                            else:
                                                if "protocol" not in entry:
                                                    errors.append(
                                                        f"Missing 'protocol' value in '{protocol_index} entry in "
                                                        f"'port_mapping' list of {interface_index} 'interface' block"
                                                        f"of {entity_index} 'entity' block.")
                                                else:
                                                    if entry.get("protocol") not in PacketTypeEnum.list() and \
                                                            entry.get("protocol") not in TransportProtocolEnum.list():
                                                        errors.append(f"'protocol' value in {protocol_index} entry of "
                                                                      f"'port_mapping' list "
                                                                      f"of {interface_index} 'interface' block"
                                                                      f"of {entity_index} 'entity' block"
                                                                      f" should be one of {PacketTypeEnum.list()}"
                                                                      f" or one of {TransportProtocolEnum.list()}")

                                                if "port" not in entry:
                                                    errors.append(
                                                        f"Missing 'port' value in '{protocol_index} entry in "
                                                        f"'port_mapping' list of {interface_index} 'interface' block"
                                                        f"of {entity_index} 'entity' block.")
                                                else:
                                                    if not isinstance(entry.get("port"), int) or \
                                                            entry.get("port") < 0 or entry.get("port") > 65535:
                                                        errors.append(f"'port' value in '{protocol_index} entry in "
                                                                      f"'port_mapping' list of {interface_index} "
                                                                      f"'interface' block"
                                                                      f" of {entity_index} 'entity' block"
                                                                      f"should be an int between 0 and 65535.")

                                # if 'transport' not in interface:
                                #     errors.append(f"Missing 'transport' value in {interfaces} 'interface' block"
                                #                   f"of {entity_index} 'entity' block.")
                                # else:
                                #     protocols = interface.get('transport')
                                #     if not isinstance(protocols, list):
                                #         errors.append(f"'transport' of {interfaces} 'interface' block"
                                #                       f"of {entity_index} 'entity' block"
                                #                       f" should be an lIST")
                                #     else:
                                #         protocol_index = 0
                                #         for protocol in protocols:
                                #             if not isinstance(protocol, str):
                                #                 errors.append(f"'{protocol_index} position in 'transport' list "
                                #                               f"of {interfaces} 'interface' block"
                                #                               f"of {entity_index} 'entity' block"
                                #                               f" should be an STR")
                                #             else:
                                #                 if protocol not in TransportProtocolEnum.list():
                                #                     errors.append(f"'{protocol_index} position in 'transport' list "
                                #                                   f"of {interfaces} 'interface' block"
                                #                                   f"of {entity_index} 'entity' block"
                                #                                   f" should be one of {TransportProtocolEnum.list()}")

                                interface_index = interface_index + 1
                entity_index = entity_index + 1

        return len(errors) == 0, errors

    @classmethod
    def __validate_lab_config(cls, config) -> tuple[bool, list[str]]:
        """
        Validates the given lab configuration.

        Returns:
            (bool, list): Tuple of validity status and a list of error messages.
        """
        errors = []
        if not isinstance(config, dict):
            errors.append("Configuration should be a dictionary.")

        #  Main key check
        if 'lab_config' not in config:
            errors.append("Missing 'lab_config' value. Check your configuration structure.")
        else:
            lab_config = config.get('lab_config')

            #  Blocks validation
            if 'entities' not in lab_config:
                errors.append("Missing 'entities' value. Check your configuration structure.")
            else:
                g_status, g_errors = cls.__validate_entities_block(lab_config.get('entities'))
                if not g_status:
                    errors.extend(g_errors)

        return len(errors) == 0, errors

    @staticmethod
    def __extract_field_from_config(field_name, config_data):
        if field_name not in config_data:
            raise ValueError(f"Missing {field_name} section in configuration file.")
        else:
            return config_data.get(field_name)

    @staticmethod
    def __load_file(path: str) -> dict:
        """
        Load and parse the YAML configuration file.
        :raises: FileNotFoundError, yaml.YAMLError
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r") as file:
            try:
                return yaml.safe_load(file)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file: {e}")

    @staticmethod
    def is_valid_fqdn(fqdn: str) -> bool:
        """
        Validate the format of an FQDN.

        Args:
            fqdn (str): The FQDN string to validate.

        Returns:
            bool: True if the FQDN is valid, False otherwise.
        """
        fqdn_regex = (
            r'^(?=.{1,253}$)'  # Total length of FQDN (1-253 characters)
            r'(([a-zA-Z0-9]{1,63})'  # First label: alphanumeric (1-63 chars)
            r'(-[a-zA-Z0-9]{1,62})?'  # Optional: hyphen followed by alphanumerics
            r'\.)+'  # Each label ends with a dot (.)
            r'[a-zA-Z]{2,}$'  # Ends with a valid TLD (min 2 letters)
        )
        return bool(re.match(fqdn_regex, fqdn))

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """
        Validate an IP address.
        :param ip: str
        :return: bool
        """
        ip_regex = re.compile(
            r'^((25[0-5]|2[0-4][0-9]|1[0-9]{1,2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{1,2}|[1-9]?[0-9])$'
        )
        return bool(ip_regex.match(ip))

    @staticmethod
    def is_valid_subnet_mask(mask: str) -> bool:
        """
        Validate the format of a subnet mask.

        Args:
            mask (str): The subnet mask to validate.

        Returns:
            bool: True if the subnet mask is valid, False otherwise.
        """
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

    @staticmethod
    def is_valid_mac(mac_address: str) -> bool:
        """
        Validate the format of a MAC address.

        Args:
            mac_address (str): The MAC address string to validate.

        Returns:
            bool: True if the MAC address is valid, False otherwise.
        """
        mac_regex = (
            r'^([0-9A-Fa-f]{2}[:-]){5}'  # First 5 pairs of hexadecimal digits with : or -
            r'([0-9A-Fa-f]{2})$'  # Last pair of hexadecimal digits
        )
        return bool(re.match(mac_regex, mac_address))
