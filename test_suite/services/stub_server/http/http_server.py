import http.server
import socketserver
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import json
import ssl


def _mk_ssl_ctx_for_server(args):
    if not args.server_cert or not args.server_key:
        return None  # plain HTTP

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # pin min/max versions if requested
    if args.tls_min:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3 if args.tls_min == "1.3" else ssl.TLSVersion.TLSv1_2
    if args.tls_max:
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3 if args.tls_max == "1.3" else ssl.TLSVersion.TLSv1_2

    if getattr(args, "keylog", None):
        ctx.keylog_filename = args.keylog

    ctx.load_cert_chain(certfile=args.server_cert, keyfile=args.server_key)
    if getattr(args, "require_client_cert", False):
        if not args.ca:
            raise ValueError("--require_client_cert requires --ca")
        ctx.load_verify_locations(cafile=args.ca)
        ctx.verify_mode = ssl.CERT_REQUIRED

    return ctx


class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, ssl_context=None, **kwargs):
        self.source_ip = source_ip
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_ip, 0)
        if self.ssl_context is not None:
            kwargs['ssl_context'] = self.ssl_context
        self.poolmanager = PoolManager(*args, **kwargs)


def run_http_server(args):
    if args.role == "RECEIVER":
        class CustomHandler(http.server.BaseHTTPRequestHandler):
            def _handle_request(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b''

                print(f"[RECEIVER] {self.command} {self.path}")
                if body:
                    print(f"[RECEIVER] Body: {body.decode(errors='replace')}")

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

        with ReuseTCPServer((args.ip, args.port), CustomHandler) as httpd:
            server_ctx = _mk_ssl_ctx_for_server(args)
            if server_ctx:
                httpd.socket = server_ctx.wrap_socket(httpd.socket, server_side=True)
                print(f"[HTTPS RECEIVER] Listening on https://{args.ip}:{args.port} "
                      f"(TLS {server_ctx.minimum_version.name}..{server_ctx.maximum_version.name 
                      if server_ctx.maximum_version else 'MAX'})")
            else:
                print(f"[HTTP RECEIVER] Listening on http://{args.ip}:{args.port}")
            httpd.serve_forever()

    elif args.role == "SENDER":
        # Build client SSL context
        ssl_ctx = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH
        )

        if getattr(args, "keylog", None):
            ssl_ctx.keylog_filename = args.keylog

        # Server verification
        if args.insecure:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
        elif args.ca:
            ssl_ctx.load_verify_locations(cafile=args.ca)

        # Pin TLS versions
        if args.tls_min:
            ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_3 if args.tls_min == "1.3" else ssl.TLSVersion.TLSv1_2
        if args.tls_max:
            ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_3 if args.tls_max == "1.3" else ssl.TLSVersion.TLSv1_2

        # Client certificate (mTLS)
        cert_tuple = (args.cert, args.cert_key) if (args.cert and args.cert_key) else None

        session = requests.Session()

        # Determine scheme from target_uri, not from presence of certs
        # (you already pass http(s):// in target_uri)
        scheme = "https" if args.target_uri.lower().startswith("https://") else "http"
        session.mount(f"{scheme}://", SourceIPAdapter(args.ip, ssl_context=ssl_ctx))

        method = args.method.upper()
        headers = {"Content-Type": args.content_type or "application/json"}

        full_url = f"{args.target_uri.removesuffix('/')}/{args.path.removeprefix('/')}"

        _tp = args.target_prefix.strip()
        if _tp and _tp.lower() != "none":
            full_url = (f"{args.target_uri.removesuffix('/')}/"
                        f"{_tp.removeprefix('/').removesuffix('/')}/"
                        f"{args.path.removeprefix('/')}")

        request_args = {
            "url": full_url,
            "headers": headers,
            "cert": cert_tuple,
            "verify": (False if args.insecure else (args.ca if args.ca else True)),
            "timeout": (5, 15),
        }
        if method in ("POST", "PUT"):
            request_args["data"] = (args.body or "").encode()

        print(f"[SENDER] {method} from {args.ip} → {full_url} "
              f"(TLS {getattr(ssl_ctx, 'minimum_version', None)}..{getattr(ssl_ctx, 'maximum_version', None)})")
        try:
            resp = session.request(method, **request_args)
            print(f"[SENDER] Response: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[SENDER] Request failed: {e}")

    elif args.role == "IUT":
        print("[IUT] Not implemented yet — extend here.")
