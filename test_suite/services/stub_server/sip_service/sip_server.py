import logging
import ssl
import threading
import time

from rtp_transport import RTPTransport
from scenario_runner import ScenarioRunner
from sip_transport import SIPTransport
from sipp_loader import load_sipp_or_yaml
from utils import default_vars


class SIPStubServerService:
    def __init__(
        self,
        bind,
        remote,
        protocol,
        scenario_path,
        scenario_type="auto",
        rtp_bind=None,
        rtp_remote=None,
        tls_cert=None,
        tls_key=None,
        tls_ca=None,
        ssl_config=None,
        openssl_config_file=None,
        require_client_cert=False,
        log_file=None,
        log_level="INFO",
        message_timeout=5.0,
        transaction_timeout=32.0,
        extra_vars=None,
    ):
        logging.basicConfig(
            filename=log_file,
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(message)s",
        )
        self.log = logging.getLogger("SIPStub")

        self.bind = bind
        self.remote = remote
        self.protocol = protocol
        self.scenario_path = scenario_path
        self.scenario_type = scenario_type

        self.rtp_bind = rtp_bind
        self.rtp_remote = rtp_remote

        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.tls_ca = tls_ca
        self.require_client_cert = require_client_cert

        self.message_timeout = message_timeout
        self.transaction_timeout = transaction_timeout
        self.extra_vars = extra_vars or {}

        self.ssl_config = ssl_config
        self.openssl_config_file = openssl_config_file

        self.sip = None
        self.rtp = None
        self.runner = None
        self._stop = threading.Event()
        self.steps = None

    def _apply_ssl_config(self, ctx: ssl.SSLContext) -> None:
        if not self.ssl_config:
            return

        cfg = self.ssl_config.get("ssl_config", {})

        cipher_string = cfg.get("cipher_string")
        if cipher_string:
            ctx.set_ciphers(cipher_string)
            self.log.info("Applied SSL cipher_string: %s", cipher_string)

    def _ssl_contexts(self):
        if self.protocol != "TLS":
            return None, None

        # SERVER context (for incoming)
        server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        if self.ssl_config:
            self._apply_ssl_config(server_ctx)

        if self.tls_cert and self.tls_key:
            server_ctx.load_cert_chain(self.tls_cert, self.tls_key)

        if self.tls_ca:
            server_ctx.load_verify_locations(self.tls_ca)

        if self.require_client_cert:
            server_ctx.verify_mode = ssl.CERT_REQUIRED

        # CLIENT context (for outbound)
        client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        if self.ssl_config:
            self._apply_ssl_config(client_ctx)

        if self.tls_ca:
            client_ctx.load_verify_locations(self.tls_ca)

        client_ctx.check_hostname = False
        client_ctx.verify_mode = ssl.CERT_REQUIRED if self.tls_ca else ssl.CERT_NONE

        return server_ctx, client_ctx

    def run(self):
        self.log.info(
            "Starting SIP %s on %s (remote=%s)", self.protocol, self.bind, self.remote
        )

        server_ctx, client_ctx = self._ssl_contexts()

        self.sip = SIPTransport(
            self.protocol,
            self.bind,
            ssl_context=server_ctx,  # for inbound (LISTEN)
            client_ssl_context=client_ctx,
            log=self.log,
            remote=self.remote,
            openssl_config_file=self.openssl_config_file,
        )
        self.sip.start()

        if self.rtp_bind:
            self.rtp = RTPTransport(self.rtp_bind, log=self.log)
            self.rtp.start()

        vars_init = default_vars(self.bind, self.remote, self.rtp_bind, self.rtp_remote)
        vars_init["transport"] = self.protocol
        vars_init.update(self.extra_vars)

        self.steps = load_sipp_or_yaml(self.scenario_path, self.scenario_type, self.log)

        self.runner = ScenarioRunner(
            sip_transport=self.sip,
            rtp_transport=self.rtp,
            steps=self.steps,
            vars=vars_init,
            log=self.log,
            message_timeout=self.message_timeout,
            transaction_timeout=self.transaction_timeout,
            default_remote=self.remote,
        )

        rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        rx_thread.start()

        self.runner.run()  # blocking until scenario ends
        time.sleep(0.2)
        self.shutdown()

    def _rx_loop(self):
        while not self._stop.is_set():
            data, addr = self.sip.recv(timeout=0.2)
            if not data:
                continue
            try:
                text = data.decode("utf-8", "replace")
            except Exception:
                text = data.decode("latin-1", "replace")
            self.runner.on_incoming(text, addr)

    def shutdown(self):
        if self._stop.is_set():
            return
        self._stop.set()
        if self.rtp:
            try:
                self.rtp.stop()
            except Exception as e:
                print(f"{e}")
        if self.sip:
            self.sip.stop()
        self.log.info("SIP stub stopped.")
