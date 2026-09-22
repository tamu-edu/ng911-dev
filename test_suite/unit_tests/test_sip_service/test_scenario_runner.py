# test_suite/unit_tests/test_sip_service/test_scenario_runner.py
from test_suite.services.stub_server.sip_service.scenario_runner import ScenarioRunner
import test_suite.services.stub_server.sip_service.scenario_runner as sr_mod


class DummySip:
    """Minimal SIP transport stub used for ScenarioRunner tests."""

    def __init__(self):
        self.protocol = "UDP"
        self.bind = ("127.0.0.1", 5060)
        self.sent = []

    def send(self, data: bytes, addr):
        self.sent.append((data, addr))


class DummyRtp:
    """Minimal RTP transport stub used for RTP-related steps."""

    def __init__(self):
        self.recv_started = False
        self.sent = []

    def recv_loop(self, cb, timeout=0.2):
        self.recv_started = True
        self._cb = cb

    def send_raw(self, payload: bytes, remote):
        self.sent.append((payload, remote))


class DummyLog:
    """Very small logger stub; methods just swallow messages."""

    def __getattr__(self, name):
        def _(*args, **kwargs):
            pass

        return _


def test_scenario_runner_vars_and_send():
    """
    Scenario:
      - set FOO = BAR via 'vars' step
      - send INVITE with ${FOO} in header
    Expect:
      - one SIP send
      - header after rendering contains 'Foo: BAR'
      - send goes to default_remote
    """
    steps = [
        {"type": "vars", "set": {"FOO": "BAR"}},
        {
            "type": "send",
            "message": (
                "INVITE sip:alice@example.com SIP/2.0\r\n"
                "Foo: ${FOO}\r\n"
                "Content-Length: 0\r\n\r\n"
            ),
        },
    ]

    sip = DummySip()
    log = DummyLog()
    vars_init = {
        "local_ip": "127.0.0.1",
        "local_port": "5060",
        "transport": "UDP",
    }

    runner = ScenarioRunner(
        sip_transport=sip,
        rtp_transport=None,
        steps=steps,
        vars=vars_init,
        log=log,
        message_timeout=1.0,
        transaction_timeout=32.0,
        default_remote=("1.2.3.4", 5060),
    )

    runner.run()

    assert len(sip.sent) == 1
    data, addr = sip.sent[0]
    text = data.decode("utf-8", "replace")
    assert "Foo: BAR" in text
    assert addr == ("1.2.3.4", 5060)


def test_scenario_runner_await_and_operate(monkeypatch):
    """
    Scenario:
      - inbox already has one INVITE
      - step 'await' with match 'INVITE ' and an <operate>-like dict
      - operate method appends custom header
    Expect:
      - runner consumes message from inbox
      - operate is invoked and sends modified message once
    """

    # Dummy operate function that appends header
    def test_op(in_text: str, ctx: dict) -> str:
        return in_text.rstrip("\r\n") + "\r\nX-Operated: 1\r\n\r\n"

    # Monkeypatch load_callable inside scenario_runner to use our dummy
    monkeypatch.setattr(sr_mod, "load_callable", lambda name: test_op)

    steps = [
        {
            "type": "await",
            "match": {"startswith": "INVITE "},
            "operate": {
                "method": "test_op",
                "src_ip": "",
                "dst_ip": "",
                "dst_port": "5060",
                "auto_200_ok": False,
                "send_back": True,  # <---- MUST BE ADDED
            },
        }
    ]

    sip = DummySip()
    log = DummyLog()
    vars_init = {
        "local_ip": "127.0.0.1",
        "local_port": "5060",
        "transport": "UDP",
    }

    runner = ScenarioRunner(
        sip_transport=sip,
        rtp_transport=None,
        steps=steps,
        vars=vars_init,
        log=log,
        message_timeout=1.0,
        transaction_timeout=32.0,
        default_remote=None,
    )

    # Pre-populate inbox with one INVITE from peer
    runner.inbox.append(
        ("INVITE sip:test@example.com SIP/2.0\r\n\r\n", ("10.0.0.5", 5060))
    )

    runner.run()

    # We expect operate to send exactly one message back to source address
    assert len(sip.sent) == 1
    data, addr = sip.sent[0]
    text = data.decode("utf-8", "replace")
    assert "X-Operated: 1" in text
    assert addr == ("10.0.0.5", 5060)


def test_scenario_runner_rtp_send_and_recv_start():
    """
    Scenario:
      - start RTP receive loop (rtp_recv_start)
      - send one RTP packet using rtp_send with payload_hex
    Expect:
      - recv_loop called
      - send_raw called with decoded payload and correct remote from vars
    """
    steps = [
        {"type": "rtp_recv_start"},
        {"type": "rtp_send", "payload_hex": "414243"},  # "ABC"
    ]

    sip = DummySip()
    rtp = DummyRtp()
    log = DummyLog()
    vars_init = {
        "local_ip": "127.0.0.1",
        "local_port": "5060",
        "rtp_remote_ip": "10.0.0.2",
        "rtp_remote_port": "4000",
        "transport": "UDP",
    }

    runner = ScenarioRunner(
        sip_transport=sip,
        rtp_transport=rtp,
        steps=steps,
        vars=vars_init,
        log=log,
        message_timeout=1.0,
        transaction_timeout=32.0,
        default_remote=None,
    )

    runner.run()

    assert rtp.recv_started is True
    assert len(rtp.sent) == 1
    payload, remote = rtp.sent[0]
    assert payload == b"ABC"
    assert remote == ("10.0.0.2", 4000)


def test_scenario_runner_await_with_asserts():
    """
    Scenario:
      - inbox has one 200 OK with 'HELLO 123' inside
      - await step matches 'SIP/2.0 200'
      - asserts:
          contains: HELLO
          regex: HELLO 123
    Expect:
      - run completes without raising AssertionError
    """
    steps = [
        {
            "type": "await",
            "match": {"startswith": "SIP/2.0 200"},
            "assert": [
                {"contains": "HELLO"},
                {"regex": r"HELLO 123"},
            ],
        }
    ]

    sip = DummySip()
    log = DummyLog()
    vars_init = {
        "local_ip": "127.0.0.1",
        "local_port": "5060",
        "transport": "UDP",
    }

    runner = ScenarioRunner(
        sip_transport=sip,
        rtp_transport=None,
        steps=steps,
        vars=vars_init,
        log=log,
        message_timeout=1.0,
        transaction_timeout=32.0,
        default_remote=None,
    )

    msg = "SIP/2.0 200 OK\r\n" "X-Body: HELLO 123\r\n" "Content-Length: 0\r\n\r\n"
    runner.inbox.append((msg, ("10.0.0.5", 5060)))

    # Should not raise
    runner.run()
