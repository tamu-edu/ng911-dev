# test_suite/unit_tests/test_sip_service/test_sip_transport.py
import socket
import time

from test_suite.services.stub_server.sip_service.sip_transport import SIPTransport


def test_sip_transport_udp_send_recv():
    t = SIPTransport("UDP", ("127.0.0.1", 0))
    t.start()
    local_addr = t.sock.getsockname()

    # Use a raw UDP socket as peer
    peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    peer.bind(("127.0.0.1", 0))
    peer_addr = peer.getsockname()

    # Send from peer to our transport
    peer.sendto(b"hello-udp", local_addr)
    data, addr = t.recv(timeout=0.5)
    assert data == b"hello-udp"
    assert addr[0] == "127.0.0.1"

    # Send back from transport to peer (addr passed explicitly)
    t.send(b"reply-udp", peer_addr)
    peer.settimeout(0.5)
    data2, addr2 = peer.recvfrom(65535)
    assert data2 == b"reply-udp"

    peer.close()
    t.stop()


def test_sip_transport_tcp_listen_and_client_outbound():
    # Server transport
    srv = SIPTransport("TCP", ("127.0.0.1", 0))
    srv.start()
    srv_addr = srv.sock.getsockname()

    # Client transport (outbound)
    cli = SIPTransport("TCP", ("127.0.0.1", 0), remote=srv_addr)
    cli.start()

    # Let the client connect lazily on first send
    cli.send(b"hello-tcp", srv_addr)

    # Server should accept and receive
    time.sleep(0.1)
    data, addr = srv.recv(timeout=0.5)
    assert data == b"hello-tcp"
    assert addr[0] == "127.0.0.1"

    # Now server replies back to client
    srv.send(b"reply-tcp", addr)
    time.sleep(0.1)
    data2, addr2 = cli.recv(timeout=0.5)
    assert data2 == b"reply-tcp"

    cli.stop()
    srv.stop()
