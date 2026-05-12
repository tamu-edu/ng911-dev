import time
import os

from enums import TransportProtocolEnum
from logger.logger_service import LoggingMeta
from services.config.types.forward_conduit_config import ForwardConduit, Conduit
from services.config.types.lab_config import LabConfig, PortMapping
from services.config.types.run_config import RunConfig, RunVariation
from .ms_client import MSClient, MSClientError
from .psm_state_enum import State


class ProxyServerManagementService(metaclass=LoggingMeta):
    """
    Proxy Server Management Service or PSMService
    is a Service to manage the proxy server management
    """

    _run_variation: RunVariation
    _run_config: RunConfig
    _lab_config: LabConfig
    _proxy_server_config: dict
    _forward_conduit_config: ForwardConduit

    _TS_PRS_IF_NAME = "IF_PROX_TS"
    _TS_PRS_MS_IF_NAME = "IF_PROX_TS_MS"
    _POLL_INTERVAL = 1  # seconds
    _MAX_WAIT = 600
    _START_MAX_WAIT = 60

    def __init__(
        self,
        session_id: str,
        run_variation: RunVariation,
        run_config: RunConfig,
        lab_config: LabConfig,
        forward_conduit_config: ForwardConduit,
    ):
        self._run_variation = run_variation
        self._run_config = run_config
        self._lab_config = lab_config
        self._forward_conduit_config = forward_conduit_config
        self._session_id = session_id

        self._client = self._set_ms_client()

        self._proxy_server_config = {}
        if forward_conduit_config:
            self._set_proxy_server_config()

    def _set_ms_client(self) -> MSClient:

        _base_url = self._get_ms_base_url()

        return MSClient(base_url=_base_url, timeout=5)

    def _get_ms_base_url(self) -> str:
        _psh = self._lab_config.get_proxy_server_entity()
        _base_url = ""

        for _if in _psh.interfaces:
            if _if.name == self._TS_PRS_IF_NAME:
                for _p in _if.port_mapping:
                    if _p.name == self._TS_PRS_MS_IF_NAME:
                        return f"{_p.protocol.lower()}://{_if.ip}:{_p.port}"

        raise RuntimeError(
            f"[PSM Service] ⚠️ Could not resolve MS base URL "
            f"from {self._TS_PRS_IF_NAME} IF and {self._TS_PRS_MS_IF_NAME} PORT_MAPPING"
        )

    def _set_proxy_server_config(self):
        fsh = self._lab_config.get_forward_server_entity()

        if fsh is None:
            raise RuntimeError("[PSM Service] FORWARD SERVER NOT FOUND")

        self._proxy_server_config = {
            "network": {
                "host": fsh.interfaces[0].ip,
                "user": fsh.ssh.user,
                "ssh_key": fsh.ssh.ssh_key,
            },
            "conduits": self._get_conduits_list(),
        }

        print(f"[PSM Service] PS config set {self._proxy_server_config}")

    def _get_conduits_list(self) -> list:
        conduits_list = []

        for conduit in self._forward_conduit_config.forward_conduits or []:
            conduits_list.extend(self._get_conduit_data(conduit))

        return conduits_list

    def _get_conduit_data(self, conduit: Conduit) -> list:
        """
        {
            "name": conduit.name,
            "from": self._get_if_info(conduit.from_if),
            "to": self._get_if_info(conduit.to_if),
            "proxy": self._get_if_info(conduit.proxy_if),
            "transport": self._add_transport_details()
        }
        """
        # TODO ASK - CHECK by IF or PORT MAPPING? If by IF - should we create a conduit per port in port_mapping
        conduit_list = []
        from_if = self._lab_config.get_if_by_name(conduit.from_if)
        to_if = self._lab_config.get_if_by_name(conduit.to_if)
        proxy_if = self._lab_config.get_if_by_name(conduit.proxy_if)

        if from_if is None:
            raise RuntimeError(f"[PSM Service] from_if {conduit.from_if} NOT FOUND")
        if to_if is None:
            raise RuntimeError(f"[PSM Service] to_if {conduit.to_if} NOT FOUND")
        if proxy_if is None:
            raise RuntimeError(f"[PSM Service] proxy_if {conduit.proxy_if} NOT FOUND")

        for port in from_if.port_mapping:
            to_port = self._get_to_port_mapping(port.name)
            proxy_port = self._get_proxy_port_mapping(port.name)

            if to_port is None:
                raise RuntimeError(f"[PSM Service] to_if {port.name} NOT FOUND")
            if proxy_port is None:
                raise RuntimeError(f"[PSM Service] proxy_if {to_port}_PRS NOT FOUND")

            conduit_list.append(
                {
                    "name": conduit.name,
                    "from": {
                        "ip": from_if.ip,
                        "port": port.port,
                        "protocol": TransportProtocolEnum.get_unified_protocol_name(
                            port.transport_protocol
                        ),
                    },
                    "to": {
                        "ip": to_if.ip,
                        "port": to_port.port,
                        "protocol": TransportProtocolEnum.get_unified_protocol_name(
                            to_port.transport_protocol
                        ),
                    },
                    "proxy": {
                        "ip": proxy_if.ip,
                        "port": proxy_port.port,
                        "protocol": TransportProtocolEnum.get_unified_protocol_name(
                            proxy_port.transport_protocol
                        ),
                    },
                    "transport": {
                        "protocol": TransportProtocolEnum.get_unified_protocol_name(
                            proxy_port.transport_protocol
                        ),
                        "tls": self._get_tls_details(proxy_port, to_if),
                    },
                }
            )
        return conduit_list

    def _get_tls_details(self, port: PortMapping, to_if) -> dict:
        """
        Builds TLS configuration for proxy transport.
        """

        if port.transport_protocol not in TransportProtocolEnum.list_tls():
            return {
                "enabled": False,
                "mode": None,
                "server_side": None,
                "client_side": None,
            }

        pca_cert = self._lab_config.pca_certificate_file
        pca_key = self._lab_config.pca_certificate_key

        if not pca_cert or not pca_key:
            raise RuntimeError(
                "[PSM Service] ⚠️ TLS enabled but PCA cert/key not configured"
            )

        # TODO: replace with dynamically generated cert per target host
        server_cert = pca_cert
        server_key = pca_key

        to_entity = self._lab_config.get_entity_by_if_name(to_if.name)

        client_cert = to_entity.certificate_file if to_entity else None
        client_key = to_entity.certificate_key if to_entity else None

        # TODO "mode": "passthrough"   (no MITM, just capture)
        # TODO "mode": "mirror"        (advanced)

        return {
            "enabled": True,
            "mode": "terminate",
            "server_side": {"cert": server_cert, "key": server_key, "ca": pca_cert},
            "client_side": {"cert": client_cert, "key": client_key, "ca": pca_cert},
        }

    def _get_to_port_mapping(self, from_port_name: str) -> PortMapping | None:
        print(self._reverse_port_name(from_port_name))
        return self._lab_config.get_port_mapp_by_name(
            self._reverse_port_name(from_port_name)
        )

    def _get_proxy_port_mapping(self, from_port_name: str) -> PortMapping | None:
        return self._lab_config.get_port_mapp_by_name(
            f"{self._reverse_port_name(from_port_name)}_PRS"
        )

    @staticmethod
    def _reverse_port_name(port_name: str) -> str:
        pn_split = port_name.split("_")

        return "_".join(["IF", pn_split[2], pn_split[1], *pn_split[3:]])

    def start_session(self) -> None:
        start_time = time.time()

        while True:
            if time.time() - start_time > self._START_MAX_WAIT:
                raise TimeoutError(
                    "[PSM Service] ⚠️ Could not start session: MS busy too long"
                )

            try:
                self._client.start_session(
                    session_id=self._session_id, config=self._proxy_server_config
                )
                print(
                    f"[PSM Service] 🌐 -> session with {self._session_id} id started successfully."
                )
                return  # success

            except MSClientError as e:
                if e.status_code == 409:
                    time.sleep(self._POLL_INTERVAL)
                    continue

                # hard failure
                raise RuntimeError(f"[PSM Service] ⚠️ Failed to start session: {e}")

    def wait_until_running(self) -> None:
        """
        Poll MS until RUNNING.
        Returns if RUNNING or raise an exception if timeout.
        """
        start_time = time.time()

        while True:
            if time.time() - start_time > self._MAX_WAIT:
                raise TimeoutError(
                    "[PSM Service] ⚠️ MS did not entered the RUNNING state "
                    f"after {self._MAX_WAIT} seconds."
                )

            try:
                status = self._client.get_status(self._session_id)
            except MSClientError as e:
                # Important edge case:
                # MS returns 404 when state == READY (no active session)
                # SO if not entered yet might still return 404
                if e.status_code == 404:
                    time.sleep(self._POLL_INTERVAL)
                    continue
                raise RuntimeError(
                    f"[PSM Service] ⚠️ Status check failed during session start: {e}"
                )

            state = status.get("status")

            if not state:
                raise RuntimeError("[PSM Service] Invalid status payload received")

            if state == State.RUNNING.value:
                print(
                    f"[PSM Service] 🌐 -> Session with id {self._session_id} has successfully been started."
                )
                return

            print("[PSM Service] ⏳ -> Waiting for PROXY to start the session.")

            if state == State.RESETTING.value:
                raise RuntimeError("[PSM Service] MS entered RESETTING during startup")

            if state == State.READY.value:
                raise RuntimeError(
                    "[PSM Service] Session returned to READY during startup"
                )

            time.sleep(self._POLL_INTERVAL)

    def wait_until_retrieve_ready(self) -> dict:
        """
        Poll MS until RETRIEVE_READY.
        Returns artifacts dict.
        """
        _start_time = time.time()
        _is_stopping = False

        while True:
            try:
                status = self._client.get_status(self._session_id)
            except MSClientError as e:
                raise RuntimeError(f"[PSM Service] ⚠️ Status check failed: {e}")

            state = status.get("status")

            if state in State.list_active_states():

                print(f"[PSM Service] 🌐 -> Session is {state}.")

                # raise TimeoutError("MS did not reach RETRIEVE_READY in time")
                if state == State.RUNNING.value:
                    if time.time() - _start_time > self._MAX_WAIT and not _is_stopping:
                        print(
                            f"[PSM Service] ⚠️ -> Session is {state} more that {self._MAX_WAIT} seconds. Trying to Stop"
                        )
                        self.stop_session()
                        _is_stopping = True
                        continue
                elif state == State.STOPPING.value:
                    if time.time() - _start_time > self._MAX_WAIT * 2 and _is_stopping:
                        print(
                            f"[PSM Service] ⚠️ -> Session is {state} more "
                            f"that {self._MAX_WAIT} seconds."
                        )
                        raise RuntimeError(
                            "[PSM Service] ⚠️ MS exceeded all possible timeouts."
                        )

                time.sleep(self._POLL_INTERVAL)
                continue

            if state == State.RETRIEVE_READY.value:
                print(
                    "[PSM Service] 🌐 -> Proxy Server artifacts are ready to be retrieved."
                )

                if not status.get("artifacts"):
                    raise RuntimeError(
                        "[PSM Service] ⚠️ No artifacts in status payload"
                    )

                return status.get("artifacts") or {}

            if state == State.RESETTING.value:
                raise RuntimeError("[PSM Service] ⚠️ MS entered RESETTING unexpectedly")

            if state == State.READY.value:
                raise RuntimeError(
                    "[PSM Service] ⚠️ Session disappeared (returned to READY)"
                )

            raise RuntimeError(f"[PSM Service] ⚠️ Unexpected state: {state}")

    def stop_session(self) -> None:
        try:
            self._client.stop_session(self._session_id)
            print("[PSM Service] Initiating session stop")
        except MSClientError as e:
            raise RuntimeError(f"[PSM Service] ⚠️ Failed to initiate session stop: {e}")

    def retrieve_artifacts(self, artifacts: dict, dst_dir: str) -> dict:
        """
        Downloads artifacts from MS.
        Returns local file paths.
        """
        os.makedirs(dst_dir, exist_ok=True)

        local_paths = {}

        for name, path in artifacts.items():
            filename = os.path.basename(path)
            dst_path = os.path.join(dst_dir, filename)

            try:
                self._client.download_artifact(path, dst_path)
                print(
                    f"[PSM Service] 🌐 -> {name} artifact from {path} has been downloaded to {dst_path}."
                )
            except MSClientError as e:
                raise RuntimeError(f"[PSM Service] ⚠️ Failed to download {name}: {e}")

            local_paths[name] = dst_path

        return local_paths

    def reset(self) -> None:
        try:
            self._client.reset_session(self._session_id)
        except MSClientError as e:
            raise RuntimeError(f"[PSM Service] ⚠️ Reset failed: {e}")

    def wait_until_reset(self) -> None:
        start_time = time.time()

        while True:
            if time.time() - start_time > self._MAX_WAIT:
                raise TimeoutError(
                    f"[PSM Service] ⚠️ MS did not return to READY state "
                    f"after {self._MAX_WAIT} seconds."
                )

            try:
                status = self._client.get_status(self._session_id)
            except MSClientError as e:
                # Important edge case:
                # MS returns 404 when state == READY (no active session)
                if e.status_code == 404:
                    return
                raise RuntimeError(
                    f"[PSM Service] ⚠️ Status check failed during reset: {e}"
                )

            state = status.get("status")

            if state == State.READY.value:
                return

            time.sleep(self._POLL_INTERVAL)
