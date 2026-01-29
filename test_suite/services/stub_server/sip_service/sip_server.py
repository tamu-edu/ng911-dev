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
    def __init__(self, bind, remote, protocol,
                 scenario_path, scenario_type="auto",
                 rtp_bind=None, rtp_remote=None,
                 tls_cert=None, tls_key=None, tls_ca=None,
                 require_client_cert=False,
                 log_file=None, log_level="INFO",
                 message_timeout=5.0, transaction_timeout=32.0,
                 extra_vars=None):
        logging.basicConfig(filename=log_file, level=getattr(logging, log_level.upper(), logging.INFO),
                            format="%(asctime)s %(levelname)s %(message)s")
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

        self.sip = None
        self.rtp = None
        self.runner = None
        self._stop = threading.Event()
        self.steps = None

    def _ssl_context(self):
        if self.protocol != "TLS":
            return None
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if self.tls_cert and self.tls_key:
            ctx.load_cert_chain(self.tls_cert, self.tls_key)
        if self.tls_ca:
            ctx.load_verify_locations(self.tls_ca)
        if self.require_client_cert:
            ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    def run(self):
        self.log.info("Starting SIP %s on %s (remote=%s)", self.protocol, self.bind, self.remote)
        self.sip = SIPTransport(
            self.protocol,
            self.bind,
            ssl_context=self._ssl_context(),
            log=self.log,
            remote=self.remote,
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
        if self._stop.is_set(): return
        self._stop.set()
        if self.rtp:
            try:
                self.rtp.stop()
            except Exception as e:
                print(f"{e}")
        if self.sip:
            self.sip.stop()
        self.log.info("SIP stub stopped.")