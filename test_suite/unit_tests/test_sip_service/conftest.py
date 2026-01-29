import os
import sys
import socket
import pytest

# Ensure sip_service modules are importable
HERE = os.path.dirname(__file__)
SIP_SERVICE_ROOT = os.path.abspath(
    os.path.join(HERE, "..", "..", "services", "stub_server", "sip_service")
)

if SIP_SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SIP_SERVICE_ROOT)


@pytest.fixture
def free_udp_port():
    """Return an available UDP port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def free_tcp_port():
    """Return an available TCP port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port
