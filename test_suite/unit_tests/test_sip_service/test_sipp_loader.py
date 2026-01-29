import textwrap
from pathlib import Path

import pytest

from test_suite.services.stub_server.sip_service.sipp_loader import (
    load_sipp_or_yaml,
    _map_sipp_vars_to_tpl,
)


class DummyLog:
    """Simple logger stub used in tests."""
    def __init__(self):
        self.infos = []
        self.warnings = []

    def info(self, msg, *args):
        self.infos.append(msg % args if args else msg)

    def warning(self, msg, *args):
        self.warnings.append(msg % args if args else msg)


# ---------------------------------------------------------------------------
# Unit tests for _map_sipp_vars_to_tpl
# ---------------------------------------------------------------------------

def test_map_sipp_vars_to_tpl_basic():
    src = "Via: SIP/2.0/[transport] [local_ip]:[local_port]"
    out = _map_sipp_vars_to_tpl(src)
    assert "Via: SIP/2.0/${transport} ${local_ip}:${local_port}" in out


def test_map_sipp_vars_to_tpl_with_dollar():
    src = "To: urn:service:sos:[$IF_OSP_BCF]@bcf.edu"
    out = _map_sipp_vars_to_tpl(src)
    # Unknown SIPp var names should be preserved as-is in ${NAME}
    assert "urn:service:sos:${IF_OSP_BCF}@bcf.edu" in out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_xml(tmp_path: Path, body: str) -> Path:
    xml = textwrap.dedent(body).lstrip()
    p = tmp_path / "scenario.xml"
    p.write_text(xml, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# XML (SIPp) scenario tests
# ---------------------------------------------------------------------------

def test_load_send_single_message(tmp_path):
    """
    <send> with a single SIP message in CDATA should produce one 'send' step.
    """
    path = _write_xml(
        tmp_path,
        """\
        <?xml version="1.0" encoding="ISO-8859-1" ?>
        <scenario name="single_send">
          <send>
            <![CDATA[
INVITE sip:[remote_ip]:[remote_port] SIP/2.0
Via: SIP/2.0/[transport] [local_ip]:[local_port]
            ]]>
          </send>
        </scenario>
        """,
    )
    log = DummyLog()
    steps = load_sipp_or_yaml(str(path), "sipp", log=log)

    assert len(steps) == 1
    step = steps[0]
    assert step["type"] == "send"
    assert "INVITE sip:${remote_ip}:${remote_port} SIP/2.0" in step["message"]
    assert "Via: SIP/2.0/${transport} ${local_ip}:${local_port}" in step["message"]


def test_load_send_with_multiple_messages(tmp_path):
    """
    CDATA containing multiple SIP start lines (no indentation) should be split
    into multiple 'send' steps.
    """
    path = _write_xml(
        tmp_path,
        """\
        <?xml version="1.0" encoding="ISO-8859-1" ?>
        <scenario name="multi_send">
          <send><![CDATA[
INVITE sip:a@example.com SIP/2.0
Via: SIP/2.0/UDP 1.1.1.1:5060

ACK sip:a@example.com SIP/2.0
Via: SIP/2.0/UDP 1.1.1.1:5060
]]></send>
        </scenario>
        """,
    )
    log = DummyLog()
    steps = load_sipp_or_yaml(str(path), "sipp", log=log)

    # Two SIP start lines -> two send steps according to _split_multi_messages
    assert len(steps) == 2
    assert steps[0]["type"] == "send"
    assert steps[1]["type"] == "send"
    assert steps[0]["message"].startswith("INVITE")
    assert steps[1]["message"].startswith("ACK")


def test_load_recv_with_response_and_ereg_and_operate(tmp_path):
    """
    <recv> with response, <action><ereg ...>, and <operate> should be converted into
    a single 'await' step with match/extract and 'operate' preserved.

    NOTE: current implementation supports multiple <operate>, so step["operate"]
    is a list of dicts.
    """
    path = _write_xml(
        tmp_path,
        """\
        <?xml version="1.0" encoding="ISO-8859-1" ?>
        <scenario name="recv_with_operate">
          <recv response="200">
            <action>
              <ereg regexp="To: .*;tag=([0-9A-Za-z]+)" assign="to_tag"/>
            </action>
            <operate
              method_name="test_append_header"
              src_ip="[local_ip]"
              dst_ip="[$IF_ESRP_BCF]"
              dst_port="5060"
              auto_200_ok="false"
            />
          </recv>
        </scenario>
        """,
    )
    log = DummyLog()
    steps = load_sipp_or_yaml(str(path), "sipp", log=log)

    assert len(steps) == 1
    step = steps[0]

    # Basic type and matching
    assert step["type"] == "await"
    assert step["match"]["startswith"] == "SIP/2.0 200"

    # Extract (ereg) mapping
    assert "extract" in step
    assert step["extract"]["to_tag"] == "To: .*;tag=([0-9A-Za-z]+)"

    # Operate block: expect list of operations
    operate_list = step.get("operate")
    assert isinstance(operate_list, list)
    assert len(operate_list) == 1

    op = operate_list[0]
    assert op["method"] == "test_append_header"

    # src_ip/dst_ip/dst_port go through _map_sipp_vars_to_tpl
    assert op["src_ip"] == "${local_ip}"
    assert op["dst_ip"] == "${IF_ESRP_BCF}"
    assert op["dst_port"] == "5060"
    assert op["auto_200_ok"] is False


def test_load_pause_nop_and_goto(tmp_path):
    """
    <pause>, <nop>, and <goto> should become sleep/jump steps.
    """
    path = _write_xml(
        tmp_path,
        """\
        <?xml version="1.0" encoding="ISO-8859-1" ?>
        <scenario name="timing_and_flow">
          <pause milliseconds="250"/>
          <nop/>
          <label id="L1"/>
          <goto ref="L1"/>
        </scenario>
        """,
    )
    log = DummyLog()
    steps = load_sipp_or_yaml(str(path), "sipp", log=log)

    # pause
    assert steps[0]["type"] == "sleep"
    assert steps[0]["seconds"] == 0.25
    # nop
    assert steps[1]["type"] == "sleep"
    assert steps[1]["seconds"] == 0
    # label + jump
    assert steps[2]["type"] == "label"
    assert steps[2]["id"] == "L1"
    assert steps[3]["type"] == "jump"
    assert steps[3]["target"] == "L1"


def test_load_set_variable_step(tmp_path):
    """
    <Set variable="X" value="Y"/> should become a 'vars' step with mapped value.
    """
    path = _write_xml(
        tmp_path,
        """\
        <?xml version="1.0" encoding="ISO-8859-1" ?>
        <scenario name="set_var">
          <Set variable="INVITE_TARGET" value="sip:[remote_ip]:[remote_port]"/>
        </scenario>
        """,
    )
    log = DummyLog()
    steps = load_sipp_or_yaml(str(path), "sipp", log=log)

    assert len(steps) == 1
    step = steps[0]
    assert step["type"] == "vars"
    assert "set" in step
    assert "INVITE_TARGET" in step["set"]
    val = step["set"]["INVITE_TARGET"]
    assert "${remote_ip}" in val
    assert "${remote_port}" in val


def test_global_only_logs_and_not_add_steps(tmp_path):
    """
    <Global ...> should log var names but not create any 'vars' step.
    """
    path = _write_xml(
        tmp_path,
        """\
        <?xml version="1.0" encoding="ISO-8859-1" ?>
        <scenario name="globals_only">
          <Global variables="BCF_FQDN, ESRP_FQDN, IF_OSP_BCF, IF_ESRP_BCF"/>
        </scenario>
        """,
    )
    log = DummyLog()
    steps = load_sipp_or_yaml(str(path), "sipp", log=log)

    assert steps == []  # no steps generated
    # But logger should have info about parsed globals
    assert any("Parsed Global vars" in msg for msg in log.infos)


# ---------------------------------------------------------------------------
# YAML auto-detection and passthrough
# ---------------------------------------------------------------------------

def test_auto_type_detection_yaml(tmp_path):
    """
    When scenario_type='auto' and extension is not '.xml', loader should treat it as YAML.
    """
    yaml_path = tmp_path / "scenario.yaml"
    yaml_path.write_text(
        textwrap.dedent(
            """\
            - type: send
              message: "HELLO"
            - type: sleep
              seconds: 0.5
            """
        ),
        encoding="utf-8",
    )
    log = DummyLog()
    steps = load_sipp_or_yaml(str(yaml_path), "auto", log=log)

    assert len(steps) == 2
    assert steps[0]["type"] == "send"
    assert steps[0]["message"] == "HELLO"
    assert steps[1]["type"] == "sleep"
    assert steps[1]["seconds"] == 0.5


def test_auto_type_detection_xml(tmp_path):
    """
    When scenario_type='auto' and extension is '.xml', loader should treat it as SIPp XML.
    """
    path = _write_xml(
        tmp_path,
        """\
        <?xml version="1.0" encoding="ISO-8859-1" ?>
        <scenario name="auto_xml">
          <send>
            <![CDATA[
INVITE sip:a@example.com SIP/2.0
            ]]>
          </send>
        </scenario>
        """,
    )
    log = DummyLog()
    steps = load_sipp_or_yaml(str(path), "auto", log=log)

    assert len(steps) == 1
    assert steps[0]["type"] == "send"
    assert "INVITE sip:a@example.com SIP/2.0" in steps[0]["message"]
