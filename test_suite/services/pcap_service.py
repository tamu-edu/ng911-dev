import logging
import threading
import time
import copy
from pathlib import Path
from typing import List

import pyshark
import warnings
import json
import html
from enums import PacketTypeEnum, TransportProtocolEnum
from logger.logger_service import LoggingMeta
from services.aux_services.sip_message_services import extract_raw_sip_message_string
from services.config.types.lab_config import LabConfig
from services.config.types.forward_conduit_config import ForwardConduit, Conduit
from services.pcap.message_entry import MessageEntry

# TSHARK_PATH = r'C:\Users\aragn\Downloads\WiresharkPortable64\App\Wireshark\tshark.exe'

PacketTypeFilter = str | list[str] | None


class FilterConfig:
    """
    FilterConfig represents filtering parameters for test_suite packet extraction
    """

    src_ip: str | None
    dst_ip: str | None
    src_port: int | None
    dst_port: int | None
    src_ip_list: list[str] | None
    dst_ip_list: list[str] | None
    packet_type: PacketTypeFilter
    message_method: list | None
    http_status_code: int | None
    after_timestamp: float | None = None
    header_part: str | None = None
    body_part: str | None = None
    response_mode: bool = False

    def __init__(
        self,
        src_ip: str | None = None,
        dst_ip: str | None = None,
        packet_type: PacketTypeFilter = None,
        message_method: list | None = None,
        http_status_code: int | None = None,
        after_timestamp: float | None = None,
        header_part: str | None = None,
        body_part: str | None = None,
        src_ip_list: list[str] | None = None,
        dst_ip_list: list[str] | None = None,
        src_port: int | None = None,
        dst_port: int | None = None,
        response_mode: bool = False,
    ):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.packet_type = packet_type
        self.message_method = message_method
        self.http_status_code = http_status_code
        self.after_timestamp = after_timestamp
        self.header_part = header_part
        self.body_part = body_part
        self.src_ip_list = src_ip_list
        self.dst_ip_list = dst_ip_list
        self.src_port = src_port
        self.dst_port = dst_port
        self.response_mode = response_mode

    def to_pretty_string(self) -> str:
        """
        Returns a human-readable representation of FilterConfig:
        key -> value\n

        Rules:
        - None values are skipped (or include if you prefer — see option below)
        - Lists are rendered as comma-separated values
        """

        def _format_value(obj_value):
            if isinstance(obj_value, list):
                return ", ".join(map(str, obj_value))
            return str(obj_value)

        fields = {
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_ip_list": self.src_ip_list,
            "dst_ip_list": self.dst_ip_list,
            "packet_type": self.packet_type,
            "message_method": self.message_method,
            "http_status_code": self.http_status_code,
            "after_timestamp": self.after_timestamp,
            "header_part": self.header_part,
            "body_part": self.body_part,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "response_mode": self.response_mode,
        }

        lines = []

        for _k, _v in fields.items():
            if _v is not None:
                lines.append(f"{_k} -> {_format_value(_v)}")

        return "\n".join(lines)


class PcapCaptureService(metaclass=LoggingMeta):
    def __init__(
        self,
        pcap_file: str | None = None,
        capture=None,
        ssl_keys_file_path: str | None = None,
        io_mode: bool = False,
        lab_config: LabConfig | None = None,
        forward_conduit_config: ForwardConduit | None = None,
    ):
        """
        Initialize the PcapService.
        :param pcap_file: The str file path to the pcap file
        """
        self._io_mode = io_mode
        self._lab_config = lab_config
        self._forward_conduit_config = forward_conduit_config

        if capture is None and pcap_file is None:
            raise ValueError(
                "You should provide either path to a pcap file or a capture file"
            )
        if pcap_file is not None and capture is not None:
            warnings.warn(
                "You have provided both a path and a capture file. "
                "Priority goes to the capture file",
                UserWarning,
            )

        self.capture = None
        self.pcap_file = pcap_file
        self.logger = logging.getLogger("MethodLoggerService")

        if capture is not None:
            self.capture = capture
        elif pcap_file is not None:
            self._get_reassembled_capture(pcap_file, ssl_keys_file_path)

    def _log_filtering_result(self, config: FilterConfig, result: list):

        msg = "\n"
        msg += f"For given Filter Config: \n {config.to_pretty_string()} \n Matched: \n"

        for pkt in result:
            msg += str(pkt) + "\n"

        self.logger.debug(f"Result: {msg}")

    @staticmethod
    def _normalize_packet_type_filter(
        packet_type: PacketTypeFilter,
    ) -> list[str]:
        """
        Normalize packet_type filter to a list.

        Args:
            packet_type:
                Packet type filter as string, list of strings, or None.

        Returns:
            List of packet type names.
        """
        if packet_type is None:
            return []

        if isinstance(packet_type, list):
            return packet_type

        return [packet_type]

    def _get_decode_as_params(self) -> list[str]:
        """
        Builds TShark Decode As parameters for I/O proxy ingress ports.

        Decode As rules are derived from proxy interfaces defined by
        ForwardConduitConfig and protocol metadata stored in LabConfig.

        Only proxy ingress ports are decoded. Proxy egress traffic is intentionally
        excluded because logical I/O packet attribution is based on the PROXY_IF leg.
        """
        if not self._io_mode:
            return []

        if not self._lab_config or not self._forward_conduit_config:
            return []

        decode_as_params: list[str] = []
        added_rules: set[str] = set()

        for conduit in self._get_forward_conduits():
            proxy_if = self._lab_config.get_if_by_name(conduit.proxy_if)

            if proxy_if is None:
                continue

            for port in proxy_if.port_mapping or []:
                proxy_port = int(port.port)
                application_protocol = port.protocol.lower()

                if port.transport_protocol in TransportProtocolEnum.list_tls():
                    rules = [
                        f"tcp.port=={proxy_port},tls",
                        f"tls.port=={proxy_port},{application_protocol}",
                    ]

                elif port.transport_protocol == TransportProtocolEnum.TCP.value:
                    rules = [
                        f"tcp.port=={proxy_port},{application_protocol}",
                    ]

                elif port.transport_protocol == TransportProtocolEnum.UDP.value:
                    rules = [
                        f"udp.port=={proxy_port},{application_protocol}",
                    ]

                else:
                    continue

                for rule in rules:
                    if rule in added_rules:
                        continue

                    decode_as_params.extend(
                        [
                            "-d",
                            rule,
                        ]
                    )
                    added_rules.add(rule)

        if decode_as_params:
            print(
                "[PcapCaptureService] I/O Decode As parameters: " f"{decode_as_params}"
            )

        return decode_as_params

    def _get_reassembled_capture(
        self, pcap_file, ssl_keys_file_path: str | None = None
    ):
        """
        Reads the test_suite file, reassembles TCP and UDP streams.
        :param pcap_file: The path to the pcap file
        :param ssl_keys_file_path: The path to file with ssl keys
        :return: pyshark FileCapture object
        """
        print("🟡 Preparing a FileCapture from {}".format(pcap_file))
        custom_params = None
        if ssl_keys_file_path and len(ssl_keys_file_path) > 0:
            print("🟡 Using a SSL Keys from {}".format(ssl_keys_file_path))
            custom_params = [
                "-o",
                f"tls.keylog_file:{ssl_keys_file_path}",
                "-o",
                "tls.desegment_ssl_records:true",
                "-o",
                "tls.desegment_ssl_application_data:true",
            ]

            if self._io_mode:
                custom_params.extend(self._get_decode_as_params())

        def load_file_capture():
            self.capture = pyshark.FileCapture(
                pcap_file,
                custom_parameters=custom_params,
                # debug=True
                # tshark_path=TSHARK_PATH
            )

        thread = threading.Thread(target=load_file_capture)
        thread.start()
        thread.join()
        print(f"✅ Created a FileCapture -> {self.capture}")
        time.sleep(2)

    def _get_forward_conduits(self) -> list[Conduit]:
        if not self._forward_conduit_config:
            return []

        return getattr(self._forward_conduit_config, "forward_conduits", []) or []

    def _resolve_entity_name_by_ip(self, ip: str) -> str:
        if not self._lab_config:
            return ip

        for entity in self._lab_config.entities or []:
            for interface in entity.interfaces or []:
                if interface.ip == ip:
                    return entity.name

        return ip

    @staticmethod
    def _get_packet_dst_port(packet) -> int | None:
        if hasattr(packet, "tcp"):
            return int(packet.tcp.dstport)

        if hasattr(packet, "udp"):
            return int(packet.udp.dstport)

        return None

    @staticmethod
    def _get_packet_src_port(packet) -> int | None:
        if hasattr(packet, "tcp"):
            return int(packet.tcp.srcport)

        if hasattr(packet, "udp"):
            return int(packet.udp.srcport)

        return None

    def _get_if_port(
        self,
        if_name: str,
        packet_type: PacketTypeFilter = None,
    ) -> int | None:
        if not self._lab_config:
            return None

        interface = self._lab_config.get_if_by_name(if_name)
        if not interface:
            return None

        ports = interface.port_mapping or []
        packet_types = self._normalize_packet_type_filter(packet_type)

        if packet_types:
            for packet_type_item in packet_types:
                for port in ports:
                    if port.protocol == packet_type_item:
                        return int(port.port)

        if len(ports) == 1:
            return int(ports[0].port)

        return None

    def _resolve_io_logical_flow(
        self,
        observed_dst_ip: str,
        observed_dst_port: int | None,
        observed_src_ip: str,
        observed_src_port: int | None,
        packet_type: str | None = None,
    ) -> tuple[str, str] | None:
        """
        Resolves logical flow from first observed I/O proxy leg:

            FWD -> PROXY_IF:PROXY_PORT

        The proxy interface is 1:1 with a forward conduit, so:
            PROXY_IF:PROXY_PORT -> REAL_SRC -> REAL_DST
        """

        if observed_dst_port is None and observed_src_port is None:
            return None

        for conduit in self._get_forward_conduits():
            proxy_ip = self._get_if_ip(conduit.proxy_if)
            proxy_port = self._get_if_port(conduit.proxy_if, packet_type)

            real_src = self._get_if_ip(conduit.from_if)
            real_dst = self._get_if_ip(conduit.to_if)

            if (
                proxy_ip is None
                or proxy_port is None
                or real_src is None
                or real_dst is None
            ):
                continue

            if proxy_ip == observed_dst_ip and proxy_port == observed_dst_port:
                return real_src, real_dst

            if proxy_ip == observed_src_ip and proxy_port == observed_src_port:
                return real_dst, real_src

        return None

    def _get_if_ip(self, if_name: str) -> str | None:
        if not self._lab_config:
            return None

        interface = self._lab_config.get_if_by_name(if_name)
        return interface.ip if interface else None

    def _find_io_conduit_by_logical_flow(
        self,
        src_ip: str,
        dst_ip: str,
    ) -> Conduit | None:
        for conduit in self._get_forward_conduits():
            from_ip = self._get_if_ip(conduit.from_if)
            to_ip = self._get_if_ip(conduit.to_if)

            if from_ip == src_ip and to_ip == dst_ip:
                return conduit

        return None

    def _find_io_reverse_conduit_by_logical_flow(
        self,
        src_ip: str,
        dst_ip: str,
    ) -> Conduit | None:
        """
        Finds reverse conduit.

        Example:

            logical response:
                BCF -> OSP

            request conduit:
                OSP_to_BCF

        therefore:
            from_if == dst_ip
            to_if == src_ip
        """

        for conduit in self._get_forward_conduits():

            from_ip = self._get_if_ip(conduit.from_if)
            to_ip = self._get_if_ip(conduit.to_if)

            if from_ip == dst_ip and to_ip == src_ip:
                return conduit

        return None

    def _translate_config_for_io_mode(self, config: FilterConfig) -> list[FilterConfig]:
        """
        Translates logical endpoint filters into physical PCAP filters for I/O mode.

        Logical:
            FE_SRC -> FE_DST

        Observed on PSH after proxy termination:
            FWD_IP -> PROXY_IF

        Test engineers still pass logical src/dst.
        This method converts them internally.
        """
        if not self._io_mode:
            return [config]

        if not self._lab_config or not self._forward_conduit_config:
            return [config]

        translated_configs: list[FilterConfig] = []

        src_values = config.src_ip_list or ([config.src_ip] if config.src_ip else [])
        dst_values = config.dst_ip_list or ([config.dst_ip] if config.dst_ip else [])

        # Only translate when we have explicit logical src/dst pairs.
        if not src_values or not dst_values:
            return [config]

        for src_ip in src_values:
            for dst_ip in dst_values:

                if config.response_mode:
                    conduit = self._find_io_reverse_conduit_by_logical_flow(
                        src_ip=src_ip,
                        dst_ip=dst_ip,
                    )
                else:
                    conduit = self._find_io_conduit_by_logical_flow(
                        src_ip=src_ip,
                        dst_ip=dst_ip,
                    )

                if not conduit:
                    continue

                proxy_ip = self._get_if_ip(conduit.proxy_if)
                proxy_port = self._get_if_port(conduit.proxy_if, config.packet_type)

                if not proxy_ip or not proxy_port:
                    continue

                translated = copy.deepcopy(config)

                translated.src_ip_list = None
                translated.dst_ip_list = None

                if config.response_mode:
                    #
                    # Response path:
                    #
                    # PROXY_IF -> FWD
                    #
                    translated.src_ip = proxy_ip
                    translated.src_port = proxy_port
                    translated.dst_ip = None
                    translated.dst_port = None
                else:
                    #
                    # Request path:
                    #
                    # FWD -> PROXY_IF
                    #
                    translated.src_ip = None
                    translated.src_port = None
                    translated.dst_ip = proxy_ip
                    translated.dst_port = proxy_port

                translated_configs.append(translated)
        return translated_configs or [config]

    def get_capture(self):
        """
        Getter for the PcapService capture property
        :return: pyshark FileCapture object
        """
        return self.capture

    def get_capture_name(self):
        """
        Getter for the PcapService capture property
        :return: pyshark FileCapture object
        """
        return str(self.pcap_file)

    def get_capture_len(self):
        """
        Getter for the len of the PcapService capture property
        :return: int, amount of packets in the capture
        """
        return len(list(self.capture))

    def close_capture(self):
        """
        Closes the pyshark capture object manually
        :return: None
        """
        self.capture.close()

    def get_all_sip_messages(self):
        """
        Extracts all the sip messages from the capture
        :return: list of sip messages
        """
        return self.get_messages_by_config(FilterConfig(packet_type=PacketTypeEnum.SIP))

    def get_messages_by_config(self, config: FilterConfig):
        def match_packet(packet, active_config: FilterConfig):
            # Check IP source and destination conditions
            if active_config.src_ip and (
                not hasattr(packet, "ip") or packet.ip.src != active_config.src_ip
            ):
                return False
            if active_config.src_ip_list and (
                not hasattr(packet, "ip")
                or packet.ip.src not in active_config.src_ip_list
            ):
                return False
            if active_config.dst_ip and (
                not hasattr(packet, "ip") or packet.ip.dst != active_config.dst_ip
            ):
                return False
            if active_config.dst_ip_list and (
                not hasattr(packet, "ip")
                or packet.ip.dst not in active_config.dst_ip_list
            ):
                return False

            packet_src_port = self._get_packet_src_port(packet)
            packet_dst_port = self._get_packet_dst_port(packet)

            if active_config.src_port and packet_src_port != active_config.src_port:
                return False

            if active_config.dst_port and packet_dst_port != active_config.dst_port:
                return False

            # Check packet type (handle both HTTP and HTTP/JSON)
            packet_types = self._normalize_packet_type_filter(active_config.packet_type)

            packet_layer = None

            if packet_types:
                for packet_type_item in packet_types:
                    packet_layer = getattr(packet, packet_type_item, None)

                    if packet_layer is None and packet_type_item == PacketTypeEnum.HTTP:
                        packet_layer = getattr(packet, "HTTP/JSON", None)

                    if packet_layer is not None:
                        break

                if packet_layer is None:
                    return False

            # Check message methods (SIP/HTTP methods)
            if active_config.message_method and packet_layer:
                method = getattr(packet_layer, "method", None) or getattr(
                    packet_layer, "request_method", None
                )
                if method not in active_config.message_method:
                    return False

            # Check HTTP status code
            if active_config.http_status_code and packet_layer:
                response_code = getattr(packet_layer, "response_code", None)
                if response_code != str(active_config.http_status_code):
                    return False

            # Check timestamp condition
            if active_config.after_timestamp and (
                not hasattr(packet, "sniff_timestamp")
                or float(packet.sniff_timestamp) <= float(active_config.after_timestamp)
            ):
                return False

            # Check request URI header # TODO check if other headers needs to be checked
            if active_config.header_part and packet_layer:
                header = getattr(packet_layer, "r_uri", None)
                if (
                    header
                    and active_config.header_part.lower() not in str(header).lower()
                ):
                    return False

            # Check body
            if active_config.body_part and packet_layer:
                body = getattr(packet_layer, "msg_body", None)
                if body and active_config.body_part.lower() not in body.lower():
                    return False

            return True

        result: list = []

        if self.capture is not None:
            normalized_configs = self._translate_config_for_io_mode(config)

            for normalized_config in normalized_configs:
                result.extend(
                    pkt for pkt in self.capture if match_packet(pkt, normalized_config)
                )

        self._log_filtering_result(config=config, result=result)

        return result

    def build_io_transcript(self) -> list[dict]:
        """
        Builds logical communication transcript for I/O mode.
        """

        if not self._io_mode:
            return []

        if self.capture is None:
            return []

        transcript: list[MessageEntry] = []

        for packet in self.capture:
            try:

                if not hasattr(packet, "ip"):
                    continue

                observed_dst_ip = str(packet.ip.dst)
                observed_dst_port = self._get_packet_dst_port(packet)

                observed_src_ip = str(packet.ip.src)
                observed_src_port = self._get_packet_src_port(packet)

                packet_type = None

                if hasattr(packet, "sip") or hasattr(packet, "raw_sip"):
                    packet_type = PacketTypeEnum.SIP
                elif hasattr(packet, "http") or hasattr(packet, "HTTP/JSON"):
                    packet_type = PacketTypeEnum.HTTP

                logical_flow = self._resolve_io_logical_flow(
                    observed_dst_ip=observed_dst_ip,
                    observed_dst_port=observed_dst_port,
                    observed_src_ip=observed_src_ip,
                    observed_src_port=observed_src_port,
                    packet_type=packet_type,
                )

                # Skip service/internal traffic
                if not logical_flow:
                    continue

                logical_src_ip, logical_dst_ip = logical_flow

                src_name = self._resolve_entity_name_by_ip(logical_src_ip)
                dst_name = self._resolve_entity_name_by_ip(logical_dst_ip)

                protocol: str | None = None
                layer = None

                # =========================
                # SIP
                # =========================

                if hasattr(packet, "sip") or hasattr(packet, "raw_sip"):
                    protocol = "SIP"

                # =========================
                # HTTP
                # =========================

                elif hasattr(packet, "http"):
                    protocol = "HTTP"
                    layer = packet.http

                elif hasattr(packet, "HTTP/JSON"):
                    protocol = "HTTP"
                    layer = getattr(packet, "HTTP/JSON")

                if not protocol:
                    continue

                method = None
                response_code = None

                # =========================
                # SIP extraction
                # =========================

                if protocol == "SIP":

                    message = extract_raw_sip_message_string(packet)

                    if not message:
                        continue

                    if hasattr(packet, "sip"):
                        method = getattr(packet.sip, "Method", None)
                        response_code = getattr(packet.sip, "Status_Code", None)

                # =========================
                # HTTP extraction
                # =========================

                else:

                    if layer is None:
                        continue

                    method = getattr(layer, "method", None) or getattr(
                        layer, "request_method", None
                    )

                    response_code = getattr(layer, "response_code", None)

                    message = str(layer)

                # =========================
                # Message classification
                # =========================

                if response_code:
                    message_type = "RESPONSE"

                    if protocol == "SIP":
                        message = extract_raw_sip_message_string(packet)
                        summary = message.splitlines()[0].replace("SIP/", "")
                    elif protocol == "HTTP":
                        response_phrase = getattr(
                            layer,
                            "response_phrase",
                            None,
                        )

                        summary = (
                            f"{response_code} {response_phrase}"
                            if response_phrase
                            else str(response_code)
                        )

                    else:
                        summary = str(response_code)

                else:
                    message_type = "REQUEST"
                    summary = str(method) if method else protocol

                packet_number = getattr(packet, "number", 0)
                sniff_timestamp = getattr(packet, "sniff_timestamp", 0)

                transcript.append(
                    MessageEntry(
                        timestamp=float(sniff_timestamp),
                        src_name=src_name,
                        src_ip=logical_src_ip,
                        dst_name=dst_name,
                        dst_ip=logical_dst_ip,
                        protocol=protocol,
                        message_type=message_type,
                        method=str(method) if method else None,
                        summary=summary,
                        message=message,
                        packet_number=int(packet_number),
                    )
                )

            except Exception as e:
                self.logger.debug(f"Failed building transcript entry: {e}")

        transcript.sort(key=lambda x: x.timestamp)

        return [entry.to_dict() for entry in transcript]

    @staticmethod
    def generate_mermaid_str(transcript: list[dict]) -> tuple[str, dict[str, str]]:

        participants: List[str] = []

        mermaid_lines: list[str] = [
            "sequenceDiagram",
            "autonumber",
        ]

        message_map: dict[str, str] = {}

        for idx, entry in enumerate(transcript, start=1):
            src = entry["src_name"]
            dst = entry["dst_name"]

            participants.append(src)
            participants.append(dst)

            msg_id = f"M{idx}"

            protocol = entry.get("protocol") or ""
            summary = entry.get("summary") or "MESSAGE"

            label = f"{protocol} {summary} [{msg_id}]"

            mermaid_lines.append(f"{src}->>{dst}: {label}")

            message_map[msg_id] = entry.get("message", "")

        participant_lines = [
            f"participant {participant}" for participant in participants
        ]

        mermaid_str = "\n".join(
            ["sequenceDiagram"] + participant_lines + mermaid_lines[1:]
        )

        return mermaid_str, message_map

    @staticmethod
    def generate_sequence_diagram_html(
        mermaid_str: str,
        message_map: dict[str, str],
        title: str = "NG911 Sequence Diagram",
    ) -> str:

        escaped_messages = {k: html.escape(v) for k, v in message_map.items()}

        messages_json = json.dumps(escaped_messages)

        buttons_html = ""

        for msg_id in message_map.keys():
            buttons_html += f"""
<button class="msg-btn" onclick="showMessage('{msg_id}')">
    {msg_id}
</button>
"""

        return f"""
<!DOCTYPE html>
<html lang="en">

<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>

<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

mermaid.initialize({{
    startOnLoad: true,
    theme: 'dark',
    securityLevel: 'loose'
}});

window.messageMap = {messages_json};

window.showMessage = function(id) {{

    const modal = document.getElementById("modal");
    const modalTitle = document.getElementById("modal-title");
    const modalBody = document.getElementById("modal-body");

    modalTitle.innerText = id;
    modalBody.innerHTML = window.messageMap[id];

    modal.style.display = "block";
}};

window.closeModal = function() {{
    document.getElementById("modal").style.display = "none";
}};
</script>

<style>

body {{
    background-color: #0b1020;
    color: #e5e7eb;
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}}

h1 {{
    margin-bottom: 30px;
}}

.diagram-container {{
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    overflow-x: auto;
}}

.message-toolbar {{
    margin-top: 30px;
}}

.msg-btn {{
    margin: 5px;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background-color: #2563eb;
    color: white;
    cursor: pointer;
    font-weight: bold;
}}

.msg-btn:hover {{
    background-color: #1d4ed8;
}}

.modal {{
    display: none;
    position: fixed;
    z-index: 9999;
    left: 5%;
    top: 5%;
    width: 90%;
    height: 90%;
    background-color: #111827;
    border: 2px solid #374151;
    border-radius: 12px;
    overflow: hidden;
}}

.modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background-color: #1f2937;
    border-bottom: 1px solid #374151;
}}

.modal-title {{
    font-size: 20px;
    font-weight: bold;
}}

.close-btn {{
    background-color: #dc2626;
    border: none;
    color: white;
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
}}

.close-btn:hover {{
    background-color: #b91c1c;
}}

.modal-body {{
    padding: 20px;
    overflow: auto;
    height: calc(100% - 80px);
}}

pre {{
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: Consolas, monospace;
    font-size: 14px;
    line-height: 1.4;
    color: #d1d5db;
}}

</style>

</head>

<body>

<h1>{html.escape(title)}</h1>

<div class="diagram-container">
<div class="mermaid">

{mermaid_str}

</div>
</div>

<div class="message-toolbar">
<h2>Messages</h2>

{buttons_html}

</div>

<div id="modal" class="modal">

<div class="modal-header">

<div id="modal-title" class="modal-title">
Message
</div>

<button class="close-btn" onclick="closeModal()">
Close
</button>

</div>

<div class="modal-body">

<pre id="modal-body"></pre>

</div>

</div>

</body>
</html>
"""

    def save_sequence_diagram_html(
        self,
        variation_name: str,
        output_dir: str,
        filename: str = "sequence_diagram.html",
    ) -> str:
        """
        Saves generated sequence diagram HTML.

        Returns:
            Full path to created file.
        """
        transcript = self.build_io_transcript()

        mermaid_str, message_map = self.generate_mermaid_str(transcript)

        html_report = self.generate_sequence_diagram_html(
            mermaid_str=mermaid_str,
            message_map=message_map,
            title=f"{variation_name} Variation Flow",
        )

        output_path = Path(output_dir + "/sequence_diagrams")
        output_path.mkdir(parents=True, exist_ok=True)

        html_file = output_path / f"{variation_name}_{filename}"

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_report)

        return str(html_file)
