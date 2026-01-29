import time
import re
from typing import Dict, Tuple

from sipp_compatibility import render_sipp_like
from extra_logic.extra_logic_loader import load_callable
from rtp_transport import RTPTransport, RTPProxyTransport, RTPAudioStream, RTPTextStream
from sdp_utils import parse_sdp_connection_and_audio_port

CALL_ID_RE = re.compile(r"(?mi)^\s*Call-ID\s*:\s*(.+?)\s*$")
SDP_SPLIT_RE = re.compile(r"\r\n\r\n", re.M)  # split headers/body
CT_RE = re.compile(r"(?im)^\s*Content-Type\s*:\s*application/sdp(?:\s*;.*)?\s*$")
REQ_LINE_RE = re.compile(r"^([A-Z]+)\s+\S+\s+SIP/2\.0", re.M)
RESP_LINE_RE = re.compile(r"^SIP/2\.0\s+(\d{3})\b", re.M)
_HDR_RE = re.compile(r"(?im)^([A-Za-z\-]+)\s*:\s*(.*?)\s*$")


class ScenarioRunner:
    """
    Executes IR steps:
      - await {match:{startswith|contains|regex}, timeout, extract:{k:pattern}, optional?}
      - send/respond/proceed {message, to?}
      - sleep {seconds}
      - vars {set:{k:v}}
      - assert {regex|contains}
      - rtp_recv_start
      - rtp_send {payload_hex}
      - label {id}
      - jump {target}
    """

    def __init__(self, sip_transport, rtp_transport, steps, vars, log,
                 message_timeout, transaction_timeout, default_remote,
                 hook_pipeline=None):
        self.sip = sip_transport
        self.rtp = rtp_transport
        self.steps = steps or []
        self.vars = vars or {}
        self.log = log
        self.message_timeout = message_timeout
        self.transaction_timeout = transaction_timeout
        self.default_remote = default_remote
        self.inbox = []
        self.peer = None  # discovered on first inbound

        self.hooks = hook_pipeline
        # we keep discovered RTP remote here
        self.rtp_remote = None

        # computed/default vars
        self.vars.setdefault("peer_ip", "")
        self.vars.setdefault("peer_port", "")
        self.vars.setdefault("call_number", self.vars.get("from_tag", "1"))
        self.vars.setdefault("transport", self._compute_transport() or "UDP")
        self.vars.setdefault("peer_tag_param", "")  # becomes ";tag=..." after 200 OK if extracted

        # build label index for jumps
        self.label_idx = {}
        for i, st in enumerate(self.steps):
            if st.get("type") == "label" and "id" in st:
                # jump should land on the *next* step after label
                self.label_idx[st["id"]] = i + 1

        # RTP media sessions (multiple bind ip:port at the same time)
        self.rtp_sessions: Dict[Tuple[str, int], RTPTransport | RTPProxyTransport] = {}
        # key: (dst_ip, dst_port) -> RTPTransport

        # Stateful RTP text streams:
        # key = (src_ip, src_port, dst_ip, dst_port, payload_type)
        self.rtp_text_streams: dict[tuple[str, int, str, int, int], RTPTextStream] = {}

        # If scenario contains explicit media steps, we disable auto-RTP-from-SDP
        self.explicit_media = any(
            st.get("type") in ("media_start", "media_stop") for st in self.steps
        )

    def _compute_transport(self):
        # Guess from local vars (protocol not directly passed here, but we infer from Via headers if needed).
        # For now: rely on provided CLI protocol via vars injection in service (utils.default_vars can set it).
        return self.vars.get("transport") or "UDP"

    @staticmethod
    def _extract_sdp_if_present(sip_text: str) -> str | None:
        """
        Return SDP body if Content-Type is application/sdp, else None.
        """
        # fast check: look for Content-Type header
        if not CT_RE.search(sip_text):
            return None
        parts = SDP_SPLIT_RE.split(sip_text, maxsplit=1)
        if len(parts) == 2:
            return parts[1]
        return None

    @staticmethod
    def _parse_headers(sip_text: str) -> dict:
        head = sip_text.split("\r\n\r\n", 1)[0]
        headers = {}
        for m in _HDR_RE.finditer(head):
            headers[m.group(1).lower()] = m.group(2)
        return headers

    def _build_200_ok_from_request(self, req_text: str, vars_dict: dict) -> str:
        h = self._parse_headers(req_text)
        via = h.get("via", "")
        from_h = h.get("from", "")
        to_h = h.get("to", "")
        call_id = h.get("call-id", vars_dict.get("call_id", "X@" + vars_dict.get("local_ip", "stub")))
        cseq = h.get("cseq", f"{vars_dict.get('cseq', '1')} INVITE")

        to_tag = vars_dict.get("to_tag") or vars_dict.get("from_tag") or "srvtag"
        if ";tag=" not in to_h:
            to_h = f"{to_h};tag={to_tag}"
            vars_dict["peer_tag_param"] = f";tag={to_tag}"

        return (
            "SIP/2.0 200 OK\r\n"
            f"Via: {via}\r\n"
            f"From: {from_h}\r\n"
            f"To: {to_h}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: {cseq}\r\n"
            "Content-Length: 0\r\n\r\n"
        )

    def on_incoming(self, text, addr):
        # business-logic hooks (if you already wired them)
        if self.hooks:
            ctx = {"vars": self.vars, "log": self.log, "direction": "in", "protocol": self.sip.protocol}
            res = self.hooks.run_on_receive(text, addr, ctx)
            if res.drop:
                self.log.info("Incoming message dropped by business logic.")
                return
            if res.respond_with:
                self._send_text(res.respond_with, addr)
                return
            if res.text is not None:
                text = res.text

        # remember peer
        if not self.peer:
            self.peer = addr
            self.vars["peer_ip"], self.vars["peer_port"] = addr[0], str(addr[1])

            # Try to extract SDP and discover RTP peer (common cases: INVITE w/ SDP, 200 OK w/ SDP)
            sdp = self._extract_sdp_if_present(text)
            if sdp:
                ip, port = parse_sdp_connection_and_audio_port(sdp)
                if port:
                    # prefer explicit SDP c= ip, fallback to src addr if missing
                    rtp_ip = ip or addr[0]
                    self.rtp_remote = (rtp_ip, port)
                    self.log.info("Discovered RTP remote via SDP: %s:%s", rtp_ip, port)

                    # Auto-create RTP only if scenario does not define explicit media steps
                    if self.rtp is None and not getattr(self, "explicit_media", False):
                        # bind to local SIP IP with ephemeral RTP port (0) unless provided via vars
                        local_ip = self.vars.get("rtp_local_ip") or self.vars.get("local_ip") or self.sip.bind[0]
                        local_port = int(self.vars.get("rtp_local_port") or 0)
                        self.rtp = RTPTransport((local_ip, local_port), log=self.log)
                        self.rtp.start()
                        self.rtp.recv_loop(lambda data, a: None)  # no-op receiver; can attach real cb if needed
                        # store the actual local RTP port for SDP answers if your scenarios build them
                        try:
                            actual_bind = self.rtp.sock.getsockname()
                            self.vars["rtp_local_ip"] = actual_bind[0]
                            self.vars["rtp_local_port"] = str(actual_bind[1])
                        except Exception as e:
                            print(f"Unexpected error {e}")

        # queue message
        self.inbox.append((text, addr))
        self.log.info("RX %s: %s", addr, text.split("\r\n", 1)[0])

    def _execute_operate(self, operate: dict, in_text: str, src_addr):
        """Run <operate> business-logic for a received message."""
        # Render transport-related attrs
        src_ip = self._render(operate.get("src_ip") or "")
        dst_ip = self._render(operate.get("dst_ip") or "")
        dst_port_s = self._render(operate.get("dst_port") or "5060")
        try:
            dst_port = int(dst_port_s) if dst_port_s else 5060
        except ValueError:
            dst_port = 5060

        # Render dynamic params (global_var, ctx_key, etc.)
        raw_params = operate.get("params") or {}
        rendered_params = {}
        for k, v in raw_params.items():
            rendered_params[k] = self._render(v or "")

        # Optional source filter
        if src_ip and src_addr[0] != src_ip:
            self.log.info("operate: source_ip mismatch (%s != %s), skipping", src_addr[0], src_ip)
            return

        method = operate["method"]
        fn = load_callable(method)  # callable(message_text, ctx) -> str|None

        ctx = {
            "src_addr": src_addr,
            "vars": self.vars,
            "log": self.log,
            "operate": {
                "method": method,
                "params": rendered_params,
            },
        }

        out_text = fn(in_text, ctx)

        # If handler returns None or empty string, treat as "no outgoing send".
        if out_text is None or out_text == "":
            return

        if not isinstance(out_text, str):
            raise TypeError(f"operate '{method}' must return SIP text or None")

        auto_200 = bool(operate.get("auto_200_ok", False))
        send_back = bool(operate.get("send_back", False))

        if dst_ip:  # forward
            if auto_200:  # and send response 200ok
                ok_text = self._build_200_ok_from_request(in_text, self.vars)
                self._send_text(ok_text, src_addr)
            self._send_text(out_text, (dst_ip, dst_port))
        elif send_back:  # send response with modified msg
            self._send_text(out_text, src_addr)
        else:  # return modified message for further use
            return out_text

    def _execute_send_operate(self, operate: dict, msg_text: str, dst_addr):
        """Run <operate> attached to a <send> step, transforming msg_text before send."""
        raw_params = operate.get("params") or {}
        rendered_params = {}
        for k, v in raw_params.items():
            rendered_params[k] = self._render(v or "")

        method = operate["method"]
        fn = load_callable(method)  # callable(message_text, ctx) -> str

        ctx = {
            "vars": self.vars,
            "log": self.log,
            "direction": "out",
            "dst_addr": dst_addr,
            "operate": {
                "method": method,
                "params": rendered_params,
            },
        }

        out_text = fn(msg_text, ctx)
        if out_text is None or out_text == "":
            # If handler returns None/empty, keep original message
            return msg_text

        if not isinstance(out_text, str):
            raise TypeError(f"send-operate '{method}' must return SIP text or None")

        return out_text

    def run(self):
        pc = 0
        while pc < len(self.steps):
            step = self.steps[pc]
            pc += 1  # default advance; jump can override
            t = step.get("type")

            if t == "label":
                # no-op; control falls through
                continue

            if t == "jump":
                target = step.get("target")
                if target in self.label_idx:
                    pc = self.label_idx[target]
                    continue
                raise ValueError(f"jump target not found: {target}")

            if t == "await":
                timeout = float(step.get("timeout", self.message_timeout))
                try:
                    matched = self._await(step.get("match", {}), timeout)
                except TimeoutError:
                    if step.get("optional"):
                        self.log.info("optional await timed out, continuing: %s", step.get("match"))
                        continue
                    raise

                # assertions (if any)
                for asrt in step.get("assert", []):
                    if "regex" in asrt and not re.search(asrt["regex"], matched[0], re.M):
                        raise AssertionError(f"assert regex failed: {asrt['regex']}")
                    if "contains" in asrt and asrt["contains"] not in matched[0]:
                        raise AssertionError(f"assert contains failed: {asrt['contains']}")

                # extract vars (e.g., to_tag)
                for k, pat in step.get("extract", {}).items():
                    m = re.search(pat, matched[0], re.M)
                    if m:
                        self.vars[k] = m.group(1)
                        if k == "to_tag":
                            self.vars["peer_tag_param"] = f";tag={self.vars['to_tag']}"

                # multiple operates support
                operates = step.get("operate") or []
                if isinstance(operates, dict):
                    operates = [operates]

                if operates:
                    matched_text, matched_addr = matched
                    current_text = matched_text
                    for op in operates:
                        current_text = self._execute_operate(op, current_text, matched_addr)

                continue

            if t in ("send", "respond", "proceed"):
                msg = self._render(step["message"])
                addr = self._resolve_addr(step.get("to"))

                operates = step.get("operate") or []
                if isinstance(operates, dict):
                    operates = [operates]

                for op in operates:
                    msg = self._execute_send_operate(op, msg, addr)

                self._send_text(msg, addr)
                continue

            if t == "sleep":
                time.sleep(float(step.get("seconds", 0.1)))
                continue

            if t == "vars":
                for k, v in step.get("set", {}).items():
                    self.vars[k] = self._render(v)
                continue

            if t == "assert":
                text = self.inbox[-1][0] if self.inbox else ""
                if "regex" in step and not re.search(step["regex"], text, re.M):
                    raise AssertionError(f"assert regex failed: {step['regex']}")
                if "contains" in step and (step["contains"] not in text):
                    raise AssertionError(f"assert contains failed: {step['contains']}")
                continue

            if t == "rtp_recv_start":
                if not self.rtp:
                    raise RuntimeError("RTP not configured (no rtp_bind)")
                self.rtp.recv_loop(cb=lambda data, addr: self.log.debug("RTP RX %dB from %s", len(data), addr))
                continue

            if t == "rtp_send":
                if not self.rtp:
                    raise RuntimeError("RTP not configured (no rtp_bind)")
                payload_hex = self._render(step["payload_hex"])
                self.rtp.send_raw(bytes.fromhex(payload_hex), self._resolve_rtp_remote())
                continue

            if t == "media_start":
                media_type = (step.get("media_type") or "rtp").lower()

                # --------- RTP ----------
                if media_type == "rtp":
                    dst_ip = self._render(step.get("dst_ip") or "")
                    dst_port_s = self._render(step.get("dst_port") or "")
                    if not dst_ip or not dst_port_s:
                        self.log.error("media_start: dst_ip or dst_port is missing after render")
                        continue
                    try:
                        dst_port = int(dst_port_s)
                    except ValueError:
                        self.log.error("media_start: invalid dst_port %r", dst_port_s)
                        continue

                    key = (dst_ip, dst_port)
                    if key in self.rtp_sessions:
                        self.log.info("RTP media already started on %s:%s, skipping", dst_ip, dst_port)
                        continue

                    src_ip = self._render(step.get("src_ip") or "")

                    rtp = RTPTransport((dst_ip, dst_port), log=self.log)
                    try:
                        rtp.start()

                        def _cb(data, _addr, expected_src=src_ip):
                            # Optional source IP filter
                            if expected_src and _addr[0] != expected_src:
                                return
                            self.log.debug("RTP RX %dB from %s", len(data), _addr)

                        rtp.recv_loop(_cb)
                        self.rtp_sessions[key] = rtp
                        self.log.info("Started RTP media on %s:%s (src_ip filter=%s)", dst_ip, dst_port,
                                      src_ip or "any")
                    except OSError as e:
                        if self.log:
                            self.log.error(f"RTP not bound -> {e}")

                    continue

                # --------- RTP proxy ----------
                if media_type == "rtp_proxy":
                    proxy_ip = self._render(step.get("proxy_ip") or "")
                    proxy_port_s = self._render(step.get("proxy_port") or "")
                    dst_ip = self._render(step.get("dst_ip") or "")
                    dst_port_s = self._render(step.get("dst_port") or "")
                    src_ip = self._render(step.get("src_ip") or "")

                    if not proxy_ip or not dst_ip or not dst_port_s:
                        self.log.error("media_start rtp_proxy: proxy_ip/dst_ip/dst_port missing after render")
                        continue
                    try:
                        dst_port = int(dst_port_s)
                    except ValueError:
                        self.log.error("media_start rtp_proxy: invalid dst_port %r", dst_port_s)
                        continue

                    if proxy_port_s:
                        try:
                            proxy_port = int(proxy_port_s)
                        except ValueError:
                            self.log.error("media_start rtp_proxy: invalid proxy_port %r", proxy_port_s)
                            continue
                    else:
                        proxy_port = dst_port

                    key = (proxy_ip, proxy_port, dst_ip, dst_port)
                    if key in self.rtp_sessions:
                        self.log.info(
                            "RTP proxy already started on %s:%s → %s:%s, skipping",
                            proxy_ip, proxy_port, dst_ip, dst_port
                        )
                        continue

                    proxy = RTPProxyTransport(
                        bind_ip=proxy_ip,
                        bind_port=proxy_port,
                        dst_ip=dst_ip,
                        dst_port=dst_port,
                        src_ip_filter=src_ip,
                        log=self.log,
                    )
                    try:
                        proxy.start()
                        self.rtp_sessions[key] = proxy
                        self.log.info(
                            "Started RTP proxy on %s:%s → %s:%s (src_ip filter=%s)",
                            proxy_ip, proxy_port, dst_ip, dst_port, src_ip or "any"
                        )
                    except OSError as e:
                        if self.log:
                            self.log.error(f"RTP proxy not bound -> {e}")

                    continue

                # --------- RTP send text (RFC 4103 / RTT-like) ----------
                if media_type == "rtp_send_text":
                    dst_ip = self._render(step.get("dst_ip") or "")
                    dst_port_s = self._render(step.get("dst_port") or "")

                    # Source stream control (bind for sending)
                    src_ip = self._render(step.get("src_ip") or "") or (
                            self.vars.get("rtp_local_ip") or self.vars.get("local_ip") or self.sip.bind[0]
                    )
                    src_port_s = self._render(step.get("src_port") or "") or "0"

                    text = self._render(step.get("text") or "")
                    split = bool(step.get("split", False))

                    payload_type_s = self._render(step.get("payload_type") or "98")
                    ts_step_s = self._render(step.get("ts_step") or "20")

                    if not dst_ip or not dst_port_s:
                        self.log.error("rtp_send_text: dst_ip/dst_port missing after render")
                        continue

                    ssrc = int(step["ssrc"]) if step.get("ssrc") else None

                    csrc_list = []
                    if step.get("csrc"):
                        csrc_list = [
                            int(x.strip())
                            for x in step["csrc"].split(",")
                            if x.strip()
                        ]

                    try:
                        dst_port = int(dst_port_s)
                        src_port = int(src_port_s)
                        payload_type = int(payload_type_s)
                        ts_step = int(ts_step_s)
                    except ValueError:
                        self.log.error("rtp_send_text: invalid port/payload_type/ts_step")
                        continue

                    key = (src_ip, src_port, dst_ip, dst_port, payload_type)
                    stream = self.rtp_text_streams.get(key)

                    if stream is not None:
                        if ssrc is not None and ssrc != stream.ssrc:
                            self.log.warning(
                                "RTT stream already exists; SSRC change ignored "
                                "(existing=%s requested=%s)",
                                stream.ssrc,
                                ssrc
                            )

                        if csrc_list and csrc_list != stream.csrc_list:
                            self.log.warning(
                                "RTT stream already exists; CSRC change ignored "
                                "(existing=%s requested=%s)",
                                stream.csrc_list,
                                csrc_list
                            )

                    if stream is None:
                        stream = RTPTextStream(
                            src_ip=src_ip,
                            src_port=int(src_port or 0),
                            dst_ip=dst_ip,
                            dst_port=int(dst_port),
                            payload_type=int(payload_type or 98),
                            ts_step=int(ts_step or 20),
                            ssrc=ssrc,
                            csrc_list=csrc_list,
                            log=self.log,
                        )
                        stream.start()
                        self.rtp_text_streams[key] = stream

                    if split:
                        # Typing simulation: 1 char per RTP packet
                        # RFC 4103: timestamp clock = 1000 Hz → ts_step = milliseconds
                        delay_sec = ts_step / 1000.0

                        for ch in text:
                            stream.send_text_packet(ch)
                            time.sleep(delay_sec)
                    else:
                        # Single RTP packet for entire string
                        stream.send_text_packet(text)

                    continue

                # --------- RTP play audio ----------
                if media_type == "rtp_play_audio":
                    audio = RTPAudioStream(
                        src_ip=self._render(step["src_ip"]),
                        src_port=int(self._render(step["src_port"])),
                        dst_ip=self._render(step["dst_ip"]),
                        dst_port=int(self._render(step["dst_port"])),
                        audio_file=self._render(step["audio_file"]),
                        codec=self._render(step.get("codec", "pcmu")),
                        payload_type=int(self._render(step["payload_type"])) if step.get("payload_type") else None,
                        clock_rate=int(self._render(step.get("clock_rate", "8000"))),
                        ptime=int(self._render(step.get("ptime", "20"))),
                        ssrc=int(step["ssrc"]) if step.get("ssrc") else None,
                        log=self.log,
                    )

                    audio.play()
                    continue

            if t == "media_stop":
                dst_ip = self._render(step.get("dst_ip") or "")
                dst_port_s = self._render(step.get("dst_port") or "")

                if not dst_ip or not dst_port_s:
                    self.log.error("media_stop: dst_ip or dst_port is missing after render")
                    continue
                try:
                    dst_port = int(dst_port_s)
                except ValueError:
                    self.log.error("media_stop: invalid dst_port %r", dst_port_s)
                    continue

                # Stop RTT (RTP text) streams matching dst_ip/dst_port
                for key, stream in list(self.rtp_text_streams.items()):
                    _, _, d_ip, d_port, _ = key
                    if d_ip == dst_ip and d_port == dst_port:
                        try:
                            stream.stop()
                        except Exception:
                            pass
                        self.rtp_text_streams.pop(key, None)
                        self.log.info("Stopped RTP text stream → %s:%s", dst_ip, dst_port)

                key = (dst_ip, dst_port)
                rtp = self.rtp_sessions.pop(key, None)
                if rtp:
                    try:
                        rtp.stop()
                    except Exception as e:
                        print(f"Unexpected error {e}")
                    self.log.info("Stopped media on %s:%s", dst_ip, dst_port)
                else:
                    self.log.warning("media_stop: no RTP session found for %s:%s", dst_ip, dst_port)
                continue

            raise ValueError(f"Unknown step type: {t}")

        self.log.info("Scenario finished")

        # Cleanup text streams
        for s in list(self.rtp_text_streams.values()):
            try:
                s.stop()
            except Exception:
                pass

    def _await(self, cond, timeout):
        end = time.time() + timeout
        while time.time() < end:
            if self.inbox:
                msg = self.inbox.pop(0)
                if self._match(msg[0], cond):
                    self.peer = msg[1]
                    self.vars["peer_ip"], self.vars["peer_port"] = self.peer[0], str(self.peer[1])
                    return msg
            time.sleep(0.01)
        raise TimeoutError(f"await timed out: {cond}")

    @staticmethod
    def _match(text, cond):
        if "startswith" in cond and not text.startswith(cond["startswith"]):
            return False
        if "contains" in cond and cond["contains"] not in text:
            return False
        if "regex" in cond and not re.search(cond["regex"], text, re.M):
            return False
        return True

    def _render(self, s):
        if s is None:
            return ""
        return re.sub(r"\$\{([a-zA-Z0-9_]+)\}", lambda m: str(self.vars.get(m.group(1), "")), s)

    def _resolve_addr(self, to_arg):
        if to_arg is None:
            # NEW: default is remote-ip, not peer
            if self.default_remote:
                return self.default_remote

            if self.peer:
                return self.peer

            raise RuntimeError("No peer/default remote known yet")

        if to_arg == "peer":
            if self.peer:
                return self.peer
            raise RuntimeError("Peer not known yet")

        to_str = self._render(to_arg).strip()

        if ":" in to_str:
            ip, port = to_str.split(":", 1)
            return ip, int(port)

        port = None
        if self.default_remote:
            port = self.default_remote[1]
        elif self.vars.get("remote_port"):
            port = int(self.vars["remote_port"])
        else:
            port = 5060
        return to_str, port

    def _resolve_rtp_remote(self):
        ip = self.vars.get("rtp_remote_ip")
        port = self.vars.get("rtp_remote_port")
        if ip and port:
            return ip, int(port)
        raise RuntimeError("RTP remote not set")

    def _send_text(self, msg_text, addr):
        # data = msg_text.encode("utf-8")
        # self.sip.send(data, addr)
        # self.log.info("TX %s: %s", addr, msg_text.split("\r\n", 1)[0])

        data = render_sipp_like(msg_text, self.vars)
        self.sip.send(data, addr)

        first = data.decode("utf-8", "replace").split("\r\n", 1)[0]
        self.log.info("TX %s: %s", addr, first)
