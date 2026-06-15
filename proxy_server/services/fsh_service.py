import subprocess
from proxy_server.models.session_models import ConduitConfig, NetworkConfig


class FSHService:
    """
    Manages Forwarding Server Host (FSH).

    Responsibilities:
    - enable forwarding
    - apply iptables DNAT/SNAT rules
    - cleanup rules
    """

    def __init__(self, network: NetworkConfig):
        self._host = network.host
        self._user = network.user
        self._ssh_key = network.ssh_key

        self._applied_commands: list[str] = []

    # =========================
    # PUBLIC API
    # =========================

    def apply_rules(self, conduits: list[ConduitConfig]) -> None:
        """
        Applies forwarding rules for all conduits.
        """

        self._enable_ip_forwarding()

        for conduit in conduits:
            self._apply_conduit_rules(conduit)

    def cleanup(self) -> None:
        """
        Removes applied iptables rules in reverse order.
        """

        for cmd in reversed(self._applied_commands):
            delete_cmd = self._to_delete_rule(cmd)

            try:
                self._run_ssh(delete_cmd)
            except Exception as e:
                print(f"[FSHService] ⚠️ Failed to remove rule: {delete_cmd} | {e}")

        self._applied_commands.clear()

    # =========================
    # INTERNAL RULE LOGIC
    # =========================

    def _apply_conduit_rules(self, conduit: ConduitConfig) -> None:
        """
        For one conduit:

        Device A thinks it sends to Device B.
        FSH redirects that traffic to PSH proxy endpoint.

        A -> B becomes:
        A -> FSH -> PSH proxy_ip:proxy_port
        """

        from_ip = conduit.from_.ip
        to_ip = conduit.to.ip
        to_port = conduit.to.port

        proxy_ip = conduit.proxy.ip
        proxy_port = conduit.proxy.port

        protocol = conduit.transport.protocol.lower()

        # DNAT: traffic originally addressed to target goes to PSH proxy
        dnat_cmd = (
            f"iptables -t nat -A PREROUTING "
            f"-s {from_ip} -d {to_ip} "
            f"-p {protocol} --dport {to_port} "
            f"-j DNAT --to-destination {proxy_ip}:{proxy_port}"
        )

        # MASQUERADE/SNAT: allow forwarding path to work cleanly
        #
        # NOTE:
        # This is intentionally broad for MVP.
        # Later we can replace MASQUERADE with exact SNAT rules
        # if routing requires preserving specific source behavior.
        masquerade_cmd = (
            f"iptables -t nat -A POSTROUTING "
            f"-d {proxy_ip} "
            f"-p {protocol} --dport {proxy_port} "
            f"-j MASQUERADE"
        )

        self._apply_rule(dnat_cmd)
        self._apply_rule(masquerade_cmd)

    def _enable_ip_forwarding(self) -> None:
        self._run_ssh("sysctl -w net.ipv4.ip_forward=1")

    def _apply_rule(self, cmd: str) -> None:
        self._run_ssh(cmd)
        self._applied_commands.append(cmd)

    # =========================
    # SSH EXECUTION
    # =========================

    def _run_ssh(self, remote_cmd: str) -> str:
        # enforce sudo for all FSH operations
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
        """
        Converts:
            iptables ... -A CHAIN ...
        into:
            iptables ... -D CHAIN ...
        """

        if " -A " not in add_cmd:
            raise ValueError(f"Cannot convert iptables rule to delete form: {add_cmd}")

        return add_cmd.replace(" -A ", " -D ", 1)
