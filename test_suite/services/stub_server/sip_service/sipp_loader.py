import os
import re
import xml.etree.ElementTree as ElTree
from typing import Any

import yaml
import textwrap

SIP_START_RE = re.compile(
    r"^(?:"
    r"(INVITE|ACK|BYE|CANCEL|REGISTER|OPTIONS|SUBSCRIBE|NOTIFY|MESSAGE|UPDATE|INFO|PRACK)\s+.+?"
    r"|SIP/2\.0\s+\d{3}\b"
    r")",
    re.M,
)

# SIPp -> our ${var} mapping
VAR_MAP = {
    "local_ip": "local_ip",
    "local_port": "local_port",
    "remote_ip": "remote_ip",
    "remote_port": "remote_port",
    "transport": "transport",
    "call_id": "call_id",
    "call_number": "call_number",  # we will set equal to from_tag by default
    "branch": "branch",
    # special:
    "peer_tag_param": "peer_tag_param",  # becomes ";tag=${to_tag}" or ""
}


def _map_sipp_vars_to_tpl(text: str) -> str:
    """
    Replace [var] -> ${var} and [$var] -> ${var}, keeping unknown names intact.
    Normalize line endings to CRLF.
    """

    def repl(m):
        name = m.group(1)
        key = VAR_MAP.get(name, name)
        return "${" + key + "}"

    # Handle [var]
    out = re.sub(r"\[([a-zA-Z0-9_]+)\]", repl, text)
    # Handle [$var]
    out = re.sub(r"\[\$([a-zA-Z0-9_]+)\]", repl, out)

    # Normalize line endings
    out = out.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    return out


def _split_multi_messages(cdata: str) -> list[str]:
    """
    If CDATA contains more than one SIP start line (e.g. INVITE... then ACK...),
    split it into separate messages, preserving CRLFs.
    """
    text = cdata.strip()
    if not text:
        return []
    starts = [m.start() for m in SIP_START_RE.finditer(text)]
    if not starts or len(starts) == 1:
        return [text]
    chunks = []
    for i, pos in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        chunk = text[pos:end].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def load_sipp_or_yaml(path: str, scenario_type: str, log=None):
    """
    Load YAML or SIPp XML into an internal list of step dicts.
    Backward-compatible. Adds <operate .../> support under <recv ...>.
    """
    typ = scenario_type
    if typ == "auto":
        ext = os.path.splitext(path)[1].lower()
        typ = "sipp" if ext == ".xml" else "yaml"

    if typ == "yaml":
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []

    # --- SIPp XML ---
    steps: list[dict[str, Any]] = []
    label_index = (
        {}
    )  # label id -> future step index placeholder list (kept for compatibility)

    tree = ElTree.parse(path)  # nosec B314 as we parse only trusted self_prepared files
    root = tree.getroot()

    for node in root:
        tag = (node.tag or "").lower()

        # --- Global: DO NOT emit a vars step; only log declared names ---
        if tag == "global":
            vars_line = node.attrib.get("variables", "")
            if vars_line:
                var_names = [
                    v.strip() for v in vars_line.replace(",", " ").split() if v.strip()
                ]
                if log and var_names:
                    log.info("Parsed Global vars: %s", ", ".join(var_names))
            continue

        if tag == "label":
            label_id = node.attrib.get("id")
            if not label_id:
                if log:
                    log.warning("<label> without id ignored.")
                continue
            steps.append({"type": "label", "id": label_id})
            label_index[label_id] = len(steps)
            continue

        if tag == "send":
            raw = node.text or ""
            raw = textwrap.dedent(raw)
            raw = raw.lstrip("\r\n")

            raw = _map_sipp_vars_to_tpl(raw)

            # NEW: support "to" attribute on <send> (e.g. to="192.168.0.152:5060" or to="[$remote_ip]:[$remote_port]")
            to_attr = node.attrib.get("to")
            to_value = _map_sipp_vars_to_tpl(to_attr) if to_attr is not None else None

            # collect all <operate> inside <send> (pre-send hooks)
            operates: list[dict[str, Any]] = []
            for child in node:
                ctag = (child.tag or "").lower()
                if ctag == "operate":

                    def _norm_attr(v: str | None) -> str | None:
                        return _map_sipp_vars_to_tpl(v) if v is not None else None

                    method_name = child.attrib.get("method_name") or child.attrib.get(
                        "method"
                    )
                    if not method_name:
                        raise ValueError(
                            "<operate> inside <send> requires 'method_name'"
                        )

                    reserved = {"method_name", "method"}
                    params = {}
                    for k, v in child.attrib.items():
                        if k in reserved:
                            continue
                        params[k] = _norm_attr(v) or ""

                    operates.append(
                        {
                            "method": method_name,
                            "params": params,
                        }
                    )

            messages = _split_multi_messages(raw)
            for idx, m in enumerate(messages):
                step = {"type": "send", "message": m}
                if to_value:
                    step["to"] = to_value

                # attach operates only to first message of this <send> block
                if idx == 0 and operates:
                    step["operate"] = operates
                steps.append(step)
            continue

        if tag == "subscribe":
            match = {}

            if "request" in node.attrib:
                match["startswith"] = f"{node.attrib['request']} "
            if "response" in node.attrib:
                match["startswith"] = f"SIP/2.0 {node.attrib['response']}"

            reset_socket = node.attrib.get("reset_socket", "false").lower() in (
                "1",
                "true",
                "yes",
            )

            message = None
            operates: list[dict[str, Any]] = []

            for child in node:
                ctag = (child.tag or "").lower()

                if ctag == "send":
                    raw = child.text or ""
                    raw = textwrap.dedent(raw)
                    raw = raw.lstrip("\r\n")
                    raw = _map_sipp_vars_to_tpl(raw)

                    messages = _split_multi_messages(raw)
                    if messages:
                        message = messages[0]

                if ctag == "operate":

                    def _norm_attr(v: str | None) -> str | None:
                        return _map_sipp_vars_to_tpl(v) if v is not None else None

                    method_name = child.attrib.get("method_name") or child.attrib.get(
                        "method"
                    )
                    if not method_name:
                        raise ValueError("<subscribe><operate> requires 'method_name'")

                    reserved = {
                        "method_name",
                        "method",
                        "src_ip",
                        "dst_ip",
                        "dst_port",
                        "auto_200_ok",
                        "send_back",
                    }

                    params = {}
                    for k, v in child.attrib.items():
                        if k in reserved:
                            continue
                        params[k] = _norm_attr(v) or ""

                    operates.append(
                        {
                            "method": method_name,
                            "src_ip": _norm_attr(child.attrib.get("src_ip", "")),
                            "dst_ip": _norm_attr(child.attrib.get("dst_ip", "")),
                            "dst_port": _norm_attr(child.attrib.get("dst_port", ""))
                            or "5060",
                            "auto_200_ok": (
                                str(child.attrib.get("auto_200_ok", "false")).lower()
                                in ("1", "true", "yes")
                            ),
                            "send_back": (
                                str(child.attrib.get("send_back", "false")).lower()
                                in ("1", "true", "yes")
                            ),
                            "params": params,
                        }
                    )

            steps.append(
                {
                    "type": "subscribe",
                    "match": match,
                    "message": message,  # optional
                    "operate": operates,  # optional
                    "reset_socket": reset_socket,
                }
            )
            continue

        if tag == "recv":
            match = {}
            if "request" in node.attrib:
                match["startswith"] = f"{node.attrib['request']} "
            if "response" in node.attrib:
                match["startswith"] = f"SIP/2.0 {node.attrib['response']}"
            optional = node.attrib.get("optional", "false").lower() == "true"

            # base await step
            step = {"type": "await", "match": match}

            # NEW: reset_socket support
            if node.attrib.get("reset_socket", "false").lower() in ("1", "true", "yes"):
                step["reset_socket"] = True

            if optional:
                step["optional"] = True

            # per-step timeout (seconds), if provided in XML
            if "timeout" in node.attrib:
                step["timeout"] = float(node.attrib["timeout"]) / 1000.0

            # existing actions (ereg/assert)
            for child in node:
                ctag = (child.tag or "").lower()
                if ctag == "action":
                    for g in child:
                        if g.tag.lower() == "ereg":
                            rexp = g.attrib.get("regexp")
                            assign = g.attrib.get("assign")
                            if rexp and assign:
                                step.setdefault("extract", {})[assign] = rexp
                            elif rexp:
                                step.setdefault("assert", []).append({"regex": rexp})

            # NEW: support multiple <operate> children
            operates = []
            for child in node:
                ctag = (child.tag or "").lower()
                if ctag == "operate":

                    def _norm_attr(v: str | None) -> str | None:
                        return _map_sipp_vars_to_tpl(v) if v is not None else None

                    method_name = child.attrib.get("method_name") or child.attrib.get(
                        "method"
                    )
                    if not method_name:
                        raise ValueError("<operate> requires 'method_name'")

                    # Reserved attributes that control transport / behavior
                    reserved = {
                        "method_name",
                        "method",
                        "src_ip",
                        "dst_ip",
                        "dst_port",
                        "auto_200_ok",
                        "send_back",
                    }

                    # Dynamic params -> passed later to ctx["operate"]["params"]
                    params: dict[str, str] = {}
                    for k, v in child.attrib.items():
                        if k in reserved:
                            continue
                        params[k] = _norm_attr(v) or ""

                    operates.append(
                        {
                            "method": method_name,
                            "src_ip": _norm_attr(child.attrib.get("src_ip")),
                            "dst_ip": _norm_attr(child.attrib.get("dst_ip")),
                            "dst_port": _norm_attr(child.attrib.get("dst_port"))
                            or "5060",
                            # Default = False now
                            "auto_200_ok": (
                                str(child.attrib.get("auto_200_ok", "false")).lower()
                                in ("1", "true", "yes")
                            ),
                            # New flag: send response back only when no dst_ip
                            "send_back": (
                                str(child.attrib.get("send_back", "false")).lower()
                                in ("1", "true", "yes")
                            ),
                            "params": params,
                        }
                    )

            if operates:
                # Always store as list; runner will iterate them in order
                step["operate"] = operates

            steps.append(step)
            continue

        # --- Media: start RTP for specific (dst_ip, dst_port) ---
        # --- Media: start RTP or RTP proxy ---
        if tag == "media":
            media_type = (node.attrib.get("type") or "rtp").lower()

            def _norm_attr(v: str | None) -> str | None:
                return _map_sipp_vars_to_tpl(v) if v is not None else None

            # RTP
            if media_type == "rtp":
                src_ip = _norm_attr(node.attrib.get("src_ip"))
                dst_ip = _norm_attr(node.attrib.get("dst_ip"))
                dst_port = _norm_attr(node.attrib.get("dst_port"))

                step = {
                    "type": "media_start",
                    "media_type": "rtp",
                }
                if src_ip is not None:
                    step["src_ip"] = src_ip
                if dst_ip is not None:
                    step["dst_ip"] = dst_ip
                if dst_port is not None:
                    step["dst_port"] = dst_port

                steps.append(step)
                continue

            # RTP proxy
            if media_type == "rtp_proxy":
                proxy_ip = _norm_attr(node.attrib.get("proxy_ip"))
                proxy_port = _norm_attr(node.attrib.get("proxy_port"))
                src_ip = _norm_attr(node.attrib.get("src_ip"))
                dst_ip = _norm_attr(node.attrib.get("dst_ip"))
                dst_port = _norm_attr(node.attrib.get("dst_port"))

                step = {
                    "type": "media_start",
                    "media_type": "rtp_proxy",
                }
                if proxy_ip is not None:
                    step["proxy_ip"] = proxy_ip
                if proxy_port is not None:
                    step["proxy_port"] = proxy_port
                if src_ip is not None:
                    step["src_ip"] = src_ip
                if dst_ip is not None:
                    step["dst_ip"] = dst_ip
                if dst_port is not None:
                    step["dst_port"] = dst_port

                steps.append(step)
                continue

            # RTP send text (RFC 4103 / RTT-like)
            if media_type == "rtp_send_text":
                src_ip = _norm_attr(node.attrib.get("src_ip"))
                src_port = _norm_attr(node.attrib.get("src_port"))
                dst_ip = _norm_attr(node.attrib.get("dst_ip"))
                dst_port = _norm_attr(node.attrib.get("dst_port"))
                text = _norm_attr(node.attrib.get("text"))
                payload_type = _norm_attr(node.attrib.get("payload_type"))
                ts_step = _norm_attr(node.attrib.get("ts_step"))
                split = (node.attrib.get("split") or "false").lower() in (
                    "1",
                    "true",
                    "yes",
                )
                ssrc = _norm_attr(node.attrib.get("ssrc"))
                csrc = _norm_attr(node.attrib.get("csrc"))

                step = {
                    "type": "media_start",
                    "media_type": "rtp_send_text",
                    "split": split,
                }
                if src_ip is not None:
                    step["src_ip"] = src_ip
                if src_port is not None:
                    step["src_port"] = src_port
                if dst_ip is not None:
                    step["dst_ip"] = dst_ip
                if dst_port is not None:
                    step["dst_port"] = dst_port
                if text is not None:
                    step["text"] = text
                if payload_type is not None:
                    step["payload_type"] = payload_type
                if ts_step is not None:
                    step["ts_step"] = ts_step
                if ssrc is not None:
                    step["ssrc"] = ssrc
                if csrc is not None:
                    step["csrc"] = csrc

                steps.append(step)
                continue

            # RTP play audio (G.711)
            if media_type == "rtp_play_audio":

                def _norm_attr(v: str | None) -> str | None:
                    return _map_sipp_vars_to_tpl(v) if v is not None else None

                step = {
                    "type": "media_start",
                    "media_type": "rtp_play_audio",
                }

                for attr in (
                    "src_ip",
                    "src_port",
                    "dst_ip",
                    "dst_port",
                    "audio_file",
                    "codec",
                    "payload_type",
                    "clock_rate",
                    "ptime",
                    "ssrc",
                ):
                    val = _norm_attr(node.attrib.get(attr))
                    if val is not None:
                        step[attr] = val

                steps.append(step)
                continue

            if log:
                log.warning(
                    "Media type '%s' not supported, only 'rtp' and 'rtp_proxy'",
                    media_type,
                )
            continue

        # --- Stop media: stop RTP/RTP proxy for specific (dst_ip, dst_port) ---
        if tag == "stop_media":
            media_type = (node.attrib.get("type") or "rtp").lower()

            def _norm_attr(v: str | None) -> str | None:
                return _map_sipp_vars_to_tpl(v) if v is not None else None

            dst_ip = _norm_attr(node.attrib.get("dst_ip"))
            dst_port = _norm_attr(node.attrib.get("dst_port"))

            if media_type not in ("rtp", "rtp_proxy"):
                if log:
                    log.warning(
                        "Stop media type '%s' not supported, only 'rtp' and 'rtp_proxy'",
                        media_type,
                    )
                continue

            step = {
                "type": "media_stop",
                "media_type": media_type,
            }
            if dst_ip is not None:
                step["dst_ip"] = dst_ip
            if dst_port is not None:
                step["dst_port"] = dst_port

            steps.append(step)
            continue

        if tag == "pause":
            ms = int(node.attrib.get("milliseconds", "100"))
            steps.append({"type": "sleep", "seconds": ms / 1000.0})
            continue

        if tag == "nop":
            steps.append({"type": "sleep", "seconds": 0})
            continue

        if tag == "goto":
            ref = node.attrib.get("ref")
            if not ref:
                if log:
                    log.warning("<goto> without ref ignored.")
                continue
            steps.append({"type": "jump", "target": ref})
            continue

        # --- NEW: support <Set variable="X" value="Y" /> (SIPp-like) ---
        # Case-insensitive tag: <Set .../> or <set .../>
        if tag == "set":
            var_name = node.attrib.get("variable") or node.attrib.get("var")
            if not var_name:
                if log:
                    log.warning("<Set> without 'variable' ignored.")
                continue
            value = node.attrib.get("value", "")
            # Allow [var] substitution tokens inside value (map to ${var} so runner can render)
            value = _map_sipp_vars_to_tpl(value)
            # Emit a 'vars' step so ScenarioRunner applies it in sequence
            steps.append({"type": "vars", "set": {var_name: value}})
            if log:
                log.info("Parsed Set: %s = %r", var_name, value)
            continue

        if log:
            log.warning("SIPp tag not supported (ignored): <%s>", node.tag)

    # Label resolution stays as-is in your engine if you use it downstream.
    return steps
