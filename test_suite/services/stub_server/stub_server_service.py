import json
import logging
import os
import subprocess
from typing import List, Any

import psutil
import ipaddress

from enums import TransportProtocolEnum
from services.docker.docker_service import DockerService
from .enums import StubServerProtocol, StubServerRole
from ..aux_services.aux_services import get_sudo
from ..config.mapping.protocol_mapping import protocol_map
from ..config.types.lab_config import LabConfig, Entity, Interface, PortMapping
from services.process.process_runner import run_process


class StubServerService:
    _ACTIVE_SERVICES: set[Any] = set()

    def __init__(
        self,
        entity_name: str,
        lab_config: LabConfig,
        current_entity: Entity,
        current_if: Interface,
        port: PortMapping,
        ss_role: StubServerRole,
        docker_service: DockerService | None = None,
        scenario_file: str | None = None,
        sipp_kwargs: dict | None = None,
        request_data: dict | None = None,
        run_in_background: bool = True,
        ssl_keylog_file: str | None = None,
        shared_ip_aliases=None,
    ):

        self.interface = current_if
        self._lab_config = lab_config
        self.if_port = port

        self.name = entity_name
        self.protocol = StubServerProtocol(self.if_port.protocol)
        self.current_entity = current_entity
        self.role = ss_role
        self.ip_alias = current_if.ip
        self.ip_alias_exist = False
        self.ports = self._prepare_port_mapping()
        self.scenario_file = scenario_file
        self.sipp_kwargs = sipp_kwargs
        self.request_data = request_data
        self.run_in_background = run_in_background
        self.target_uri = self._calculate_target_uri()
        self.ssl_keylog_file = ssl_keylog_file

        self.process = None
        self._is_sipp_was_launched = False

        self.docker_service = docker_service
        self._shared_ip_aliases = shared_ip_aliases if shared_ip_aliases else []

    def _prepare_port_mapping(self) -> dict:
        protocol = protocol_map.get(self.if_port.protocol.upper())
        if protocol is None:
            raise ValueError(f"Unknown protocol: {self.if_port.protocol}")
        return {
            f"{self.if_port.port}/{protocol}": self.if_port.port,
        }

    def _get_target_api_prefix(self) -> str | None:
        """
        Returns the target Entity api prefix
        :return:
        """
        if_name_splited = self.interface.name.split("_")
        target_if_name = f"IF_{if_name_splited[2]}_{if_name_splited[1]}"
        for entity in self._lab_config.entities:
            if entity.api_http_url_prefix:
                for interface in entity.interfaces or []:
                    if interface.name == target_if_name:
                        if entity.api_http_url_prefix:
                            return entity.api_http_url_prefix.removeprefix(
                                "/"
                            ).removesuffix("/")
        return None

    def _calculate_target_uri(self) -> str | None:
        """
        # target_uri format: "sip:<ip>:<port> or http(s)://<ip>:<port>"
        :return: str
        """
        if_name_splited = self.interface.name.split("_")
        target_if_name = f"IF_{if_name_splited[2]}_{if_name_splited[1]}"
        for entity in self._lab_config.entities:
            for interface in entity.interfaces or []:
                if interface.name == target_if_name:
                    for port in interface.port_mapping or []:
                        if port.protocol == self.protocol.value.upper():
                            if self.protocol.value.upper() == "SIP":
                                return (
                                    f"{self.protocol.value.lower()}:{interface.fqdn or entity.fqdn or interface.ip}"
                                    f":{port.port}"
                                )
                            elif (
                                self.protocol.value.upper() == "HTTP"
                                or self.protocol.value.upper() == "HTTPS"
                            ):
                                return (
                                    f"{self.protocol.value.lower()}://"
                                    f"{interface.fqdn or entity.fqdn or interface.ip}"
                                    f":{port.port}"
                                )
        return None

    def _parse_target_uri(self):
        try:
            uri_parts = self.target_uri.split(":")
            return uri_parts[1], int(uri_parts[2])
        except (IndexError, ValueError):
            raise ValueError("target_uri must be in 'sip:<ip>:<port>' format")

    def _should_use_python_sip(self) -> bool:
        """
        Decide whether to use the Python-based SIP stub server
        based on scenario file location.

        Rule:
        - scenarios under .../sip_service/... -> Python SIP service
        - all other scenarios -> legacy SIPp-based stub server
        """
        if not self.scenario_file:
            return False

        # Normalize path and make it OS-independent
        normalized = os.path.normpath(self.scenario_file).replace("\\", "/")
        # Match folder used for new SipService scenarios
        return "/sip_service/" in normalized

    def launch_stub_server(self, use_docker: bool = False):
        StubServerService._ACTIVE_SERVICES.add(self)
        if self.protocol.value == StubServerProtocol.SIP.value:
            if use_docker:
                self._launch_sip_stub_server_as_docker()
            else:
                # Auto-select engine based on scenario path
                if self._should_use_python_sip():
                    self._launch_sip_python_stub_server()
                else:
                    self._launch_sip_stub_server()
        elif self.protocol.value == StubServerProtocol.HTTP.value:
            if use_docker:
                self._launch_http_stub_server_as_docker()
            else:
                self._launch_http_stub_server()
        elif self.protocol.value == StubServerProtocol.HTTPS.value:
            if use_docker:
                self._launch_https_stub_server_as_docker()
            else:
                self._launch_https_stub_server()
        else:
            raise ValueError("Unsupported protocol provided.")

    def _calculate_subnet(self):
        """
        Calculate the subnet in CIDR notation from the IP and subnet mask.

        :param ip: IP address as string (e.g., "192.168.1.10")
        :param mask: Subnet mask as string (e.g., "255.255.255.0")
        :param gateway: Gateway IP as string (e.g., "192.168.1.1")
        :return: Subnet in CIDR format (e.g., "192.168.1.0/24")
        """
        network = ipaddress.IPv4Network(
            (self.ip_alias, self.interface.mask), strict=False
        )
        return str(network)

    @staticmethod
    def _check_iface_by_target_ip(target_ip):
        for iface_name, iface_addresses in psutil.net_if_addrs().items():
            for addr in iface_addresses or []:
                if addr.family.name == "AF_INET":
                    try:
                        iface_net = ipaddress.IPv4Network(
                            f"{addr.address}/{addr.netmask}", strict=False
                        )
                        if target_ip in iface_net:
                            return iface_name
                    except Exception as e:
                        _logger = logging.getLogger("LoggerService")
                        _logger.debug(e)
                        continue

    def _find_interface_to_bind(self):
        """
        Checks "ip" config from the lab_config
        and looks for interface name matching its value
        :return: Name of network interface or None if not found
        """
        target_ip = ipaddress.IPv4Address(self.ip_alias)
        _test_suite_host_ip = ipaddress.IPv4Address(self._lab_config.test_suite_host_ip)
        _iface_name_for_return = self._check_iface_by_target_ip(target_ip)
        if _iface_name_for_return:
            return _iface_name_for_return
        else:
            return self._check_iface_by_target_ip(_test_suite_host_ip)

    def _add_ip_alias_safely(self, ip, mask, interface):
        sudo = get_sudo()
        try:
            prefix = ipaddress.IPv4Network((ip, mask), strict=False).prefixlen
        except Exception:
            try:
                prefix = int(str(mask))
            except Exception:
                prefix = 24

        existing = subprocess.check_output(
            ["ip", "addr", "show", "dev", interface],
            text=True,
        )

        needle = f"{ip}/{prefix}"

        if needle not in existing:

            cmd = ["ip", "addr", "add", f"{ip}/{prefix}", "dev", interface]

            if sudo:
                cmd.insert(0, "sudo")

            subprocess.run(cmd, check=True, shell=False)

            print(f"Alias created -> {ip}/{prefix} dev {interface}")

            self._shared_ip_aliases.append((ip, prefix, interface))
        else:
            self.ip_alias_exist = True
            print(f"⚠️ IP alias {ip}/{prefix} already exists on {interface}")

    def _launch_sip_stub_server(self):
        sudo = get_sudo()
        """
        --trace_err
        --trace_msg
        SCENARIO_FILENAME_error.log
        SCENARIO_FILENAME_messages.log
        """
        local_interface = self._find_interface_to_bind()
        # os.system(f"{sudo}ip addr add {self.ip_alias}/{self.interface.mask} dev {local_interface}")
        # print(f"Alias created -> {self.ip_alias}/{self.interface.mask} dev {local_interface}")
        self._add_ip_alias_safely(self.ip_alias, self.interface.mask, local_interface)

        target_ip_port = self.target_uri.replace("sip:", "")
        additional_sipp_kwargs = ""
        if self.sipp_kwargs:
            if not self.sipp_kwargs.get("m") and not self.sipp_kwargs.get("-m"):
                if self.role == StubServerRole.SENDER:
                    self.sipp_kwargs["-m"] = "1"
                else:
                    self.sipp_kwargs["-m"] = "999"
            for key, value in self.sipp_kwargs.items() or []:
                key = key.removeprefix("-")
                if isinstance(value, dict):
                    for _k, _v in value.items():
                        additional_sipp_kwargs += f" -{key} {_k} {_v}"
                else:
                    additional_sipp_kwargs += f" -{key} {value}"
        else:
            if self.role == StubServerRole.SENDER:
                additional_sipp_kwargs += " -m 1"
            else:
                additional_sipp_kwargs += " -m 999"

        if self.role == StubServerRole.RECEIVER:
            cmd = (
                f"{sudo} sipp {self._get_transfer_protocol_flag_value()}"
                f" -i {self.ip_alias} -p {self.if_port.port} --trace_err --trace_msg"
            )

            if self.scenario_file is not None:
                cmd = cmd + f" -aa -default_behaviors -all,bye -sf {self.scenario_file}"

            if additional_sipp_kwargs:
                cmd = cmd + additional_sipp_kwargs

            cmd = cmd + " -bg"
        elif self.role == StubServerRole.SENDER:
            if not self.scenario_file or not self.target_uri:
                raise ValueError("Sender role requires scenario_file and target_uri.")

            cmd = (
                f"{sudo} sipp {self._get_transfer_protocol_flag_value()}"
                f" -sf {self.scenario_file} -i {self.ip_alias} -p {self.if_port.port}"
            )

            if additional_sipp_kwargs:
                cmd = cmd + additional_sipp_kwargs

            cmd = cmd + f" -aa -default_behaviors -all,bye -bg {target_ip_port}"

        elif self.role == StubServerRole.OTHER:
            cmd = (
                f"{sudo} sipp {self._get_transfer_protocol_flag_value()}"
                f" -i {self.ip_alias} -p {self.if_port.port} --trace_err --trace_msg"
            )

            if additional_sipp_kwargs:
                cmd = cmd + additional_sipp_kwargs

            cmd = cmd + f" -aa -default_behaviors -all,bye -bg {target_ip_port}"
        else:
            raise ValueError(f"Unsupported role: {self.role}")

        print(f"[SIPServerService] Launching with: {cmd}")
        self.process = run_process(cmd.split(), name="SIPp_Stub_Server")

    def _remove_ip_alias(self, ip, mask, iface="enp0s8"):
        try:
            if not self.ip_alias_exist:
                subprocess.run(
                    ["sudo", "ip", "addr", "del", f"{ip}/{mask}", "dev", iface],
                    check=False,
                )
                print(f"✔️ Removed IP alias: {ip} from {iface}")
            else:
                print(
                    f"⚠️ Skipped removing IP alias {ip}/{mask} on {iface} - was existing before Test Suite run"
                )
        except Exception as e:
            print(f"⚠️ Failed to remove IP alias {ip}: {e}")

    def _map_transport_for_py_sip(self) -> str:
        """
        Map lab transport to sip_entry --protocol.
        TLSv1.2/mTLSv1.2 -> TLS
        TCP -> TCP
        UDP -> UDP
        """
        tp = (self.if_port.transport_protocol or "").upper()
        if tp.startswith("TLS"):
            return "TLS"
        if tp == "TCP":
            return "TCP"
        return "UDP"

    def _get_tls_cli_args_for_py_sip(self) -> list[str]:
        """
        Build TLS/mTLS CLI args for our Python sip_entry.
        - server cert/key for RECEIVER (to accept TLS)
        - CA and --require-client-cert for mTLS RECEIVER
        - key log file if provided
        """
        args: List[Any] = []
        proto = self._map_transport_for_py_sip()
        if proto == "TLS":
            # Key log (Wireshark NSS format)
            if self.ssl_keylog_file:
                args += ["--tls-keylog-file", f"{self.ssl_keylog_file}"]

            # Server side TLS (RECEIVER)
            if self.role == StubServerRole.RECEIVER:
                if (
                    self.current_entity.certificate_file
                    and self.current_entity.certificate_key
                ):
                    args += [
                        "--tls-cert",
                        f"{self.current_entity.certificate_file}",
                        "--tls-key",
                        f"{self.current_entity.certificate_key}",
                    ]

                # mTLS for RECEIVER (require client cert)
                tp = (self.if_port.transport_protocol or "").upper()
                if "MTLS" in tp and self._lab_config.pca_certificate_file:
                    args += [
                        "--tls-ca",
                        f"{self._lab_config.pca_certificate_file}",
                        "--require-client-cert",
                    ]

        return args

    def _launch_sip_python_stub_server(self):
        """
        Launch our Python-based SIP service (sip_entry.py) instead of SIPp.
        Keeps the same behavior as _launch_sip_stub_server regarding IP aliasing.
        """
        # sudo = get_sudo()

        local_interface = self._find_interface_to_bind()
        if not local_interface:
            raise RuntimeError(f"Cannot find host interface for IP {self.ip_alias}")
        self._add_ip_alias_safely(self.ip_alias, self.interface.mask, local_interface)

        sip_entry_path = "test_suite/services/stub_server/sip_service/sip_entry.py"

        cmd = [
            "python3",
            sip_entry_path,
            "--bind-ip",
            f"{self.ip_alias}",
            "--bind-port",
            f"{self.if_port.port}",
            "--protocol",
            self._map_transport_for_py_sip(),
            "--scenario",
            f"{self.scenario_file}",
        ]

        if self.scenario_file and self.scenario_file.lower().endswith(".xml"):
            cmd += ["--scenario-type", "sipp"]
        else:
            cmd += ["--scenario-type", "yaml"]

        if self.role == StubServerRole.RECEIVER:
            cmd += ["--message-timeout", "300000000"]
            cmd += ["--transaction-timeout", "300000000"]

        if self.role == StubServerRole.SENDER:
            if not self.target_uri:
                raise ValueError(
                    "Sender role requires target_uri (e.g., sip:<ip>:<port>)"
                )
            remote_ip, remote_port = self._parse_target_uri()
            cmd += ["--remote-ip", f"{remote_ip}", "--remote-port", f"{remote_port}"]

        cmd += self._get_tls_cli_args_for_py_sip()

        rtp_bind_ip = (self.request_data or {}).get("rtp_bind_ip") or self.ip_alias
        rtp_bind_port = (self.request_data or {}).get(
            "rtp_bind_port"
        ) or self.if_port.port
        rtp_remote_ip = (self.request_data or {}).get("rtp_remote_ip")
        rtp_remote_port = (self.request_data or {}).get("rtp_remote_port")
        if rtp_bind_ip and rtp_bind_port:
            cmd += [
                "--rtp-bind-ip",
                f"{rtp_bind_ip}",
                "--rtp-bind-port",
                f"{rtp_bind_port}",
            ]
        if rtp_remote_ip and rtp_remote_port:
            cmd += [
                "--rtp-remote-ip",
                f"{rtp_remote_ip}",
                "--rtp-remote-port",
                f"{rtp_remote_port}",
            ]

        if self.sipp_kwargs:
            for k, v in self.sipp_kwargs.items():
                if isinstance(v, (str, int, float)):
                    cmd += ["--var", f"{k.removeprefix('-').removeprefix('--')}={v}"]
                if isinstance(v, dict):
                    for _k, _v in v.items():
                        cmd += [f"--{k.removeprefix('-').removeprefix('--')}", _k, _v]

        print(f"[SIPServerService:PY] Launching with: {' '.join(cmd)}")

        self.process = run_process(cmd, name="SIP:PY_Stub_Server")

    def _kill_existing_ss_server_process(self, ip, port):
        """
        Kill any process that is LISTENING on exact (ip, port).
        Works for TCP.
        """

        print(f"🔎 Checking for process listening on {ip}:{port}...")

        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    for conn in proc.connections(kind="inet"):
                        if conn.status == psutil.CONN_LISTEN:
                            laddr = conn.laddr
                            if laddr.ip == ip and laddr.port == port:
                                print(
                                    f"⚡ Killing PID {proc.pid} ({proc.name()}) bound to {ip}:{port}"
                                )
                                proc.kill()
                                proc.wait(timeout=3)
                                print("✅ Process killed.")
                                return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            print(f"✅ No process listening on {ip}:{port}")

        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    def _get_transfer_protocol_flag_value(self) -> str:
        """
        for SIPP
        mTLSv1.3 - None (not supported)
        mTLSv1.2 - None (not supported)
        TLSv1.3 - None (not supported)
        TLSv1.2 - '-t l1'
        TCP - '-t t1'
        UDP - '-t u1'
        :return:
        """
        if self.if_port.transport_protocol == "TLSv1.2":
            return (
                f"-t ln -max_socket 1000 "
                f"-tls_cert {self.current_entity.certificate_file} "
                f"-tls_key {self.current_entity.certificate_key} "
                f"-tls_ca {self._lab_config.pca_certificate_file}"
            )
        if self.if_port.transport_protocol == "TCP":
            return "-t tn -max_socket 1000"
        if self.if_port.transport_protocol == "UDP":
            return "-t un -max_socket 1000"
        return ""

    def _launch_sip_stub_server_as_docker(self):
        image_name = f"{self.name.replace('-', '').lower()}_image"
        container_name = f"{self.name}"

        # 1. Build Docker image if it doesn't exist
        dockerfile_path = os.path.abspath(
            "services/stub_server/sip"
        )  # Make sure it's the folder
        if not self._image_exists(image_name):
            self.docker_service.build_image(
                dockerfile_path=dockerfile_path, tag=image_name
            )

        # 2. Prepare environment variables for container
        print("_________")
        print(self.scenario_file)
        print(self.target_uri)
        print("_________")
        env_vars = {
            "ROLE": self.role.value,
            "IP": self.ip_alias,
            "PORTS": str(self.ports),  # Make sure it's serializable
            "PORT": self.if_port.port,
            "SCENARIO_FILE": self.scenario_file or "",
            "TARGET_URI": self.target_uri or "",
        }

        # 3. Calculate subnet from interface data
        subnet = self._calculate_subnet()

        # 4. Create docker network if needed
        self.docker_service.ensure_network(
            name=subnet,  # Using subnet as network name for uniqueness
            subnet=subnet,
            gateway=self.interface.gateway,
        )

        # 5. Run container on the custom network with specific IP
        self.docker_service.run_container(
            image_name=image_name,
            name=container_name,
            env=env_vars,
            port_bindings=self.ports,  # e.g., {"5060/udp": 5060}
            container_ip=self.ip_alias,  # IP alias to use inside the network
            network_name=subnet,
        )

        print(
            f"SIP Stub Server [{self.role.value}] launched in Docker: {container_name}"
        )

    def _get_ssl_args(self):
        # TLS versioning
        args = ["--tls_min=1.2", "--tls_max=1.3"]

        # HTTPS receiver (serve TLS)
        if self.role == StubServerRole.RECEIVER:
            if (
                self.current_entity.certificate_file
                and self.current_entity.certificate_key
            ):
                args.append(f"--server_cert={self.current_entity.certificate_file}")
                args.append(f"--server_key={self.current_entity.certificate_key}")

            if self.if_port.transport_protocol in [
                TransportProtocolEnum.mTLSV1_2.value,
                TransportProtocolEnum.mTLSV1_3.value,
            ]:
                if self.current_entity.certificate_file:
                    args.append(f"--ca={self._lab_config.pca_certificate_file}")
                else:
                    print("For mTLS - PCA is required for certificate validation.")
                args.append("--require_client_cert")

        # HTTPS sender (verify/mTLS)
        if self.role == StubServerRole.SENDER:
            if self.current_entity.certificate_file:
                args.append(f"--ca={self._lab_config.pca_certificate_file}")
            if self.request_data.get("insecure"):
                args.append("--insecure")

            if self.if_port.transport_protocol in [
                TransportProtocolEnum.mTLSV1_2.value,
                TransportProtocolEnum.mTLSV1_3.value,
            ]:
                if (
                    self.current_entity.certificate_file
                    and self.current_entity.certificate_key
                ):
                    args.append(f"--cert={self.current_entity.certificate_file}")
                    args.append(f"--cert_key={self.current_entity.certificate_key}")

        if self.ssl_keylog_file:
            args.append(f"--keylog={self.ssl_keylog_file}")

        return args

    def _launch_https_stub_server(self):
        if self.if_port.protocol.upper() == StubServerProtocol.HTTPS.value:
            self._launch_http_stub_server(ssl_args=self._get_ssl_args())
            return
        else:
            for port in self.interface.port_mapping or []:
                if port.protocol.upper() == StubServerProtocol.HTTPS.value:
                    self.if_port = port
                    self.ports = self._prepare_port_mapping()
                    self._launch_http_stub_server(ssl_args=self._get_ssl_args())
                    return
        self._launch_http_stub_server()

    def _launch_http_stub_server(self, ssl_args: list | None = None) -> None:
        # sudo = get_sudo()
        local_interface = self._find_interface_to_bind()
        # os.system(f"{sudo}ip addr add {self.ip_alias}/{self.interface.mask} dev {local_interface}")

        self._add_ip_alias_safely(self.ip_alias, self.interface.mask, local_interface)

        cmd = [
            "python3",
            "test_suite/services/stub_server/http/http_entry.py",
            f"--ip={self.ip_alias}",
            f"--port={self.if_port.port}",
            f"--role={self.role.value}",
            f"--target_prefix={self._get_target_api_prefix()}",
            f"--target_uri={self.target_uri}",
            f"--run_in_background={str(self.run_in_background)}",
        ]

        if (self.request_data or {}).get("method"):
            method = (self.request_data or {}).get("method")
            if isinstance(method, (list, dict)):
                method = json.dumps(method, separators=(",", ":"))
            cmd.append(f"--method={method}")

        if (self.request_data or {}).get("url"):
            path = (self.request_data or {}).get("url")
            if isinstance(path, (list, dict)):
                path = json.dumps(path, separators=(",", ":"))
            cmd.append(f"--path={path}")

        # if self.target_uri:
        #     cmd.append(f"--target_uri={self.target_uri}")
        if (self.request_data or {}).get("body"):
            body = (self.request_data or {}).get("body")
            if isinstance(body, (dict, list)):
                body = json.dumps(body)
            cmd.append(f"--body={body}")
        if (self.request_data or {}).get("content_type"):
            cmd.append(
                f"--content_type={(self.request_data or {}).get('content_type')}"
            )

        if ssl_args:
            cmd.extend(ssl_args)

        print("[HTTPServerService] Launching with:", " ".join(cmd))
        self.process = run_process(cmd, name="HTTP_Stub_Server")

    def _launch_http_stub_server_as_docker(self):
        image_name = "http_stub_server_image"
        container_name = f"{self.name}_http_stub"

        dockerfile_path = os.path.abspath("http")
        if not self._image_exists(image_name):
            self.docker_service.build_image(dockerfile_path, image_name)

        env_vars = {
            "ROLE": self.role.value,
            "IP": self.ip_alias,
            "PORTS": self.ports,
            "TARGET_URI": self.target_uri or "",
        }

        self.docker_service.run_container(
            image_name=image_name,
            name=container_name,
            env=env_vars,
            port_bindings=self.ports,
            container_ip=self.ip_alias,
            network_name="stub_server",
        )
        print(
            f"HTTP Stub Server [{self.role.value}] launched in Docker: {container_name}"
        )

    def _launch_https_stub_server_as_docker(self):
        # TODO implement or deprecate all docker methods
        pass

    def stop_stub_server_dockers(self):
        container_name = f"{self.name}_{self.protocol.value}_stub"
        self.docker_service.stop_container(container_name)
        self.docker_service.remove_container(container_name)
        print(f"Stub Server {container_name} stopped and removed.")

    def stop_stub_server(self):
        if self.process:
            print(f"Stopping Stub Server process (PID: {self.process.pid})...")
            try:
                if self.protocol.value == StubServerProtocol.SIP.value:
                    self._kill_existing_ss_server_process(
                        self.ip_alias, self.if_port.port
                    )
                self._remove_ip_alias(
                    self.ip_alias, self.interface.mask, self._find_interface_to_bind()
                )

                # If the process is still alive
                if self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                        print("Stub Server process terminated.")
                    except subprocess.TimeoutExpired:
                        print("Process did not terminate in time. Killing...")
                        self.process.kill()
                        self.process.wait()
                        print("Stub Server process killed.")
                else:
                    # If already terminated (zombie), just reap
                    self.process.wait()
                    print("Stub Server process was already terminated (zombie reaped).")

            except Exception as e:
                print(f"⚠️ Failed to stop process cleanly: {e}")
            finally:
                self.process = None
                StubServerService._ACTIVE_SERVICES.discard(self)
            print("Stub Server stopped.")
        else:
            print("No running process to stop.")

    @classmethod
    def stop_all(cls):
        print("[cleanup] Stopping all StubServerService instances")
        for svc in list(cls._ACTIVE_SERVICES):
            try:
                svc.stop_stub_server()
            except Exception as e:
                print(f"[cleanup] Failed stopping stub server: {e}")
        cls._ACTIVE_SERVICES.clear()

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def get_stub_server_status(self):
        container_name = f"{self.name}_{self.protocol.value}_stub"
        return self.docker_service.get_container_status(container_name)

    def _image_exists(self, image_name: str) -> bool:
        if not self.docker_service:
            raise RuntimeError("Docker service is not initialized")

        images = self.docker_service.client.images.list(name=image_name)
        return len(images) > 0
