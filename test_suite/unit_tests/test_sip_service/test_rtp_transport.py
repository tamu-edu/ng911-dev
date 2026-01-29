# test_suite/unit_tests/test_sip_service/test_rtp_transport.py
import socket
import time

from test_suite.services.stub_server.sip_service.rtp_transport import RTPTransport


def test_rtp_transport_bind_and_send_recv_udp():
    # Bind two RTP transports on localhost with ephemeral ports
    rtp_a = RTPTransport(("127.0.0.1", 0))
    rtp_b = RTPTransport(("127.0.0.1", 0))

    rtp_a.start()
    rtp_b.start()

    addr_b = rtp_b.sock.getsockname()

    received = {}

    def cb(data, addr):
        # store received for assertion
        received["data"] = data
        received["addr"] = addr

    rtp_b.recv_loop(cb, timeout=0.1)

    payload = b"hello-rtp"
    rtp_a.send_raw(payload, addr_b)

    # Give some time for recv_loop
    time.sleep(0.2)

    rtp_a.stop()
    rtp_b.stop()

    assert received.get("data") == payload
    assert received.get("addr")[0] == "127.0.0.1"


def test_rtp_transport_send_dummy_stream_does_not_crash():
    rtp = RTPTransport(("127.0.0.1", 0))
    rtp.start()
    remote = ("127.0.0.1", 9999)

    # Should not raise
    rtp.send_dummy_stream(remote, duration_sec=0.1, interval_sec=0.02)
    rtp.stop()
