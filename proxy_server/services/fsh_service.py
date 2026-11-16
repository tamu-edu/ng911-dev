import subprocess

from proxy_server.models.session_models import ConduitConfig, NetworkConfig

EGRESS_PORT_OFFSET = 300


class FSHService:
    """
    Manages Forwarding Server Host (FSH).

    Rules per conduit:

    1. FE_A -> FE_B
       DNAT to PSH ingress proxy endpoint.

    2. FE_A -> PSH ingress
       SNAT to FSH so PSH sees FSH as client.

    3. PSH egress -> FE_B
       SNAT to FE_A so FE_B does not see PSH.
    """

    def __init__(self, network: NetworkConfig, proxy_host_ip: str):
        self._host = network.host
        self._user = network.user
        self._proxy_host_ip = proxy_host_ip
        self._ssh_key = network.ssh_key

        self._applied_commands: list[str] = []

        self._applied_routes: set[str] = set()

    # =========================
    # PUBLIC API
    # =========================

    def apply_rules(self, conduits: list[ConduitConfig]) -> None:
        self._enable_ip_forwarding()

        for conduit in conduits:
            self._apply_conduit_rules(conduit)

    def cleanup(self) -> None:
        for cmd in reversed(self._applied_commands):
            delete_cmd = self._to_delete_rule(cmd)

            try:
                self._run_ssh(delete_cmd)
            except Exception as e:
                print(f"[FSHService] ⚠️ Failed to remove rule: {delete_cmd} | {e}")

        self._applied_commands.clear()

        for proxy_ip in self._applied_routes:
            delete_cmd = f"ip route del {proxy_ip} " f"via {self._proxy_host_ip}"

            try:
                self._run_ssh(delete_cmd)
            except Exception as e:
                print(f"[FSHService] ⚠️ Failed to remove route: " f"{delete_cmd} | {e}")

        self._applied_routes.clear()

    # =========================
    # INTERNAL RULE LOGIC
    # =========================

    def _apply_conduit_rules(self, conduit: ConduitConfig) -> None:
        from_ip = conduit.from_.ip
        from_port = conduit.from_.port

        to_ip = conduit.to.ip
        to_port = conduit.to.port

        proxy_ip = conduit.proxy.ip
        proxy_ingress_port = conduit.proxy.port
        proxy_egress_port = proxy_ingress_port + EGRESS_PORT_OFFSET

        protocol = conduit.transport.protocol.lower()

        if protocol == "tls" or "tls" in protocol:
            protocol = "tcp"

        if proxy_ip not in self._applied_routes:
            route_cmd = f"ip route add {proxy_ip} " f"via {self._proxy_host_ip}"

            self._run_ssh(route_cmd)
            self._applied_routes.add(proxy_ip)

        # 1. FE_A -> FE_B redirected to PSH ingress.
        ingress_dnat_cmd = (
            f"iptables -t nat -A PREROUTING "
            f"-s {from_ip} -d {to_ip} "
            f"-p {protocol} --dport {to_port} "
            f"-j DNAT --to-destination {proxy_ip}:{proxy_ingress_port}"
        )

        # 2. PSH ingress leg: PSH sees FSH as immediate peer.
        ingress_snat_cmd = (
            f"iptables -t nat -A POSTROUTING "
            f"-s {from_ip} -d {proxy_ip} "
            f"-p {protocol} --dport {proxy_ingress_port} "
            f"-j SNAT --to-source {self._host}"
        )

        # 3. PSH egress leg: FE_B sees FE_A as immediate peer.
        egress_snat_cmd = (
            f"iptables -t nat -A POSTROUTING "
            f"-s {proxy_ip} -d {to_ip} "
            f"-p {protocol} "
            f"--sport {proxy_egress_port} --dport {to_port} "
            f"-j SNAT --to-source {from_ip}:{from_port}"
        )

        self._apply_rule(ingress_dnat_cmd)
        self._apply_rule(ingress_snat_cmd)
        self._apply_rule(egress_snat_cmd)

    def _enable_ip_forwarding(self) -> None:
        self._run_ssh("sysctl -w net.ipv4.ip_forward=1")

    def _apply_rule(self, cmd: str) -> None:
        self._run_ssh(cmd)
        self._applied_commands.append(cmd)

    # =========================
    # SSH EXECUTION
    # =========================

    def _run_ssh(self, remote_cmd: str) -> str:
        if not remote_cmd.strip().startswith("sudo"):
            remote_cmd = f"sudo {remote_cmd}"

        ssh_cmd = [
            "ssh",
            "-i",
            self._ssh_key,
            "-o",
            "StrictHostKeyChecking=no",
            f"{self._user}@{self._host}",
            remote_cmd,
        ]

        print(f"[FSHService] SSH -> {remote_cmd}")

        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"FSH command failed: {remote_cmd}\n"
                f"STDOUT: {result.stdout}\n"
                f"STDERR: {result.stderr}"
            )

        return result.stdout

    @staticmethod
    def _to_delete_rule(add_cmd: str) -> str:
        if " -A " not in add_cmd:
            raise ValueError(f"Cannot convert iptables rule to delete form: {add_cmd}")

        return add_cmd.replace(" -A ", " -D ", 1)
