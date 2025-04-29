import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def _handle_request(self, method):
        """Common request handling logic for all HTTP methods."""
        content_length = int(self.headers.get("Content-Length", 0))
        request_body = self.rfile.read(content_length).decode() if content_length > 0 else None

        print(f"Received {method} request from {self.client_address}: {request_body if request_body else 'No body'}")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response_message = {"status": "success", "method": method, "received": request_body}
        self.wfile.write(json.dumps(response_message).encode("utf-8"))

    def do_GET(self): self._handle_request("GET")

    def do_POST(self): self._handle_request("POST")

    def do_PUT(self): self._handle_request("PUT")

    def do_DELETE(self): self._handle_request("DELETE")


class HttpReceiverService:
    def __init__(self, host: str, port: int, use_ssl: bool = False, cert_file: str = None, key_file: str = None):
        """
        Initialize HTTP Receiver Service.
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.cert_file = cert_file
        self.key_file = key_file
        self.server = HTTPServer((self.host, self.port), SimpleHTTPRequestHandler)
        self.running = False

        if self.use_ssl and self.cert_file and self.key_file:
            self.server.socket = ssl.wrap_socket(
                self.server.socket, keyfile=self.key_file, certfile=self.cert_file, server_side=True
            )
            print(f"HTTPS Receiver listening on {self.host}:{self.port}")
        else:
            print(f"HTTP Receiver listening on {self.host}:{self.port}")

    def start(self):
        """Start the HTTP server in a separate thread."""
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        print("HTTP(S) Receiver Service Started.")

    def _run_server(self):
        """Run the server, handling requests."""
        while self.running:
            self.server.handle_request()  # ✅ Handle one request at a time, allowing graceful shutdown

    def stop(self):
        """Stop the HTTP server gracefully."""
        self.running = False
        try:
            # Send a dummy request to unblock the server
            with socket.create_connection((self.host, self.port)):
                pass
        except OSError:
            pass  # Server already stopped

        self.server.server_close()
        print("HTTP(S) Receiver Service Stopped.")