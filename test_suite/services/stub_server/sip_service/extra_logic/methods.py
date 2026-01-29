import os

from .utils import *


def forward_message(message: str, ctx: dict) -> str:
    return message


def rewrite_invite_for_bcf(invite_text: str, ctx: dict) -> str:
    if not invite_text:
        ctx["log"].info("[methods] SIP INVITE text for BCF rewriting not found")
        return ""
    out = invite_text
    vars = {
        "BCF_FQDN": ctx.get("vars", {}).get("BCF_FQDN", "bcf.example.com"),
        "ESRP_FQDN": ctx.get("vars", {}).get("ESRP_FQDN", "esrp.example.com"),
    }

    actions = [
        (replace_header_field_value, out, "Request_URI", "urn:service:sos"),
        (replace_header_field_value, out, "To", "urn:service:sos"),
        (add_header_field, out, "Route", f"<{vars['ESRP_FQDN']}>;lr"),
        (add_header_field, out, "Via", f"<{vars['BCF_FQDN']}>;lr"),
        (add_or_replace_header_field, out, "Contact", f"<bcf@{vars['BCF_FQDN']}>"),
        (add_header_field_if_not_exist, out, "Call-Info", generate_identifier("callid", vars['BCF_FQDN']),
         {"purpose": "emergency-CallId"}, ':callid:'),
        (add_header_field_if_not_exist, out, "Call-Info", generate_identifier("incidentid", vars['BCF_FQDN']),
         {"purpose": "emergency-IncidentId"}, ':incidentid:'),
        (add_header_field_if_not_exist, out, "Resource-Priority", "esnet.1")
    ]
    for action in actions:
        out = action[0](out,*action[2:])
    return out


def rewrite_invite_for_esrp(invite_text: str, ctx: dict) -> str:
    if not invite_text:
        ctx["log"].info("[methods] SIP INVITE text for ESRP rewriting not found")
        return ""

    out = invite_text
    ctx_vars = {
        "BCF_FQDN": ctx.get("vars", {}).get("BCF_FQDN", "bcf.example.com"),
        "ESRP_FQDN": ctx.get("vars", {}).get("ESRP_FQDN", "esrp.example.com"),
        "CHE_FQDN": ctx.get("vars", {}).get("CHE_FQDN", "che.example.com"),
        "CHE_tel": ctx.get("vars", {}).get("CHE_tel", "+10987654321"),
    }
    repo_path = os.path.abspath(__file__).split("test_suite/")[0]
    default_location_xml_file_path = (repo_path.removesuffix("/") +
                                      "/test_suite/test_files/HTTP_messages/HTTP_HELD/Default_location")
    try:
        with open(default_location_xml_file_path, "r", encoding="utf-8") as f:
            default_location_xml = f.read()
    except Exception as e:
        ctx["log"].info(f"[methods] Error opening a file: {default_location_xml_file_path}, "
                        f"setting default location XML to None")
        default_location_xml = ""

    actions = [
        (replace_header_field_value, out, "Request_URI", "urn:service:sos"),
        (replace_header_field_value, out, "To", "urn:service:sos"),
        (add_header_field, out, "Route", f"<sip:{ctx_vars['CHE_tel']}@{ctx_vars['CHE_FQDN']}>;lr"),
        (add_header_field, out, "Via", f"<{ctx_vars['ESRP_FQDN']}>;lr"),
        (add_or_replace_header_field, out, "Contact", f"<esrp@{ctx_vars['ESRP_FQDN']}>"),
        (add_header_field_if_not_exist, out, "Call-Info",
         generate_identifier("callid", ctx_vars['ESRP_FQDN']), {"purpose": "emergency-CallId"}, ":callid:"),
        (add_header_field_if_not_exist, out, "Call-Info",
         generate_identifier("incidentid", ctx_vars['ESRP_FQDN']), {"purpose": "emergency-IncidentId"},
         ":incidentid:"),
        (add_header_field_if_not_exist, out, "Resource-Priority", "esnet.1"),
        (add_message_body_if_not_exist, out, "application/pidf+xml", default_location_xml)
    ]
    for action in actions:
        out = action[0](out,*action[2:])
    return out


def rewrite_invite_for_esrp_add_conference_id(invite_text: str, ctx: dict) -> str:
    out = rewrite_invite_for_esrp(invite_text, ctx)
    ctx_vars = {
        "conference_id": ctx.get("vars", {}).get("conference_id", "conferenceng911test123"),
        "ESRP_FQDN": ctx.get("vars", {}).get("ESRP_FQDN", "esrp.example.com")
    }
    return add_or_replace_header_field(out, "Contact",
                                       f"{ctx_vars['conference_id']}@{ctx_vars['ESRP_FQDN']};isfocus")


def save(message_text: str, ctx: dict) -> str:
    """
    Save whole incoming message into ctx["vars"][<ctx_key>] for later use.
    <operate method_name="save" ctx_key="INVITE_FROM_BCF" />
    """
    params = ctx.get("operate", {}).get("params", {})
    key = params.get("ctx_key", "LAST_MESSAGE")
    ctx["vars"][key] = message_text
    ctx["log"].info("[methods.save] stored message under vars[%r]", key)
    # usually just return original message text (or something else if needed)
    return message_text


def save_header_field(message_text: str, ctx: dict) -> str:
    """
    Saves specified header field from incoming message into ctx["vars"][<ctx_key>] for later use. Example:
    <operate
        method_name="save_header_field"
        header_field_name="To"
        ctx_key="last_To"
    />
    """
    params = ctx.get("operate", {}).get("params", {})
    key = params.get("ctx_key", "LAST_MESSAGE")
    header_field_name = params.get("header_field_name")
    for line in message_text.splitlines():
        if header_field_name.lower() in line.lower():
            ctx["vars"][key] = line
    return message_text


def save_header_field_value(message_text: str, ctx: dict) -> str:
    """
    Saves value of specified header field from incoming message into ctx["vars"][<ctx_key>] for later use. Example:
    <operate
        method_name="save_header_field_value"
        header_field_name="Call-ID:"
        ctx_key="CALL_ID"
    />
    """
    params = ctx.get("operate", {}).get("params", {})
    key = params.get("ctx_key", "LAST_MESSAGE")
    header_field_name = params.get("header_field_name")
    for line in message_text.splitlines():
        if header_field_name.lower() in line.lower():
            ctx["vars"][key] = line.split(": ")[1]
    return message_text


def substitute(message_text: str, ctx: dict) -> str:
    """
    Example:
    <operate
        method_name="substitute"
        line_to_substitute="Contact:"
        value_from_ctx="INVITE_FROM_BCF"
        key_1="foo"
        key_2="bar"
    />
    """
    p = ctx.get("operate", {}).get("params", {})
    line_prefix = p.get("line_to_substitute", "")
    from_ctx_key = p.get("value_from_ctx")

    if not line_prefix or not from_ctx_key:
        return message_text

    stored = ctx["vars"].get(from_ctx_key, "")
    if not stored:
        return message_text

    # very simple example: replace the whole line that starts with line_prefix
    lines = message_text.split("\r\n")
    new_lines = []
    for line in lines:
        if line.startswith(line_prefix):
            # here you can build whatever you want from `stored` + p["key_1"] etc.
            new_lines.append(f"{line_prefix} {stored}")
        else:
            new_lines.append(line)
    return "\r\n".join(new_lines)


def prepare_invite(message_text: str, ctx: dict) -> str:
    """EXAMPLE"""
    params = ctx.get("operate", {}).get("params", {})
    key = params.get("ctx_key")

    # any custom logic: log, tweak headers, inject smth from ctx["vars"], etc.
    ctx["log"].info("[prepare_invite] called with ctx_key=%r", key)

    # example: replace a marker in body using some vars
    body_key = params.get("body_from_var")
    if body_key and body_key in ctx["vars"]:
        marker = "${BODY_FROM_VAR}"
        message_text = message_text.replace(marker, ctx["vars"][body_key])

    return message_text


def replace_string(message_text: str, ctx: dict) -> str:
    if not message_text:
        ctx["log"].info("[methods] Message text for replacing string not found")
        return ""
    replace_from = ctx.get('operate', {}).get('params', {}).get('replace_from', {})
    replace_to = ctx.get('operate', {}).get('params', {}).get('replace_to', {})
    if (not isinstance(replace_from, str)
            or not isinstance(replace_to, str)
            or not replace_from
            or not replace_to):
        ctx["log"].info("[methods] Some of string params for replacing in message are missing")
        return ""
    return message_text.replace(replace_from,replace_to)