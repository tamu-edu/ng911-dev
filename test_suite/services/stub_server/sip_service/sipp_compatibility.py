import re
import random  # nosec B311
import string

CRLF = "\r\n"
_BRANCH_CHARS = string.ascii_letters + string.digits
SQVAR_RE = re.compile(r"\[([a-zA-Z0-9_]+)\]")  # [var] → ${var}


def gen_branch():
    return "z9hG4bK" + "".join(random.choice(_BRANCH_CHARS) for _ in range(8))


def enforce_crlf(text: str) -> str:
    """Normalize all line endings to CRLF."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", CRLF)


def split_headers_body(raw_crlf: str):
    """Split SIP message into headers and body."""
    idx = raw_crlf.find(CRLF + CRLF)
    if idx == -1:
        return raw_crlf, ""
    headers = raw_crlf[:idx]
    body = raw_crlf[idx + len(CRLF + CRLF) :]
    return headers, body


def compute_content_length(body: str) -> int:
    return len(body.encode("utf-8"))


def upsert_content_length(headers_block: str, body: str) -> str:
    """Ensure Content-Length is correct and present."""
    cl_val = str(compute_content_length(body))
    lines = headers_block.split(CRLF)
    found = False
    for i, line in enumerate(lines):
        if re.match(r"(?i)^Content-Length\s*:", line):
            prefix, _, _ = line.partition(":")
            lines[i] = f"{prefix}: {cl_val}"
            found = True
            break
    if not found:
        lines.append(f"Content-Length: {cl_val}")
    return CRLF.join(lines)


def fix_transport_tokens(msg: str, transport_token: str) -> str:
    """Replace transport placeholders like ${transport}."""
    t = (transport_token or "UDP").upper()
    msg = msg.replace("SIP/2.0/${transport}", f"SIP/2.0/{t}")
    msg = msg.replace("/${transport} ", f"/{t} ")
    return msg


def _fallback_square_vars_to_dollar(text: str) -> str:
    """Convert [var] and [$var] → ${var} if loader missed conversion."""
    # First, replace [$var] -> ${var}
    text = re.sub(r"\[\$([a-zA-Z0-9_]+)\]", lambda m: "${" + m.group(1) + "}", text)
    # Then, replace [var] -> ${var}
    text = re.sub(r"\[([a-zA-Z0-9_]+)\]", lambda m: "${" + m.group(1) + "}", text)
    return text


def _pick_target_hostport(vars_dict: dict) -> str:
    ip = (
        vars_dict.get("peer_ip")
        or vars_dict.get("remote_ip")
        or vars_dict.get("local_ip")
        or "127.0.0.1"
    )
    port = (
        vars_dict.get("peer_port")
        or vars_dict.get("remote_port")
        or vars_dict.get("local_port")
        or ""
    )
    return f"{ip}:{port}" if port else ip


def _normalize_request_uri(start_line: str, vars_dict: dict) -> str:
    """Keep valid URIs; optionally convert non-SIP URIs to sip:<ip[:port]> if forced.
    By default we DO NOT rewrite URN (urn:service:...), because many tests expect it.
    Set vars_dict["__force_sip_uri"]=True to force conversion of non-sip URIs.
    """
    m = re.match(r"^([A-Z]+)\s+(\S+)\s+SIP/2\.0", start_line)
    if not m:
        return start_line
    method, uri = m.groups()
    uri_l = uri.lower()

    # Always keep standard schemes as-is (esp. URN)
    if uri_l.startswith(("sip:", "sips:", "tel:", "urn:")):
        return start_line

    # Only convert when explicitly forced
    if not vars_dict.get("__force_sip_uri"):
        return start_line

    target = _pick_target_hostport(vars_dict)
    return f"{method} sip:{target} SIP/2.0"


def _normalize_start_line_and_ruri(rendered: str, vars_dict: dict) -> str:
    """Ensure SIP request start-line is valid; do NOT alter responses."""
    first_end = rendered.find(CRLF)
    first_line = rendered if first_end == -1 else rendered[:first_end]
    # Do not touch response lines
    if first_line.startswith("SIP/2.0"):
        return rendered
    fixed_first = _normalize_request_uri(first_line, vars_dict)
    if fixed_first == first_line:
        return rendered
    return fixed_first + (rendered[first_end:] if first_end != -1 else "")


def render_sipp_like(template_text: str, vars_dict: dict) -> bytes:
    """
    Render SIP message like SIPp:
    - Substitute variables
    - Normalize CRLF
    - Fix Request-URI if needed
    - Ensure each header ends with CRLF
    - Auto insert Call-ID if missing
    - Fix Content-Length
    """
    # Convert [var] → ${var}
    template_text = _fallback_square_vars_to_dollar(template_text)

    # Generate ${branch} if needed
    if "${branch}" in template_text and "branch" not in vars_dict:
        vars_dict = dict(vars_dict)
        vars_dict["branch"] = gen_branch()

    # Substitute ${var}
    def subst(m):
        return str(vars_dict.get(m.group(1), ""))

    rendered = re.sub(r"\$\{([a-zA-Z0-9_]+)\}", subst, template_text)

    # Replace transport tokens
    rendered = fix_transport_tokens(rendered, str(vars_dict.get("transport")))

    # Normalize CRLF
    rendered = enforce_crlf(rendered)

    # Fix request line
    rendered = _normalize_start_line_and_ruri(rendered, vars_dict)

    # Split headers and body
    headers, body = split_headers_body(rendered)

    # Ensure every header line ends with CRLF correctly
    headers_lines = [line.strip() for line in headers.split(CRLF) if line.strip()]
    headers = CRLF.join(headers_lines)

    # Add Call-ID if missing
    if not re.search(r"(?im)^Call-ID\s*:", headers):
        call_id = (
            vars_dict.get("call_id")
            or f"{''.join(random.choices(string.ascii_letters + string.digits, k=10))}@{vars_dict.get('local_ip', 'stub')}"
        )
        headers += f"{CRLF}Call-ID: {call_id}"

    # Update Content-Length
    headers = upsert_content_length(headers, body)

    # Reassemble message
    out = headers + CRLF + CRLF + body

    # Ensure ending CRLF CRLF if no body
    if not out.endswith(CRLF + CRLF) and body == "":
        out = out + CRLF + CRLF

    return out.encode("utf-8")
