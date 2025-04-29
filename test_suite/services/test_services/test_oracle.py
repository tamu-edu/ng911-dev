import asyncio
import gc
import multiprocessing
import shutil
import sys
import os
import importlib
import time
import services.prep_services as prep_services
from collections import defaultdict
from multiprocessing import Manager
from dataclasses import field
from typing import List
from services.config.config_enum import ScenarioMode
from services.config.types.lab_config import LabConfig, PortMapping, Entity, Interface
from services.docker.docker_service import DockerService
from services.monitoring_service import MonitoringService
from services.pcap_service import PcapCaptureService
from services.config.types.test_config import TestConfig
from services.config.types.run_config import RunConfig, RunVariation, RunTest
from services.config.schemas.requirements_schema import REQUIREMENTS_SCHEMA
from logger.logger_service import LoggingMeta
from services.stub_server.enums import StubServerProtocol, StubServerRole
from services.test_services.test_conduction_service import TestConductionService
from services.test_services.types.test_types import OracleTestScenario
from services.test_services.types.test_verdict import VerdictType
from services.stub_server.stub_server_service import StubServerService
from services.config.config_enum import EntityMode
from services.aux.aux_services import get_entity_protocol

# Including our tests modules which are in a folder named "tests" to sys.path
module_directory = os.path.abspath("tests")
if module_directory not in sys.path:
    sys.path.append(module_directory)


class TestOracle(metaclass=LoggingMeta):
    """
    TestOracle service is a class to conduct tests using provided configs
    """
    _test_config: TestConfig
    _lab_config: LabConfig
    scenarios: List[OracleTestScenario] = []
    general_verdict: VerdictType

    def __init__(self, test_config: TestConfig, lab_config: LabConfig, run_config: RunConfig):
        self._test_config = test_config
        self._lab_config = lab_config
        self._run_config = run_config
        self.tests = []
        self.captured_files = []
        self.__prepare_scenarios()

    @staticmethod
    def __get_test_id_from_req(req: str) -> [str, list]:
        """
        Get test id from REQUIREMENTS_SCHEMA by REQ name
        :param req: str
        :return: test_id as str
        """
        if req in REQUIREMENTS_SCHEMA.keys():
            return [REQUIREMENTS_SCHEMA.get(req).get("test_id"), REQUIREMENTS_SCHEMA.get(req).get("subtests")]

    @staticmethod
    def __optimize_test_list_for_variation(test_list: list) -> list:
        """
        Removes duplicates in test_list by test_id and merge subtests.
        :param test_list:
        :return: list
        """
        result = defaultdict(set)
        use_all_subtests = set()

        for test in test_list:
            test_id = test["test_id"]
            subtests = test["subtests"]

            if not subtests:
                # Indicates using all subtests, so clear and mark this test_id accordingly
                use_all_subtests.add(test_id)
                result[test_id] = set()  # Empty set as indicator
                continue

            # If test_id already marked as using all subtests, skip merging
            if test_id in use_all_subtests:
                continue

            result[test_id].update(subtests)

        # Convert sets back to sorted lists
        return [
            {"test_id": test_id, "subtests": [] if test_id in use_all_subtests else sorted(subtests)}
            for test_id, subtests in result.items()
        ]

    def __generate_test_list_for_variation(self, reqs: list, variation: str) -> list:
        result = []
        for req in reqs:
            normalized_variations = [v.lower() for v in req.variations]
            if variation.lower() in normalized_variations or "all" in normalized_variations:
                test_data = self.__get_test_id_from_req(req.name)
                if test_data:
                    test_id, subtests = test_data
                    result.append({"test_id": test_id, "subtests": subtests})
        return result

    def __finalize_test_list_for_variation(self, test_list: list, pcap_service: PcapCaptureService,
                                           variation: RunVariation) -> list:
        """
        Wraps test_list in TestConductionService
        """
        return [
            TestConductionService(
                name=f"{variation.name}_{test.get('test_id').split('_', 1)[0]}",
                tests_list=importlib.import_module(test.get("test_id")).get_test_list(
                    pcap_service, self._lab_config, variation.filtering_options, variation
                ),
                subtests_list=test.get("subtests")
            )
            for test in test_list
        ]

    def _generate_capture_filter_from_config(self):
        unique_ips = set()

        for entity in self._lab_config.entities:
            for interface in entity.interfaces:
                if interface.ip:
                    unique_ips.add(interface.ip)

        # Build the capture filter string
        return " or ".join(f"host {ip}" for ip in sorted(unique_ips))

    @staticmethod
    def _get_action_type(entity_role: str) -> str:
        if entity_role == StubServerRole.SENDER.value:
            return "send"
        if entity_role == StubServerRole.RECEIVER.value:
            return "receive"

    @staticmethod
    def _get_ss_role_by_action_type(action_type: str) -> str:
        if action_type == "send":
            return StubServerRole.SENDER.value
        if action_type == "receive":
            return StubServerRole.RECEIVER.value

    @staticmethod
    def _check_value_for_file_var_mode(value: str):
        if value is None:
            return None, False
        value_split = value.split(".")
        if value_split[0] == "file":
            # if not os.path.exists(value_split[1]):
            #     raise FileNotFoundError(f"File not found: {value_split[1]}")
            result = value_split[1]
            for item in value_split[2:]:
                result += f".{item}"
            return result, True
        elif value_split[0] == "var":
            return value_split[1], False
        else:
            result = value_split[0]
            for item in value_split[1:]:
                result += f".{item}"
            return result, False

    def _get_manual_actions(self, variation: RunVariation) -> list:
        manual_actions = []
        for message in variation.params["messages"]:
            if message['action'] == "manual":
                manual_actions.append(message)
        return manual_actions

    def _prepare_action_data_for_ss_launch(self, variation: RunVariation, entity_role: str,
                                           next_action_id: str | None = "") -> dict:
        action_data = {}
        # TODO can it be that the STIMULUS would be HTTP and be started without scenario
        # 2.1 Prepare scenario file
        for message in variation.params["messages"]:
            if (message["action"] == self._get_action_type(entity_role) and (
                    (not next_action_id) or
                    (next_action_id and message.get("id") == next_action_id)
            )
            ):
                if message['type'] == StubServerProtocol.HTTP.value:
                    context = {}  # This is where you save results (e.g., {"var.jws_body": "..."})

                    prep_steps = message['prep_steps']

                    # do prep_steps for preparing body
                    if prep_steps:
                        for step in prep_steps:
                            method_name = step.get("method_name")
                            kwargs = step.get("kwargs", {})
                            for key, value in kwargs.items():
                                kwargs[key], _ = self._check_value_for_file_var_mode(value)
                            save_key, _ = self._check_value_for_file_var_mode(step.get("save_result_as"))

                            # Get the method by name
                            method = getattr(prep_services, method_name)

                            # Call the method with kwargs
                            result = method(**kwargs)

                            # Save the result under desired key
                            context[save_key] = result

                    request_body, is_file = self._check_value_for_file_var_mode(message.get("body"))

                    if is_file:
                        with open(request_body, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        request_body = content
                    else:
                        if request_body in context.keys():
                            request_body = context.get(request_body)

                    action_data[f"http_{entity_role.lower()}"] = {
                        "method": message["method"],
                        "url": message["http_url"],
                        "body": request_body,
                        "next_action": message.get("next_action")
                    }
                    return action_data
                elif message['type'] == StubServerProtocol.SIP.value:
                    sipp_scenario = message["sipp_scenario"]

                    sipp_scenario_file, _ = self._check_value_for_file_var_mode(
                        sipp_scenario.get("scenario_file_path")
                    )

                    filename = os.path.basename(sipp_scenario_file)
                    destination_dir = os.path.join("services", "stub_server", "sip", "scenarios")
                    destination_path = os.path.join(destination_dir, filename)

                    # Ensure destination directory exists
                    os.makedirs(destination_dir, exist_ok=True)

                    shutil.copy(
                        sipp_scenario_file, destination_path
                    )

                    # TODO modify sipp scen file due to prep steps

                    action_data[f"sipp_{entity_role.lower()}_scenario_path"] = {
                        "path": destination_path,
                        "next_action": message.get("next_action")
                    }
                    return action_data

    def _launch_live_capturing(self, variation: RunVariation):
        monitoring_capture_file = os.path.join("/tmp", f"{variation.name.split('.')[0]}_capture.pcap")

        self.captured_files.append(monitoring_capture_file)
        monitor = MonitoringService(
            local_host_ip=self._lab_config.test_suite_host_ip,
            interface="local"
        )
        # monitor.start_local_monitoring(
        #     capture_filter=self._generate_capture_filter_from_config(),
        #     output_file_path=monitoring_capture_file,
        #     timeout=120
        # )
        monitor.start_direct_tshark_capture(
            capture_filter=self._generate_capture_filter_from_config(),
            output_file_path=monitoring_capture_file
        )
        return monitor, monitoring_capture_file

    def _launch_stub_server(self,
                            interface: Interface, port: PortMapping,
                            entity: Entity, action_data: dict) -> (StubServerService, str):
        if port.protocol == StubServerProtocol.SIP.value:
            stub_service = StubServerService(
                entity_name=entity.name,
                lab_config=self._lab_config,
                current_entity=entity,
                port=port,
                current_if=interface,
                docker_service=None,
                scenario_file=action_data.get(f"sipp_{entity.role.lower()}_scenario_path").get("path"),
                run_in_background=True
            )
            stub_service.launch_stub_server()
            return stub_service, action_data.get(f"sipp_{entity.role.lower()}_scenario_path").get("next_action")
        elif port.protocol == StubServerProtocol.HTTP.value:
            stub_service = StubServerService(
                entity_name=entity.name,
                lab_config=self._lab_config,
                current_entity=entity,
                port=port,
                current_if=interface,
                docker_service=None,
                request_data=action_data.get(f"http_{entity.role.lower()}"),
                run_in_background=True
            )
            stub_service.launch_stub_server()
            return stub_service, action_data.get(f"http_{entity.role.lower()}").get("next_action")

    def _prepare_oracle_test_scen(self, run_test: RunTest, variation: RunVariation,
                                  capture=None, pcap_file: str = None):

        if capture:
            variation_pcap_service = PcapCaptureService(capture=capture)
        elif pcap_file:
            variation_pcap_service = PcapCaptureService(pcap_file=pcap_file)
        else:
            raise ValueError("Cannot prepare oracle test scen -> capture or pcap_file is missing")

        print(f"🧪 Loaded capture contains {variation_pcap_service.get_capture_len()} packets.")

        test_list = self.__optimize_test_list_for_variation(
            self.__generate_test_list_for_variation(run_test.requirements, variation.name)
        )
        return OracleTestScenario(
            name=variation.name,
            tests=self.__finalize_test_list_for_variation(
                test_list, variation_pcap_service, variation
            )
        ), variation_pcap_service

    def _run_variation_live(self, run_test: RunTest, variation: RunVariation, shared_scenario, conn):
        print(f" 🏃‍🏃🏃‍ Run of {variation.name} variation - > STARTED")

        monitor, monitoring_capture_file = self._launch_live_capturing(variation)
        time.sleep(3)

        # structure for further management of docker containers and docker services
        sss_list = []
        sss_senders_list = []

        # Look through lab_config to get all required entities
        # Sort entities so that SENDER would be launched last
        sorted_entities = sorted(
            self._lab_config.entities,
            key=lambda e: 1 if e.role.upper() == StubServerRole.SENDER.value else 0
        )

        for entity in sorted_entities:
            if entity.mode.upper() == EntityMode.STUB.value:

                action_data = self._prepare_action_data_for_ss_launch(variation, entity.role.upper())
                # collect interfaces
                for interface in entity.interfaces:
                    for port in interface.port_mapping:
                        _service, _next_action = self._launch_stub_server(
                            interface=interface,
                            port=port,
                            entity=entity,
                            action_data=action_data
                        )

                        if entity.role.upper() == StubServerRole.SENDER.value:
                            while _next_action:
                                time.sleep(10)
                                _service.stop_stub_server()

                                _action_data = (
                                    self._prepare_action_data_for_ss_launch(
                                        variation,
                                        entity.role.upper(),
                                        _next_action
                                    )
                                )

                                _service, _next_action = self._launch_stub_server(
                                    interface=interface,
                                    port=port,
                                    entity=entity,
                                    action_data=_action_data
                                )

                            sss_senders_list.append(_service)
                        else:
                            sss_list.append(_service)

        time.sleep(10)

        for service in sss_senders_list:
            service.stop_stub_server()

        manual_actions = self._get_manual_actions(variation)

        # TODO prompts for actions
        for action in manual_actions:
            sss_temp = []
            print("⚠️ MANUAL STEP REQUIRED ⚠️")
            conn.send({"type": "WAIT_FOR_MANUAL_ACTION", "prompt": action.get("prompt")})
            conn.recv()

            for entity in sorted_entities:
                if (entity.mode.upper() == EntityMode.STUB.value and
                        entity.role.upper() == self._get_ss_role_by_action_type(
                            action.get("next_action").split("_")[0])):

                    action_data = (
                        self._prepare_action_data_for_ss_launch(
                            variation,
                            entity.role.upper(),
                            action.get("next_action")
                        )
                    )

                    # collect interfaces
                    for interface in entity.interfaces:
                        for port in interface.port_mapping:
                            _service, _next_action = self._launch_stub_server(
                                interface=interface,
                                port=port,
                                entity=entity,
                                action_data=action_data
                            )

                            if entity.role.upper() == StubServerRole.SENDER.value:
                                while _next_action:
                                    time.sleep(10)
                                    _service.stop_stub_server()

                                    _action_data = (
                                        self._prepare_action_data_for_ss_launch(
                                            variation,
                                            entity.role.upper(),
                                            _next_action
                                        )
                                    )

                                    _service, _next_action = self._launch_stub_server(
                                        interface=interface,
                                        port=port,
                                        entity=entity,
                                        action_data=_action_data
                                    )
                                sss_temp.append(_service)

            time.sleep(10)
            for service in sss_temp:
                service.stop_stub_server()

        # clean up containers and remove network
        # input("\n🟢 Press [Enter] to proceed with container cleanup...")

        time.sleep(10)

        for service in sss_list:
            service.stop_stub_server()
        self._delete_temp_sipp_scenarios()

        # monitor.stop_monitoring()
        monitor.stop_direct_tshark_capture()
        time.sleep(3)

        # TODO get signal that the Var flow is over
        timeout = 15
        while timeout > 0 and not os.path.exists(monitoring_capture_file):
            time.sleep(1)
            timeout -= 1

        monitor.switch_to_file_capture(monitoring_capture_file)

        print(f"🧪 Prepared capture contains {len(list(monitor.get_capture()))} packets.")
        time.sleep(2)

        shared_scenario.append(monitoring_capture_file)

        # scenario, variation_pcap_service = self._prepare_oracle_test_scen(
        #     pcap_file=monitoring_capture_file,
        #     run_test=run_test,
        #     variation=variation
        # )
        # print("=-= variation_pcap_service -=-")
        # print(variation_pcap_service)
        # shared_scenario.append(scenario)
        # variation_pcap_service.close_capture()

        del monitor
        gc.collect()
        time.sleep(1)

        print(f"‍✅ Run of {variation.name} variation - > FINISHED")

    def __prepare_scenarios(self):
        # TODO add test name to disctinct in outprint
        for run_test in self._run_config.tests:
            print(f"📋 Preparing tests for {run_test.name}...")

            for run_variation in run_test.variations:

                if run_variation.mode.lower() == ScenarioMode.PCAP.value:
                    print(f"🤓 Analyzing PCAP file of {run_variation.name} variation...")
                    scenario, variation_pcap_service = self._prepare_oracle_test_scen(
                        pcap_file=run_variation.pcap_file,
                        variation=run_variation,
                        run_test=run_test
                    )
                    self.scenarios.append(scenario)
                    variation_pcap_service.close_capture()
                elif run_variation.mode.lower() == ScenarioMode.CAPTURE.value:
                    max_retries = 5  # Max times to retry
                    retry_count = 0
                    pcap_path = None

                    while retry_count < max_retries:
                        parent_conn, child_conn = multiprocessing.Pipe()
                        manager = Manager()
                        shared_scenarios = manager.list()
                        p = multiprocessing.Process(
                            target=self._run_variation_live,
                            args=(run_test, run_variation, shared_scenarios, child_conn)
                        )
                        p.start()

                        # 🛑 Wait for the child process to signal that manual input is needed
                        while p.is_alive():
                            if parent_conn.poll():  # non-blocking check
                                msg = parent_conn.recv()
                                if isinstance(msg, dict) and msg.get("type") == "WAIT_FOR_MANUAL_ACTION":
                                    prompt = msg.get("prompt")
                                    input(f"👉 {prompt}")
                                    parent_conn.send("CONTINUE")
                            time.sleep(0.5)

                        p.join()

                        if p.exitcode == 0:
                            print(f"✅ Variation {run_variation.name} finished without error.")
                            pcap_path = shared_scenarios[0]
                            break  # success
                        else:
                            print(f"❌ Variation {run_variation.name} failed with exit code {p.exitcode}. Retrying...")
                            retry_count += 1
                            time.sleep(2)  # Small wait before retry

                    if retry_count == max_retries:
                        raise RuntimeError(
                            f"🛑 Failed to run variation {run_variation.name} after {max_retries} retries.")

                    scenario, variation_pcap_service = self._prepare_oracle_test_scen(
                        pcap_file=pcap_path,
                        run_test=run_test,
                        variation=run_variation
                    )
                    print("=-= variation_pcap_service -=-")
                    print(variation_pcap_service)
                    # shared_scenario.append(scenario)
                    variation_pcap_service.close_capture()

                    self.scenarios.append(scenario)

        print(f"📦 Total tests prepared prepared: {len(self.scenarios)}")

    @staticmethod
    def _delete_temp_sipp_scenarios():
        scenario_dir = os.path.join("services", "stub_server", "sip", "scenarios")

        if os.path.exists(scenario_dir):
            for filename in os.listdir(scenario_dir):
                file_path = os.path.join(scenario_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"Deleted temp scenario: {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

    def run_scenarios(self):
        for scenario in self.scenarios:
            print(f"Testing {scenario.name} variation...")
            for test in scenario.tests:
                test.prepare_intermediate_verdicts()
                scenario.add_intermediate_verdicts(test.get_intermediate_verdicts())
            scenario.calculate_scenario_verdict()
        self._delete_captured_files()

    def _delete_captured_files(self, delete: bool = True):
        if delete:
            for filename in self.captured_files:
                if os.path.exists(filename):
                    os.remove(filename)
                    print(f"✅ Deleted file: {filename}")
                else:
                    print(f"⚠️ File not found: {filename}")

    def calculate_general_verdict(self):
        for scenario in self.scenarios:
            if scenario.get_scenario_verdict().test_verdict == VerdictType.FAILED:
                self.general_verdict = VerdictType.FAILED
                return
        self.general_verdict = VerdictType.PASSED

    def get_test_config(self) -> TestConfig:
        return self._test_config

    def get_run_config(self) -> RunConfig:
        return self._run_config

    def print_general_verdict(self):
        print("Printing Verdict...")

        print(f"General verdict: {self.general_verdict.value}")
        print("-" * 50)

        for scenario in self.scenarios:
            scenario.print_scenario_verdict()

        print(f"General verdict: {self.general_verdict.value}")
