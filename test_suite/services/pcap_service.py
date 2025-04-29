import os
import struct
import subprocess
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
            body_part: str | None = None
    ):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.packet_type = packet_type
        self.message_method = message_method
        self.http_status_code = http_status_code
        self.after_timestamp = after_timestamp
        self.header_part = header_part
        self.body_part = body_part


class PcapCaptureService(metaclass=LoggingMeta):
    def __init__(self, pcap_file: str | None = None, capture=None, ssl_keys_file_path: str | None = None):
        """
        Initialize the PcapService.
        :param pcap_file: The str file path to the pcap file
        """
        if capture is None and pcap_file is None:
            raise ValueError("You should provide either path to a pcap file or a capture file")
        if pcap_file is not None and capture is not None:
            warnings.warn("You have provided both a path and a capture file. "
                          "Priority goes to the capture file", UserWarning)

        self.capture = None
        if capture is not None:
            self.capture = capture
        elif pcap_file is not None:
            self._get_reassembled_capture(pcap_file, ssl_keys_file_path)

    def _get_reassembled_capture(self, pcap_file, ssl_keys_file_path: str | None = None):
        """
        Reads the test_suite file, reassembles TCP and UDP streams.
        :param pcap_file: The path to the pcap file
        :param ssl_keys_file_path: The path to file with ssl keys
        :return: pyshark FileCapture object
        """
        print("🟡 Preparing a FileCapture from {}".format(pcap_file))
        custom_params = None
        if ssl_keys_file_path and len(ssl_keys_file_path) > 0:
            custom_params = ['-o', f'tls.keylog_file:{ssl_keys_file_path}']

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
        return self.get_messages_by_config(
            FilterConfig(
                packet_type=PacketTypeEnum.SIP
            )
        )

    # def get_messages_by_config(self, config: FilterConfig):
    #     messages = [
    #         capture_packet for capture_packet in self.capture
    #         if (config.src_ip is None or (hasattr(capture_packet, "ip") and capture_packet.ip.src == config.src_ip))
    #            and (config.dst_ip is None or (hasattr(capture_packet, "ip") and capture_packet.ip.dst == config.dst_ip))
    #            and (config.packet_type is None or hasattr(capture_packet, config.packet_type))
    #            and (
    #                # if there is no packet_type we do not know where to check method, so method would be ignored
    #                    (config.message_method is None or config.packet_type is None)
    #                    or (
    #                            hasattr(capture_packet, config.packet_type)
    #                            and hasattr(getattr(capture_packet, config.packet_type), "method")
    #                            and getattr(getattr(capture_packet, config.packet_type),
    #                                        "method") in config.message_method
    #                    )
    #                    or (
    #                            hasattr(capture_packet, config.packet_type)
    #                            and hasattr(getattr(capture_packet, config.packet_type), "request_method")
    #                            and getattr(getattr(capture_packet, config.packet_type),
    #                                        "request_method") in config.message_method
    #                    )
    #            )
    #            and (
    #                    (config.http_status_code is None or config.packet_type is None)
    #                    or (
    #                            hasattr(capture_packet, config.packet_type)
    #                            and hasattr(getattr(capture_packet, config.packet_type), "response_code")
    #                            and getattr(getattr(capture_packet, config.packet_type),
    #                                        "response_code") == str(config.http_status_code)
    #                    )
    #            )
    #            and (config.after_timestamp is None or (
    #                 hasattr(capture_packet, "sniff_timestamp")
    #                 and float(capture_packet.sniff_timestamp) > config.after_timestamp)
    #                 )
    #     ]
    #     return messages

    def get_messages_by_config(self, config: FilterConfig):
        def match_packet(packet):
            # Check IP source and destination conditions
            if config.src_ip and (not hasattr(packet, "ip") or packet.ip.src != config.src_ip):
                return False
            if config.dst_ip and (not hasattr(packet, "ip") or packet.ip.dst != config.dst_ip):
                return False

            # Check packet type
            packet_layer = getattr(packet, config.packet_type, None) if config.packet_type else None
            if config.packet_type and packet_layer is None:
                return False

            # Check message methods (SIP/HTTP methods)
            if config.message_method and packet_layer:
                method = getattr(packet_layer, "method", None) or getattr(packet_layer, "request_method", None)
                if method not in config.message_method:
                    return False

            # Check HTTP status code
            if config.http_status_code and packet_layer:
                response_code = getattr(packet_layer, "response_code", None)
                if response_code != str(config.http_status_code):
                    return False

            # Check timestamp condition
            if config.after_timestamp and (not hasattr(packet, "sniff_timestamp") or float(
                    packet.sniff_timestamp) <= config.after_timestamp):
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

        return [pkt for pkt in list(self.capture) if match_packet(pkt)]
