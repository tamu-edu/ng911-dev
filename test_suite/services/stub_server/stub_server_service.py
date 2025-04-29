import ipaddress
import signal

from services.docker.docker_service import DockerService
from services.stub_server.sip.sip_stub_server_service import SIPServerService
from .enums import StubServerProtocol, StubServerRole
import os
import subprocess
import psutil
import ipaddress

from ..config.mapping.protocol_mapping import protocol_map
from ..config.types.lab_config import LabConfig, Entity, Interface, PortMapping


class StubServerService:
    def __init__(
            self, entity_name: str,
            lab_config: LabConfig, current_entity: Entity, current_if: Interface,
            port: PortMapping, docker_service: DockerService = None, scenario_file: str = None,
            request_data: dict = None, run_in_background: bool = True
    ):

        """
        name=entity.name,
        protocol=StubServerProtocol.SIP.value,
        role=entity.role.upper(),
        ip_alias=entity.ip,
        ports=ports,
        scenario_file=container_scenario_path,
        target_uri=None,
        """

        self.interface = current_if
        self._lab_config = lab_config
        self.if_port = port

        self.name = entity_name
        self.protocol = StubServerProtocol(self.if_port.protocol)
        self.role = StubServerRole(current_entity.role) if isinstance(current_entity.role, str) else current_entity.role
        self.ip_alias = current_if.ip
        self.ports = self._prepare_port_mapping()
        self.scenario_file = scenario_file
        self.request_data = request_data
        self.run_in_background = run_in_background
        self.target_uri = self._calculate_target_uri()
        print(self.target_uri)

        self.process = None
        self._is_sipp_was_launched = False

        self.docker_service = docker_service

    def _prepare_port_mapping(self) -> dict:
        protocol = protocol_map.get(self.if_port.protocol.upper())
        if protocol is None:
            raise ValueError(f"Unknown protocol: {self.if_port.protocol}")
        return {
            f"{self.if_port.port}/{protocol}": self.if_port.port,
        }

    def _calculate_target_uri(self) -> str:
        """
        # target_uri format: "sip:<ip>:<port> or http(s)://<ip>:<port>"
        :return: str
        """
        if_name_splited = self.interface.name.split("_")
        target_if_name = f"IF_{if_name_splited[2]}_{if_name_splited[1]}"
        for entity in self._lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == target_if_name:
                    for port in interface.port_mapping:
                        if port.protocol == self.protocol.value.upper():
                            # SW: removed '//' as final IP passed to SIPp was f.e. '//192.168.1.16'
                            if self.protocol.value.upper() == "SIP":
                                return f"{self.protocol.value.lower()}:{interface.ip}:{port.port}"
                            elif self.protocol.value.upper() == "HTTP" or self.protocol.value.upper() == "HTTPS":
                                return f"{self.protocol.value.lower()}://{interface.ip}:{port.port}"

    def _parse_target_uri(self):
        try:
            uri_parts = self.target_uri.split(":")
            return uri_parts[1], int(uri_parts[2])
        except (IndexError, ValueError):
            raise ValueError("target_uri must be in 'sip:<ip>:<port>' format")

    def launch_stub_server(self, use_docker: bool = False):
        if self.protocol == StubServerProtocol.SIP.value:
            if use_docker:
                self._launch_sip_stub_server_as_docker()
            else:
                self._launch_sip_stub_server()
        elif self.protocol == StubServerProtocol.HTTP.value:
            if use_docker:
                self._launch_http_stub_server_as_docker()
            else:
                self._launch_http_stub_server()
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
        network = ipaddress.IPv4Network((self.ip_alias, self.interface.mask), strict=False)
        return str(network)

    def _find_interface_to_bind(self):
        """
        Checks "ip" config from the lab_config
        and looks for interface name matching its value
        :return: Name of network interface or None if not found
        """
        target_ip = ipaddress.IPv4Address(self.ip_alias)

        for iface_name, iface_addresses in psutil.net_if_addrs().items():
            for addr in iface_addresses:
                if addr.family.name == 'AF_INET':
                    try:
                        iface_net = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
                        if target_ip in iface_net:
                            return iface_name
                    except Exception:
                        continue
        return None

    def _launch_sip_stub_server(self):
        sudo = "sudo "
        user = subprocess.run(["whoami"], capture_output=True, text=True)
        if user.stdout.strip() == "root":
            sudo = ""
        """
        --trace_err
        --trace_msg
        SCENARIO_FILENAME_error.log
        SCENARIO_FILENAME_messages.log
        """
        local_interface = self._find_interface_to_bind()
        os.system(f"{sudo}ip addr add {self.ip_alias}/{self.interface.mask} dev {local_interface}")
        print(f"Alias created -> {self.ip_alias}/{self.interface.mask} dev {local_interface}")

        target_ip_port = self.target_uri.replace("sip:", "")
        if self.role == StubServerRole.RECEIVER:
            cmd = (f"{sudo}sipp {self._get_transfer_protocol_flag_value()}"
                   f" -i {self.ip_alias} -p {self.if_port.port} -m 1 --trace_err --trace_msg")
            if self.scenario_file is not None:
                cmd = cmd + f" -sf {self.scenario_file} "
            cmd = cmd + f" -bg {target_ip_port}"
        elif self.role == StubServerRole.SENDER:
            if not self.scenario_file or not self.target_uri:
                raise ValueError("Sender role requires scenario_file and target_uri.")
            ip, port = self._parse_target_uri()
            cmd = (f"{sudo}sipp {self._get_transfer_protocol_flag_value()}"
                   f" -sf {self.scenario_file} -i {self.ip_alias} -p {self.if_port.port} "
                   # f" -sf {self.scenario_file} -s '' -i {self.ip_alias} -p {self.if_port.port} "
                   f"-m 1 --trace_err --trace_msg -bg {target_ip_port}")
        elif self.role == StubServerRole.IUT:
            cmd = (f"{sudo}sipp {self._get_transfer_protocol_flag_value()}"
                   f" -i {self.ip_alias} -p {self.if_port.port} -m 1 --trace_err --trace_msg -bg {target_ip_port}")
        else:
            raise ValueError(f"Unsupported role: {self.role}")

        print(f"[SIPServerService] Launching with: {cmd}")
        self.process = subprocess.Popen(cmd.split())

    def _remove_ip_alias(self, ip, mask, iface="enp0s8"):
        try:
            subprocess.run(
                ["sudo", "ip", "addr", "del", f"{ip}/{mask}", "dev", iface],
                check=False
            )
            print(f"✔️ Removed IP alias: {ip} from {iface}")
        except Exception as e:
            print(f"⚠️ Failed to remove IP alias {ip}: {e}")

    def _kill_existing_sipp(self, ip, port):
        print(f"🔎 Checking for existing SIPp processes on port {port}...")
        try:
            output = subprocess.check_output(["lsof", "-n", "-P", f"-iTCP:{port}", "-sTCP:LISTEN"])
            lines = output.decode().splitlines()
            for line in lines[1:]:  # skip header
                parts = line.split()
                pid = int(parts[1])
                print(f"⚡ Killing old SIPp process PID: {pid}")
                os.kill(pid, signal.SIGKILL)
        except subprocess.CalledProcessError:
            print(f"✅ No SIPp process using port {port}")
        except Exception as e:
            print(f"❌ Unexpected error checking for SIPp processes: {e}")

    def _get_transfer_protocol_flag_value(self) -> str:
        """
        mTLSv1.3 - None (not supported)
        mTLSv1.2 - None (not supported)
        TLSv1.3 - None (not supported)
        TLSv1.2 - '-t l1'
        TCP - '-t t1'
        UDP - '-t u1'
        :return:
        """
        if self.if_port.transport_protocol == "TLSv1.2":
            return '-t l1'
        if self.if_port.transport_protocol == "TCP":
            return '-t t1'
        if self.if_port.transport_protocol == "UDP":
            return '-t u1'

    def _launch_sip_stub_server_as_docker(self):
        image_name = f"{self.name.replace('-', '').lower()}_image"
        container_name = f"{self.name}"

        # 1. Build Docker image if it doesn't exist
        dockerfile_path = os.path.abspath("services/stub_server/sip")  # Make sure it's the folder
        if not self._image_exists(image_name):
            self.docker_service.build_image(
                dockerfile_path=dockerfile_path,
                tag=image_name
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
            gateway=self.interface.gateway
        )

        # 5. Run container on the custom network with specific IP
        self.docker_service.run_container(
            image_name=image_name,
            name=container_name,
            env=env_vars,
            port_bindings=self.ports,  # e.g., {"5060/udp": 5060}
            container_ip=self.ip_alias,  # IP alias to use inside the network
            network_name=subnet
        )

        print(f"SIP Stub Server [{self.role.value}] launched in Docker: {container_name}")

    def _launch_http_stub_server(self):
        sudo = "sudo "
        user = subprocess.run(["whoami"], capture_output=True, text=True)
        if user.stdout.strip() == "root":
            sudo = ""
        local_interface = self._find_interface_to_bind()
        os.system(f"{sudo}ip addr add {self.ip_alias}/{self.interface.mask} dev {local_interface}")

        cmd = [
            "python3", "services/stub_server/http/http_entry.py",
            f"--ip={self.ip_alias}",
            f"--port={self.if_port.port}",
            f"--role={self.role.value}",
            f"--method={self.request_data.get("method")}",
            f"--target_uri={self.target_uri}",
            f"--path={self.request_data.get('url')}",
            f"--run_in_background={str(self.run_in_background)}"
        ]

        # if self.target_uri:
        #     cmd.append(f"--target_uri={self.target_uri}")
        if self.request_data.get("body"):
            cmd.append(f"--body={self.request_data.get("body")}"

        print(f"[HTTPServerService] Launching with: "
              f"python3", " services/stub_server/http/http_entry.py ",
              f"--ip={self.ip_alias} ",
              f"--port={self.if_port.port} ",
              f"--role={self.role.value} ",
              f"--method={self.request_data.get("method")} ",
              f"--target_uri={self.target_uri} ",
              f"--path={self.request_data.get('url')} ",
              f"--run_in_background={str(self.run_in_background)} "
              f"--body={self.request_data.get("body")[:22] if self.request_data.get("body") else ""}"
              )
        self.process = subprocess.Popen(cmd)

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
            network_name="stub_server"
        )
        print(f"HTTP Stub Server [{self.role.value}] launched in Docker: {container_name}")

    def stop_stub_server_dockers(self):
        container_name = f"{self.name}_{self.protocol.value}_stub"
        self.docker_service.stop_container(container_name)
        self.docker_service.remove_container(container_name)
        print(f"Stub Server {container_name} stopped and removed.")

    def stop_stub_server(self):
        if self.process:
            print(f"Stopping Stub Server process (PID: {self.process.pid})...")
            try:
                if self.protocol == StubServerProtocol.SIP.value:
                    self._kill_existing_sipp(self.ip_alias, self.if_port.port)
                self._remove_ip_alias(self.ip_alias, self.interface.mask, self._find_interface_to_bind())

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
            print("Stub Server stopped.")
        else:
            print("No running process to stop.")

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def get_stub_server_status(self):
        container_name = f"{self.name}_{self.protocol.value}_stub"
        return self.docker_service.get_container_status(container_name)

    def _image_exists(self, image_name: str) -> bool:
        images = self.docker_service.client.images.list(name=image_name)
        return len(images) > 0
