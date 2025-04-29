import socket
import threading
from services.sender_services.sip_sender_service import SupportedProtocols


class SipReceiverService:
    def __init__(self, listen_ip: str, listen_port: int, protocol: str = 'UDP'):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.protocol = protocol.upper()
        self.running = False

        if self.protocol not in SupportedProtocols.list():
            raise ValueError("Unsupported protocol. Use 'UDP' or 'TCP'.")

        self.sock = socket.socket(socket.AF_INET, self._get_socket_type())
        self.sock.settimeout(1)  # Set timeout to allow graceful shutdown

    def _get_socket_type(self) -> int:
        return socket.SOCK_STREAM if self.protocol == "TCP" else socket.SOCK_DGRAM

    def start(self):
        """Start the SIP receiver service."""
        self.running = True
        self.sock.bind((self.listen_ip, self.listen_port))

        if self.protocol == "TCP":
            self.sock.listen(5)
            print(f"SIP Receiver listening on {self.listen_ip}:{self.listen_port} over TCP")
            self._handle_tcp_connections()
        else:
            print(f"SIP Receiver listening on {self.listen_ip}:{self.listen_port} over UDP")
            self._handle_udp_messages()

    def start_in_thread(self):
        """Start the receiver in a new thread."""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread

    def _handle_udp_messages(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                print(f"Received SIP message from {addr}: {data.decode()}")
            except socket.timeout:
                continue  # Allows thread to check `self.running` condition
            except socket.error as e:
                if not self.running:
                    break  # Exit gracefully when stopped
                print(f"Socket error: {e}")

    def _handle_tcp_connections(self):
        while self.running:
            try:
                conn, addr = self.sock.accept()
                print(f"New SIP connection from {addr}")
                threading.Thread(target=self._handle_tcp_client, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except socket.error as e:
                if not self.running:
                    break
                print(f"Socket error: {e}")

    def _handle_tcp_client(self, conn, addr):
        with conn:
            while self.running:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    print(f"Received SIP message from {addr}: {data.decode()}")
                except socket.timeout:
                    continue
                except socket.error as e:
                    if not self.running:
                        break
                    print(f"Socket error: {e}")

    def stop(self):
        """Stop the SIP receiver service."""
        self.running = False
        self.sock.close()
        print("SIP Receiver stopped.")