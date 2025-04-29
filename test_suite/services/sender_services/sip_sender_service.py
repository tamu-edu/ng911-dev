import socket
import logging
from enum import Enum


class SupportedProtocols(Enum):
    TCP = "TCP"  # Transmission Control Protocol
    UDP = "UDP"  # User Datagram Protocol

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class SipSenderService:
    def __init__(self, server_ip: str, server_port: int, protocol: str = "UDP", timeout: float = 5.0):
        """
        Initialize the SIP Sender Service.

        :param server_ip: IP address of the SIP server
        :param server_port: Port of the SIP server
        :param protocol: Protocol to use ('UDP' or 'TCP')
        :param timeout: Socket timeout in seconds (default: 5.0)
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.protocol = protocol.upper()

        if self.protocol not in SupportedProtocols.list():
            raise ValueError("Unsupported protocol. Use 'UDP' or 'TCP'.")

        self.sock = socket.socket(socket.AF_INET, self._get_socket_type())
        self.sock.settimeout(timeout)  # Set a timeout for the socket

        if self.protocol == SupportedProtocols.TCP.value:
            self._connect_tcp()

    def _get_socket_type(self) -> int:
        return socket.SOCK_STREAM if self.protocol == SupportedProtocols.TCP.value else socket.SOCK_DGRAM

    def _connect_tcp(self):
        """Connect to the server for TCP connections."""
        try:
            self.sock.connect((self.server_ip, self.server_port))
            logging.info(f"Connected to {self.server_ip}:{self.server_port} via TCP")
        except socket.error as e:
            logging.error(f"TCP connection error: {e}")
            raise

    def send_sip_message(self, sip_message: str):
        """
        Send the SIP message to the server.

        :param sip_message: The SIP message as a string
        """
        try:
            if self.protocol == SupportedProtocols.UDP.value:
                self.sock.sendto(sip_message.encode(), (self.server_ip, self.server_port))
                logging.info(f"SIP message sent via UDP to {self.server_ip}:{self.server_port}")
            elif self.protocol == SupportedProtocols.TCP.value:
                self.sock.sendall(sip_message.encode())
                logging.info(f"SIP message sent via TCP to {self.server_ip}:{self.server_port}")
        except socket.error as e:
            logging.error(f"Failed to send SIP message: {e}")
            raise

    def close(self):
        """
        Close the connection (for TCP) or socket (for UDP).
        """
        try:
            self.sock.close()
            logging.info(f"Connection closed for {self.protocol}")
        except Exception as e:
            logging.error(f"Error while closing socket: {e}")

    def __enter__(self):
        """Enable `with` statement support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup after use."""
        self.close()


# Example Usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    with SipSenderService("192.168.1.10", 5060, "UDP") as sip_sender:
        sip_sender.send_sip_message("REGISTER sip:example.com SIP/2.0")