# test_suite/unit_tests/test_sip_service/test_sdp_utils.py
from test_suite.services.stub_server.sip_service.sdp_utils import (
    parse_sdp_connection_and_audio_port,
)


def test_parse_sdp_connection_and_audio_port_basic():
    sdp = "\r\n".join(
        [
            "v=0",
            "o=user1 1 1 IN IP4 10.0.0.1",
            "s=-",
            "t=0 0",
            "c=IN IP4 10.0.0.1",
            "m=audio 5004 RTP/AVP 0",
        ]
    )
    ip, port = parse_sdp_connection_and_audio_port(sdp)
    assert ip == "10.0.0.1"
    assert port == 5004


def test_parse_sdp_no_c_line():
    sdp = "\r\n".join(
        [
            "v=0",
            "o=user1 1 1 IN IP4 10.0.0.1",
            "s=-",
            "t=0 0",
            "m=audio 5004 RTP/AVP 0",
        ]
    )
    ip, port = parse_sdp_connection_and_audio_port(sdp)
    assert ip is None
    assert port == 5004


def test_parse_sdp_invalid():
    ip, port = parse_sdp_connection_and_audio_port("")
    assert ip is None
    assert port is None
