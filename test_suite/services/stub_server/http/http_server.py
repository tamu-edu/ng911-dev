import http.server
import socketserver
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import json


class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, **kwargs):
        self.source_ip = source_ip
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_ip, 0)
        self.poolmanager = PoolManager(*args, **kwargs)


def run_http_server(args):
    if args.role == "RECEIVER":
        class CustomHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                print(f"[RECEIVER] Received: {post_data.decode()}")

                # Simulate expected response
                self.send_response(int(args.expected_response_code or 200))
                self.end_headers()
                self.wfile.write(b"OK")

        with socketserver.TCPServer((args.ip, args.port), CustomHandler) as httpd:
            print(f"[HTTP RECEIVER] Listening on {args.ip}:{args.port}")
            httpd.serve_forever()

    elif args.role == "SENDER":
        # Use the alias IP as source
        session = requests.Session()
        session.mount("http://", SourceIPAdapter(args.ip))

        body = args.body or ""
        headers = {"Content-Type": "application/json"}
        full_url = f"{args.target_uri}{args.path}"

        print(f"[SENDER] Sending from {args.ip} → {full_url}")
        try:
            response = session.post(full_url, data=body.encode(), headers=headers)
            print(f"[SENDER] Got response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[SENDER] Request failed: {e}")

    elif args.role == "IUT":
        print("[IUT] Behavior not defined yet — extend as needed.")
