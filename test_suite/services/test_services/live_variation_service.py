import copy
import gc
import multiprocessing
import os
import re
import shutil
import signal
import subprocess
import time
import uuid

from logger.logger_service import LoggingMeta
from services import prep_services
from services.aux_services.aux_services import get_ss_role_by_action_type, delete_temp_sipp_scenarios, get_action_type, \
    check_value_for_file_var_mode
from services.config.config_enum import EntityMode
from services.config.types.lab_config import LabConfig, PortMapping, Interface, Entity
from services.config.types.run_config import RunTest, RunVariation
from services.config.types.test_config import VarInterfaces
from services.monitoring_service import MonitoringService
from services.stub_server.enums import StubServerRole, StubServerProtocol
from services.stub_server.stub_server_service import StubServerService
from services.cleanup_registry import kill_process_tree


class LiveVariationService(metaclass=LoggingMeta):
    _lab_config: LabConfig
    _run_variant: RunVariation
    _test_id: uuid
    _output_folder: str
    _variation_ssl_keylog_file: str | None = None
    _variation_not_run_flag: bool = False

    def __init__(self, lab_config: LabConfig, run_variation: RunVariation, test_id: uuid, output_folder: str):
        self._monitor_shared_state = None
        self._shared_ip_aliases = None
        self._test_id = test_id
        self._lab_config = lab_config
        self._run_variation = run_variation
        self._output_folder = output_folder or "/tmp/pcaps"
        self._captured_files = []
        self._shared_scenarios = []
        self._pcap_path = None
        self._variation_ssl_keylog_file = None
        self._active_stub_services: list[StubServerService] = []
        self._monitoring_service = None
        self._current_process = None

    def run(self):
        max_retries = 5  # Max times to retry
        retry_count = 0

        while retry_count < max_retries:
            parent_conn, child_conn = multiprocessing.Pipe()
            manager = multiprocessing.Manager()
            shared_scenarios = manager.list()
            self._monitor_shared_state = manager.list()
            self._shared_ip_aliases = manager.list()
            p = multiprocessing.Process(
                target=self._run_variation_live,
                args=(shared_scenarios, child_conn, self._shared_ip_aliases, self._monitor_shared_state)
            )
            self._current_process = p
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
                print(f"✅ Variation {self._run_variation.name} finished without error.")
                self._pcap_path = shared_scenarios[0]
                break  # success
            else:
                print(f"❌ Variation {self._run_variation.name} failed with exit code {p.exitcode}. Retrying...")
                retry_count += 1
                self.var_cleanup()
                self.ip_alias_cleanup()
                self.tshark_alias_cleanup()
                time.sleep(3)  # Small wait before retry

        if retry_count == max_retries:
            print(
                f"⚠️ Failed to run variation {self._run_variation.name} after {max_retries} retries. Proceeding next.")
            self._variation_not_run_flag = True
            self.ip_alias_cleanup()
            self.tshark_alias_cleanup()

    def _generate_capture_filter_from_config(self):
        unique_ips = set()

        for entity in self._lab_config.entities:
            for interface in entity.interfaces:
                if interface.ip:
                    unique_ips.add(interface.ip)

        # Build the capture filter string
        return " or ".join(f"host {ip}" for ip in sorted(unique_ips))

    @staticmethod
    def _get_manual_actions(variation: RunVariation) -> list:
        """
        Generates manual actions based on variation description
        :param variation: RunVariation object
        :return: list
        """
        manual_actions = []
        for message in variation.params["messages"]:
            if message['action'] == "manual":
                manual_actions.append(message)
        return manual_actions

    def _is_manual_action_first(self) -> (bool, bool):
        """
        Generates manual actions based on variation description
        :param variation: RunVariation object
        :return: list
        """
        if self._run_variation.params.get("messages")[0]["action"] == "manual":
            if self._run_variation.params.get("messages")[0].get("next_action"):
                return True, True
            return True, False
        return False, False

    def _get_config_part_value(self, part: str) -> list | dict:
        config_part = None
        # Match the root config name before any brackets
        match_root = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", part)
        if not match_root:
            raise ValueError("Invalid expression, no valid root variable found")

        config_name = match_root.group(1)

        # Find all keys inside brackets
        keys = re.findall(r"\['([^']+)'\]", part)

        if config_name == "lab_config":
            config_part = self._lab_config.to_dict()

        # TODO add other configs support

        for key in keys:
            if isinstance(config_part, dict):
                config_part = config_part.get(key)
            else:
                raise ValueError(f"Cannot go deeper at key '{key}', current is not a dict")

        return config_part

    @staticmethod
    def _if_port_valid_for_action(port: PortMapping, message_type: str) -> bool:
        if port.protocol.upper() == message_type.upper():
            return True
        if (port.protocol.lower() in [StubServerProtocol.HTTP.value, StubServerProtocol.HTTPS.value]
                and message_type.upper() in [StubServerProtocol.HTTP.value, StubServerProtocol.HTTPS.value]):
            return True
        return False

    def _prepare_sipp_scenario_kwargs(self, context: dict, kwargs: dict) -> dict:
        prepared_kwargs = {}
        for key, value in kwargs.items():
            i_value, _, v_type = check_value_for_file_var_mode(value, True)
            if v_type == "var":
                prepared_kwargs[key] = context.get(i_value)
            elif v_type == "list":
                validated_list = []
                for l_value in i_value:
                    li_value, _, lv_type = check_value_for_file_var_mode(l_value, True)
                    if lv_type == "var":
                        validated_list.append(context.get(li_value))
                    else:
                        validated_list.append(li_value)
                prepared_kwargs[key] = validated_list
            elif v_type == "dict":
                prepared_kwargs[key] = self._prepare_sipp_scenario_kwargs(context, i_value)
            else:
                prepared_kwargs[key] = i_value
        return prepared_kwargs

    def _prepare_action_data_for_ss_launch(
            self,
            entity_role: list,
            interface: Interface,
            port: PortMapping,
            entity: Entity,
            next_action_id: str | None = ""
    ) -> dict | None:
        action_data = {}
        # TODO can it be that the STIMULUS would be HTTP and be started without scenario
        # 2.1 Prepare scenario file
        for message in self._run_variation.params["messages"]:
            if (
                # check if action is appropriate to one of the SS roles
                # SENDER - send
                # RECEIVER - receive
                # OTHER  - other
                    message["action"] in get_action_type(entity_role)
                and (
                    # check if protocol is valid for action
                    self._if_port_valid_for_action(port, message.get("type", ""))
                ) and (
                    # check if there should be next action
                    (not next_action_id)
                    or
                    (next_action_id and message.get("id") == next_action_id)
                ) and (
                    # check IF name
                    message["if_name"] == interface.name
                ) and (
                    # check IF_PORT_NAME
                    # if message["if_port_name"] is not - would be selected the 1 interface
                    # with appropriate protocol
                    (message["if_port_name"] == port.name)
                    or
                    (not message["if_port_name"])
                )
            ):
                context = {}  # This is where you save results (e.g., {"var.jws_body": "..."})

                prep_steps = message['prep_steps']

                # do prep_steps for preparing body
                if prep_steps:
                    for step in prep_steps:
                        method_name = step.get("method_name")
                        kwargs = step.get("kwargs", {})
                        for key, value in kwargs.items():
                            i_value, _, v_type = check_value_for_file_var_mode(value, True)
                            if v_type == "var":
                                kwargs[key] = context.get(i_value)
                            elif v_type == "list":
                                validated_list = []
                                for l_value in i_value:
                                    li_value, _, lv_type = check_value_for_file_var_mode(l_value, True)
                                    if lv_type == "var":
                                        validated_list.append(context.get(li_value))
                                    else:
                                        validated_list.append(li_value)
                                kwargs[key] = validated_list
                            else:
                                kwargs[key] = i_value
                        save_key, _ = check_value_for_file_var_mode(step.get("save_result_as"))

                        # Get the method by name
                        method = getattr(prep_services, method_name)

                        if method_name == "extract_from_config":
                            if isinstance(kwargs.get("config_part"), str):
                                kwargs["config_part"] = self._get_config_part_value(kwargs.get("config_part"))

                        # TODO check if kwargs should be additionally extracted

                        # Call the method with kwargs
                        result = method(**kwargs)

                        # Save the result under desired key
                        context[save_key] = result

                if message['type'] == StubServerProtocol.HTTP.value:
                    request_body, is_file = check_value_for_file_var_mode(message.get("body"))

                    # TODO if there would be different file types (formats)
                    if is_file:
                        with open(request_body, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        request_body = content
                    else:
                        if request_body in context.keys():
                            request_body = context.get(request_body)

                    http_url, _, http_url_type = check_value_for_file_var_mode(message.get("http_url"), True)
                    if http_url_type == "var":
                        http_url = context.get(http_url)

                    action_data[f"http_{entity.name.lower()}"] = {
                        "role": get_ss_role_by_action_type(message["action"]),
                        "method": message["method"],
                        "url": http_url,
                        "body": request_body,
                        "content_type": message.get("content_type"),
                        "certificate_file": message.get("certificate_file"),
                        "certificate_key": message.get("certificate_key"),
                        "next_action": message.get("next_action")
                    }
                    return action_data
                elif message['type'] == StubServerProtocol.SIP.value:
                    sipp_scenario = message["sipp_scenario"]

                    sipp_scenario_file, _ = check_value_for_file_var_mode(
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

                    sipp_kwargs = self._prepare_sipp_scenario_kwargs(
                        context, copy.deepcopy(sipp_scenario.get("kwargs"))
                    )

                    # TODO modify sipp scen file due to prep steps

                    action_data[f"sipp_{entity.name.lower()}_scenario"] = {
                        "role": get_ss_role_by_action_type(message["action"]),
                        "path": destination_path,
                        "sipp_kwargs": sipp_kwargs,
                        "next_action": message.get("next_action")
                    }
                    return action_data
        return None

    def _collect_tls_ports_for_variation(self) -> list[str]:
        """
        Return tshark -d rules (e.g., 'tcp.port==8443,ssl') ONLY for ports
        that will be used by this variation’s stub servers on the local interface.
        """
        rules = set()

        # plaintext ports we never want to force to TLS
        plain_http_ports = (80,)
        plain_sip_ports = (5060,)

        for entity in self._lab_config.entities:
            for interface in entity.interfaces:
                if self.__if_if_name_in_var_ifs(interface.name):
                    for p in interface.port_mapping:
                        proto = (p.protocol or "").upper()
                        transport = (getattr(p, "transport_protocol", "") or "").upper()
                        portnum = int(p.port)

                        # HTTPS → TLS on TCP; force decoding especially on non-443
                        if proto == "HTTPS":
                            if portnum not in plain_http_ports:
                                rules.add(f"tcp.port=={portnum},ssl")
                            continue

                        # SIP over TLS only (don’t touch plain SIP/UDP/TCP)
                        if proto == "SIP" and transport.startswith("TLS"):
                            if portnum not in plain_sip_ports:
                                rules.add(f"tcp.port=={portnum},ssl")
                            continue

                    # add other TLS-carrying protocols here if you introduce any

        return sorted(rules)

    def _launch_live_capturing(self, variation: RunVariation):
        pcap_dir = os.path.join(self._output_folder, "pcaps")
        os.makedirs(pcap_dir, exist_ok=True)

        monitoring_capture_file = os.path.join(
            pcap_dir, f"{variation.name.replace('.', '_')}_capture_{self._test_id}.pcap"
        )

        # one keylog file per test run
        self._variation_ssl_keylog_file = os.path.join(
            pcap_dir, f"{variation.name.replace('.', '_')}_keys_{self._test_id}.tlskeys"
        )

        self._captured_files.append(monitoring_capture_file)
        monitor = MonitoringService(
            local_host_ip=self._lab_config.test_suite_host_ip,
            interface="local",
            ssl_keys_file_path=self._variation_ssl_keylog_file
        )

        # optional: force TLS dissection on nonstandard ports
        decode_as_rules = self._collect_tls_ports_for_variation()

        _tshark_pid = monitor.start_direct_tshark_capture(
            capture_filter=self._generate_capture_filter_from_config(),
            output_file_path=monitoring_capture_file,
            ssl_keys_file_path=self._variation_ssl_keylog_file,
            decode_as=decode_as_rules
        )
        self._monitoring_service = monitor
        return monitor, monitoring_capture_file, _tshark_pid

    def _launch_stub_server(self,
                            interface: Interface, port: PortMapping,
                            entity: Entity, action_data: dict) -> (StubServerService, str):
        if port.protocol == StubServerProtocol.SIP.value:
            try:
                stub_service = StubServerService(
                    entity_name=entity.name,
                    lab_config=self._lab_config,
                    current_entity=entity,
                    port=port,
                    current_if=interface,
                    ss_role=action_data.get(f"sipp_{entity.name.lower()}_scenario").get("role"),
                    docker_service=None,
                    sipp_kwargs=action_data.get(f"sipp_{entity.name.lower()}_scenario").get("sipp_kwargs"),
                    scenario_file=action_data.get(f"sipp_{entity.name.lower()}_scenario").get("path"),
                    ssl_keylog_file=self._variation_ssl_keylog_file,
                    run_in_background=True,
                    shared_ip_aliases=self._shared_ip_aliases
                )
                stub_service.launch_stub_server()
                self._active_stub_services.append(stub_service)
                return stub_service, action_data.get(f"sipp_{entity.name.lower()}_scenario").get("next_action")
            except Exception as e:
                print(e)
                print(f"Failed to run stub server for {entity} -> {port.protocol}: {e}, Skipping this part")
                return None, None
        elif port.protocol == StubServerProtocol.HTTP.value:
            try:
                stub_service = StubServerService(
                    entity_name=entity.name,
                    lab_config=self._lab_config,
                    current_entity=entity,
                    port=port,
                    current_if=interface,
                    ss_role=action_data.get(f"http_{entity.name.lower()}").get("role"),
                    docker_service=None,
                    request_data=action_data.get(f"http_{entity.name.lower()}"),
                    ssl_keylog_file=self._variation_ssl_keylog_file,
                    run_in_background=True,
                    shared_ip_aliases=self._shared_ip_aliases
                )
                stub_service.launch_stub_server()
                self._active_stub_services.append(stub_service)
                return stub_service, action_data.get(f"http_{entity.name.lower()}").get("next_action")
            except Exception as e:
                print(f"Failed to run stub server for {entity} -> {port.protocol}: {e}, Skipping this part")
                return None, None

    def _prepare_and_launch_stub_server(
            self,
            entity: Entity,
            port: PortMapping,
            interface: Interface,
            next_action=None
    ) -> (StubServerService, str):
        action_data = self._prepare_action_data_for_ss_launch(entity.role, interface, port, entity, next_action)

        if action_data:
            return self._launch_stub_server(
                interface=interface,
                port=port,
                entity=entity,
                action_data=action_data
            )
        else:
            return None, None

    def __if_if_name_in_var_ifs(self, if_name: str) -> bool:
        for _if in self._run_variation.interfaces:
            if if_name == _if.name:
                return True
        return False

    def __if_if_port_name_in_var_if_port_names(self, if_name: str, if_port_name: str) -> bool:
        _interface = None
        for _if in self._run_variation.interfaces:
            if if_name == _if.name:
                _interface = _if

        if _interface is None:
            return False

        for _port_name in _interface.port_names:
            if if_port_name == _port_name:
                return True

        if len(_interface.port_names) == 0:
            return True

        return False

    def _sort_entities_sender_last(self, params: dict):
        # Look through lab_config to get all required entities
        # Sort entities so that SENDER would be launched last
        return sorted(
            self._lab_config.entities,
            key=lambda e: 1 if (
                StubServerRole.SENDER.value in e.role and
                any(
                    iface.name == message.get("if_name") and message.get("action") == "send"
                    for iface in e.interfaces
                    for message in params.get("messages", [])
                )
            ) else 0
        )

    def _run_variation_live(self, shared_scenario, conn, shared_ip_aliases, shared_monitor):
        print(f" 🏃‍🏃🏃‍ Run of {self._run_variation.name} variation - > STARTED")
        self._shared_ip_aliases = shared_ip_aliases
        monitor, monitoring_capture_file, tshark_pid = self._launch_live_capturing(self._run_variation)
        shared_monitor.append([tshark_pid, monitoring_capture_file])
        time.sleep(3)

        # structure for further management of docker containers and docker services
        sss_list = []
        sss_senders_list = []

        # Look through lab_config to get all required entities
        # Sort entities so that SENDER would be launched last
        sorted_entities = self._sort_entities_sender_last(self._run_variation.params)

        manual_actions = self._get_manual_actions(self._run_variation)
        is_manual_first, is_first_manual_has_next_action = self._is_manual_action_first()
        is_standard_start = True

        if is_manual_first:
            if not is_first_manual_has_next_action:
                _action = manual_actions.pop(0)
                _timeout = _action.get("timeout")
                if _timeout and isinstance(_timeout, int):
                    print("⚠️ REQUIRED TIMEOUT ⚠️")
                    if _action.get("prompt"):
                        print(_action.get("prompt"))
                    time.sleep(_timeout)
                else:
                    print("⚠️ MANUAL STEP REQUIRED ⚠️")
                    conn.send({"type": "WAIT_FOR_MANUAL_ACTION", "prompt": _action.get("prompt")})
                    conn.recv()
            else:
                is_standard_start = False

        if is_standard_start:
            for entity in sorted_entities:
                if entity.mode.upper() == EntityMode.STUB.value:

                    # collect interfaces
                    for interface in entity.interfaces:
                        if self.__if_if_name_in_var_ifs(interface.name):
                            for port in interface.port_mapping:
                                if self.__if_if_port_name_in_var_if_port_names(interface.name, port.name):
                                    _service, _next_action = self._prepare_and_launch_stub_server(
                                        interface=interface,
                                        port=port,
                                        entity=entity
                                    )

                                    if _service is not None:
                                        if StubServerRole.SENDER.value in entity.role:
                                            while _next_action:
                                                time.sleep(10)
                                                _service.stop_stub_server()

                                                _service, _next_action = self._prepare_and_launch_stub_server(
                                                    interface=interface,
                                                    port=port,
                                                    entity=entity,
                                                    next_action=_next_action
                                                )

                                            if _service is not None:
                                                sss_senders_list.append(_service)
                                        else:
                                            sss_list.append(_service)

                    time.sleep(10)

        for service in sss_senders_list:
            service.stop_stub_server()

        for action in manual_actions:
            sss_temp = []
            _timeout = action.get("timeout")
            if _timeout and isinstance(_timeout, int):
                print("⚠️ REQUIRED TIMEOUT ⚠️")
                if action.get("prompt"):
                    print(action.get("prompt"))
                time.sleep(_timeout)
            else:
                print("⚠️ MANUAL STEP REQUIRED ⚠️")
                conn.send({"type": "WAIT_FOR_MANUAL_ACTION", "prompt": action.get("prompt")})
                conn.recv()

            for entity in sorted_entities:
                if (entity.mode.upper() == EntityMode.STUB.value and
                        get_ss_role_by_action_type(
                            action.get("next_action").split("_")[0]
                        ) in entity.role
                ):

                    # collect interfaces
                    for interface in entity.interfaces:
                        if self.__if_if_name_in_var_ifs(interface.name):
                            for port in interface.port_mapping:
                                if self.__if_if_port_name_in_var_if_port_names(interface.name, port.name):
                                    _service, _next_action = self._prepare_and_launch_stub_server(
                                        interface=interface,
                                        port=port,
                                        entity=entity,
                                        next_action=action.get("next_action")
                                    )

                                    if _service is not None:
                                        if StubServerRole.SENDER.value in entity.role:
                                            while _next_action:
                                                time.sleep(10)
                                                _service.stop_stub_server()

                                                _service, _next_action = self._prepare_and_launch_stub_server(
                                                    interface=interface,
                                                    port=port,
                                                    entity=entity,
                                                    next_action=_next_action
                                                )

                                                if _service is not None:
                                                    sss_temp.append(_service)

            time.sleep(10)
            for service in sss_temp:
                service.stop_stub_server()

        # clean up containers and remove network -> MBR for dev
        # input("\n🟢 Press [Enter] to proceed with container cleanup...")
        # time.sleep(10)

        for service in sss_list:
            service.stop_stub_server()
        delete_temp_sipp_scenarios()

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

        del monitor
        gc.collect()
        time.sleep(1)

        print(f"‍✅ Run of {self._run_variation.name} variation - > FINISHED")

    def delete_captured_files(self, delete: bool = True):
        if delete:
            for filename in self._captured_files:
                if os.path.exists(filename):
                    os.remove(filename)
                    print(f"✅ Deleted file: {filename}")
                else:
                    print(f"⚠️ File not found: {filename}")

    def get_pcap_path(self):
        return self._pcap_path

    def get_variation_not_run_flag(self):
        return self._variation_not_run_flag

    def var_cleanup(self):
        print("[cleanup] LiveVariationService cleanup started")

        # 1. Kill variation process group FIRST
        p = getattr(self, "_current_process", None)
        if p and p.pid:
            kill_process_tree(p.pid)
            try:
                p.join(timeout=5)
            except Exception:
                pass
            self._current_process = None

    def ip_alias_cleanup(self):
        aliases = list(getattr(self, "_shared_ip_aliases", []))
        for ip, prefix, interface in aliases:
            subprocess.run(
                ["ip", "addr", "del", f"{ip}/{prefix}", "dev", interface],
                check=False
            )
            print(f"✔ Removed IP alias: {ip}/{prefix} dev {interface}")

        if hasattr(self, "_shared_ip_aliases"):
            self._shared_ip_aliases[:] = []

        print("[cleanup] LiveVariationService cleanup finished")

    def tshark_alias_cleanup(self):
        _monitors = list(getattr(self, "_monitor_shared_state", []))
        for _t_pid, _pcap_path in _monitors:
            # 1. Try graceful stop first
            try:
                subprocess.run(
                    ["tshark", "-r", _pcap_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1
                )
            except Exception:
                pass

            # 2. Kill tshark if still alive
            try:
                os.killpg(os.getpgid(_t_pid), signal.SIGTERM)
                print(f"[cleanup] Killed tshark PID {_t_pid}")
            except ProcessLookupError:
                pass
            except Exception as e:
                print(f"[cleanup] Failed killing tshark {_t_pid}: {e}")

        self._monitor_shared_state[:] = []

    def cleanup(self):
        self.var_cleanup()
        self.ip_alias_cleanup()
        self.tshark_alias_cleanup()
