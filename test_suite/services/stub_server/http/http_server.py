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
            def _handle_request(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b''

                print(f"[RECEIVER] {self.command} {self.path}")
                if body:
                    print(f"[RECEIVER] Body: {body.decode()}")

                # Determine default status code
                default_codes = {
                    "GET": 200,
                    "POST": 201,
                    "PUT": 200,
                    "DELETE": 204,
                }
                status_code = int(getattr(args, "expected_response_code", default_codes.get(self.command, 200)))

                response_body = (args.body or "OK").encode()
                content_type = args.content_type or "text/plain"

                self.send_response(status_code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                if status_code != 204:
                    self.wfile.write(response_body)

            def do_GET(self): self._handle_request()
            def do_POST(self): self._handle_request()
            def do_PUT(self): self._handle_request()
            def do_DELETE(self): self._handle_request()

        with socketserver.TCPServer((args.ip, args.port), CustomHandler) as httpd:
            print(f"[HTTP RECEIVER] Listening on {args.ip}:{args.port}")
            httpd.serve_forever()

    elif args.role == "SENDER":
        session = requests.Session()
        method = args.method.upper()
        headers = {"Content-Type": args.content_type or "application/json"}
        full_url = f"{args.target_uri}{args.path}"
        cert_tuple = (args.cert, args.cert_key) if args.cert and args.cert_key else None

        protocol = "https" if cert_tuple else "http"
        session.mount(f"{protocol}://", SourceIPAdapter(args.ip))

        request_args = {
            "url": full_url,
            "headers": headers,
            "cert": cert_tuple,
            "verify": False,
        }

        if method in ("POST", "PUT"):
            request_args["data"] = args.body.encode() if args.body else b''

        print(f"[SENDER] Sending {method} from {args.ip} → {full_url}")
        try:
            response = session.request(method, **request_args)
            print(f"[SENDER] Response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[SENDER] Request failed: {e}")

    elif args.role == "IUT":
        print("[IUT] Not implemented yet — extend here.")
