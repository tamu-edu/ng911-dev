# test_suite/unit_tests/test_sip_service/test_sipp_compatibility.py
import re

from test_suite.services.stub_server.sip_service.sipp_compatibility import (
    render_sipp_like,
    enforce_crlf,
    split_headers_body,
    upsert_content_length,
)


def test_enforce_crlf_normalizes_newlines():
    src = "A\nB\r\nC\rD"
    out = enforce_crlf(src)
    assert out.count("\r\n") == 3
    assert "\n" not in out.replace("\r\n", "")


def test_split_headers_body_no_body():
    text = "INVITE sip:x SIP/2.0\r\nHeader: 1\r\n\r\n"
    headers, body = split_headers_body(text)
    assert "INVITE sip:x" in headers
    assert body == ""


def test_upsert_content_length_add_and_update():
    headers = "INVITE sip:x SIP/2.0\r\nHeader: 1"
    body = "payload"
    updated = upsert_content_length(headers, body)
    assert re.search(r"(?im)^Content-Length\s*:\s*7\b", updated)

    # Update existing
    headers2 = "INVITE sip:x SIP/2.0\r\nContent-Length: 999"
    updated2 = upsert_content_length(headers2, body)
    assert re.search(r"(?im)^Content-Length\s*:\s*7\b", updated2)


def test_render_sipp_like_substitution_and_call_id_and_transport():
    template = (
        "INVITE sip:test SIP/2.0\r\n"
        "Via: SIP/2.0/[transport] [local_ip]:[local_port]\r\n"
        "From: <sip:user@[local_ip]>;tag=[call_number]\r\n"
        "Content-Length: 999\r\n"
        "\r\n"
        "BODY"
    )
    vars_dict = {
        "local_ip": "1.2.3.4",
        "local_port": "5060",
        "transport": "TCP",
        "call_number": "ABC",
        "call_id": "CID@1.2.3.4",
    }
    out = render_sipp_like(template, vars_dict).decode("utf-8")
    # Check transport and ip substitution happened (via loader we map to ${})
    assert "Via: SIP/2.0/TCP 1.2.3.4:5060" in out
    # Call-ID must be present
    assert re.search(r"(?im)^Call-ID\s*:\s*CID@1\.2\.3\.4\b", out)
    # Content-Length must match the body length
    assert re.search(r"(?im)^Content-Length\s*:\s*4\b", out)
