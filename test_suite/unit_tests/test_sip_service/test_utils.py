# test_suite/unit_tests/test_sip_service/test_utils.py
from test_suite.services.stub_server.sip_service.utils import (
    gen_call_id,
    gen_tag,
    default_vars,
)


def test_gen_call_id_contains_ip():
    cid = gen_call_id("1.2.3.4")
    assert "@1.2.3.4" in cid


def test_gen_tag_length():
    tag = gen_tag()
    assert len(tag) == 8


def test_default_vars_structure():
    bind = ("1.2.3.4", 5060)
    remote = ("5.6.7.8", 5080)
    rtp_bind = ("1.2.3.4", 4000)
    rtp_remote = ("5.6.7.8", 5000)

    v = default_vars(bind, remote, rtp_bind, rtp_remote)
    assert v["local_ip"] == "1.2.3.4"
    assert v["local_port"] == "5060"
    assert v["remote_ip"] == "5.6.7.8"
    assert v["remote_port"] == "5080"
    assert v["rtp_local_ip"] == "1.2.3.4"
    assert v["rtp_local_port"] == "4000"
    assert v["rtp_remote_ip"] == "5.6.7.8"
    assert v["rtp_remote_port"] == "5000"
    assert v["transport"] == ""
