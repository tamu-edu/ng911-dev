import logging
import threading
import time

import pyshark
import warnings
from enums import PacketTypeEnum
from logger.logger_service import LoggingMeta

# TSHARK_PATH = r'C:\Users\aragn\Downloads\WiresharkPortable64\App\Wireshark\tshark.exe'


class FilterConfig:
    """
    FilterConfig represents filtering parameters for test_suite packet extraction
    """

    src_ip: str | None
    dst_ip: str | None
    src_ip_list: list[str] | None
    dst_ip_list: list[str] | None
    packet_type: str | None
    message_method: list | None
    http_status_code: int | None
    after_timestamp: float | None = None
    header_part: str | None = None
    body_part: str | None = None

    def __init__(
        self,
        src_ip: str | None = None,
        dst_ip: str | None = None,
        packet_type: str | None = None,
        message_method: list | None = None,
        http_status_code: int | None = None,
        after_timestamp: float | None = None,
        header_part: str | None = None,
        body_part: str | None = None,
        src_ip_list: list[str] | None = None,
        dst_ip_list: list[str] | None = None,
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
    ):
        """
        Initialize the PcapService.
        :param pcap_file: The str file path to the pcap file
        """
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
            custom_params = ["-o", f"tls.keylog_file:{ssl_keys_file_path}"]

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
        def match_packet(packet):
            # Check IP source and destination conditions
            if config.src_ip and (
                not hasattr(packet, "ip") or packet.ip.src != config.src_ip
            ):
                return False
            if config.src_ip_list and (
                not hasattr(packet, "ip") or packet.ip.src not in config.src_ip_list
            ):
                return False
            if config.dst_ip and (
                not hasattr(packet, "ip") or packet.ip.dst != config.dst_ip
            ):
                return False
            if config.dst_ip_list and (
                not hasattr(packet, "ip") or packet.ip.dst not in config.dst_ip_list
            ):
                return False

            # Check packet type (handle both HTTP and HTTP/JSON)
            packet_layer = (
                getattr(packet, config.packet_type, None)
                if config.packet_type
                else None
            )
            if config.packet_type and packet_layer is None:
                # For HTTP, also check for HTTP/JSON variant
                if config.packet_type == PacketTypeEnum.HTTP:
                    packet_layer = getattr(packet, "HTTP/JSON", None)
                if packet_layer is None:
                    return False

            # Check message methods (SIP/HTTP methods)
            if config.message_method and packet_layer:
                method = getattr(packet_layer, "method", None) or getattr(
                    packet_layer, "request_method", None
                )
                if method not in config.message_method:
                    return False

            # Check HTTP status code
            if config.http_status_code and packet_layer:
                response_code = getattr(packet_layer, "response_code", None)
                if response_code != str(config.http_status_code):
                    return False

            # Check timestamp condition
            if config.after_timestamp and (
                not hasattr(packet, "sniff_timestamp")
                or float(packet.sniff_timestamp) <= config.after_timestamp
            ):
                return False

            # Check request URI header # TODO check if other headers needs to be checked
            if config.header_part and packet_layer:
                header = getattr(packet_layer, "r_uri", None)
                if header and config.header_part.lower() not in str(header).lower():
                    return False

            # Check body
            if config.body_part and packet_layer:
                body = getattr(packet_layer, "msg_body", None)
                if body and config.body_part.lower() not in body.lower():
                    return False

            return True

        if self.capture is not None:
            result = [pkt for pkt in self.capture if match_packet(pkt)]
        else:
            result = []

        self._log_filtering_result(config=config, result=result)

        return result
