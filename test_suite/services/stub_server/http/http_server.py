import http.server
import socketserver
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl


def _strip_cli_artifacts(s: str) -> str | None:
    """
    Defensive cleanup for CLI-passed values.
    Removes surrounding [], quotes, and whitespace.
    Examples:
      "['/test']" -> "/test"
      "'/test'"   -> "/test"
      '"/test"'   -> "/test"
    """
    if s is None:
        return s
    s = str(s).strip()

    # remove wrapping brackets
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]

    # remove wrapping quotes (single or double)
    if (s.startswith("'") and s.endswith("'")) or (
        s.startswith('"') and s.endswith('"')
    ):
        s = s[1:-1]

    return s.strip()


def _mk_ssl_ctx_for_server(args):
    if not args.server_cert or not args.server_key:
        return None  # plain HTTP

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # pin min/max versions if requested
    if args.tls_min:
        ctx.minimum_version = (
            ssl.TLSVersion.TLSv1_3 if args.tls_min == "1.3" else ssl.TLSVersion.TLSv1_2
        )
    if args.tls_max:
        ctx.maximum_version = (
            ssl.TLSVersion.TLSv1_3 if args.tls_max == "1.3" else ssl.TLSVersion.TLSv1_2
        )

    if getattr(args, "keylog", None):
        ctx.keylog_filename = args.keylog

    ctx.load_cert_chain(certfile=args.server_cert, keyfile=args.server_key)

    if getattr(args, "require_client_cert", False):
        if not args.ca:
            raise ValueError("--require_client_cert requires --ca")
        ctx.load_verify_locations(cafile=args.ca)
        ctx.verify_mode = ssl.CERT_REQUIRED

    return ctx


# class ReuseTCPServer(socketserver.TCPServer):
#     allow_reuse_address = True


class ReuseTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, ssl_context=None, **kwargs):
        self.source_ip = source_ip
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = (self.source_ip, 0)
        if self.ssl_context is not None:
            kwargs["ssl_context"] = self.ssl_context
        self.poolmanager = PoolManager(*args, **kwargs)


def _normalize_path(p: str) -> str:
    if p is None:
        return "/"

    if not p:
        return "/"

    if p:
        p = _strip_cli_artifacts(p) or ""

        if not p.startswith("/"):
            p = "/" + p

        # normalize trailing slash ("/x/" → "/x")
        if len(p) > 1 and p.endswith("/"):
            p = p[:-1]

    return p


def _read_body_once(body_spec: str) -> bytes:
    """
    body_spec:
      - None/empty -> b"OK"
      - "file./path/to.json" -> file contents
      - otherwise -> literal string bytes
    """
    if not body_spec:
        return b"OK"
    s = str(body_spec).strip()
    if s.lower().startswith("file."):
        path = s[5:]
        with open(path, "rb") as f:
            return f.read()
    return s.encode("utf-8")


def _build_routes(args):
    """
    Build routing table:
      (METHOD, PATH) -> {code:int, body:bytes, content_type:str}

    Index-based mapping:
      methods[i], paths[i], codes[i], bodies[i], content_types[i]
    If lists differ in length, we allow:
      - codes/bodies/content_types can be length 1 (broadcast)
      - otherwise must match methods/paths length
    """
    methods = getattr(args, "_methods_list", None) or [str(args.method).upper()]
    paths = getattr(args, "_paths_list", None) or [str(args.path)]
    paths = [_normalize_path(p) for p in paths]

    # If user provided multiple paths but only one method (or vice versa),
    # we allow broadcasting the single item.
    if len(methods) == 1 and len(paths) > 1:
        methods = methods * len(paths)
    if len(paths) == 1 and len(methods) > 1:
        paths = paths * len(methods)

    if len(methods) != len(paths):
        raise ValueError(
            f"HTTP RECEIVER config mismatch: methods={len(methods)} paths={len(paths)}"
        )

    n = len(methods)

    # response codes
    codes_raw = getattr(args, "_codes_list", None) or []
    if (
        len(codes_raw) == 0
        and getattr(args, "expected_response_code", None) is not None
    ):
        # legacy field, if exists somewhere else
        codes_raw = [str(args.expected_response_code)]
    # bodies
    bodies_raw = getattr(args, "_bodies_list", None) or []
    # content types
    cts_raw = getattr(args, "_content_types_list", None) or []

    def broadcast_or_validate(lst, name):
        if len(lst) == 0:
            return [None] * n
        if len(lst) == 1:
            return lst * n
        if len(lst) != n:
            raise ValueError(
                f"HTTP RECEIVER config mismatch: {name}={len(lst)} expected {n} (or 1)"
            )
        return lst

    codes_raw = broadcast_or_validate(codes_raw, "response_code") or ""
    bodies_raw = broadcast_or_validate(bodies_raw, "body") or ""
    cts_raw = broadcast_or_validate(cts_raw, "content_type")

    # default status codes if not provided
    default_codes = {
        "GET": 200,
        "POST": 201,
        "PUT": 200,
        "DELETE": 204,
    }

    routes = {}
    for i in range(n):
        m = str(methods[i]).upper()
        p = _normalize_path(paths[i])

        code = (
            int(codes_raw[i])
            if codes_raw[i] is not None
            else int(default_codes.get(m, 200))
        )
        body_bytes = _read_body_once(bodies_raw[i])
        ct = cts_raw[i] or (args.content_type or "application/json")

        # allow multiple identical responses (same key) -> last one wins (safe)
        routes[(m, p)] = {"code": code, "body": body_bytes, "content_type": ct}

    return routes


def run_http_server(args):
    if args.role == "RECEIVER":
        routes = _build_routes(args)

        print("[HTTP RECEIVER] Routes:")
        for (m, p), v in routes.items():
            print(
                f"  - {m} {p} -> {v['code']} ({len(v['body'])} bytes, {v['content_type']})"
            )

        class CustomHandler(http.server.BaseHTTPRequestHandler):
            def _handle_request(self):
                # Read request body (for visibility/debug)
                content_length = int(self.headers.get("Content-Length", 0))
                req_body = (
                    self.rfile.read(content_length) if content_length > 0 else b""
                )

                req_path = _normalize_path(
                    self.path.split("?", 1)[0]
                )  # ignore query for routing
                key = (self.command.upper(), req_path)

                print(f"[RECEIVER] {self.command} {self.path}")
                if req_body:
                    print(f"[RECEIVER] Body: {req_body.decode(errors='replace')}")

                if key not in routes:
                    # 404 fallback
                    msg = f"Not Found: {key[0]} {req_path}".encode("utf-8")
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Content-Length", str(len(msg)))
                    self.end_headers()
                    self.wfile.write(msg)
                    return

                _resp = routes[key]
                status_code = int(_resp["code"])
                response_body = _resp["body"]
                content_type = _resp["content_type"] or "application/json"

                self.send_response(status_code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                if status_code != 204:
                    self.wfile.write(response_body)

            # fmt: off
            def do_GET(self):
                self._handle_request()

            def do_POST(self):
                self._handle_request()

            def do_PUT(self):
                self._handle_request()

            def do_DELETE(self):
                self._handle_request()
            # fmt: on

            # fmt: on
            # silence default http.server noisy logs (optional)
            def log_message(self, format, *args):
                return

        with ReuseTCPServer((args.ip, args.port), CustomHandler) as httpd:
            server_ctx = _mk_ssl_ctx_for_server(args)
            if server_ctx:
                httpd.socket = server_ctx.wrap_socket(httpd.socket, server_side=True)
                print(f"[HTTPS RECEIVER] Listening on https://{args.ip}:{args.port}")
            else:
                print(f"[HTTP RECEIVER] Listening on http://{args.ip}:{args.port}")

            httpd.serve_forever()

    elif args.role == "SENDER":
        # Build client SSL context
        ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

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
            ssl_ctx.minimum_version = (
                ssl.TLSVersion.TLSv1_3
                if args.tls_min == "1.3"
                else ssl.TLSVersion.TLSv1_2
            )
        if args.tls_max:
            ssl_ctx.maximum_version = (
                ssl.TLSVersion.TLSv1_3
                if args.tls_max == "1.3"
                else ssl.TLSVersion.TLSv1_2
            )

        # Client certificate (mTLS)
        cert_tuple = (
            (args.cert, args.cert_key) if (args.cert and args.cert_key) else None
        )

        session = requests.Session()

        scheme = "https" if args.target_uri.lower().startswith("https://") else "http"
        session.mount(f"{scheme}://", SourceIPAdapter(args.ip, ssl_context=ssl_ctx))

        method = str(args.method).upper()
        headers = {"Content-Type": args.content_type or "application/json"}

        full_url = (
            f"{args.target_uri.removesuffix('/')}/{str(args.path).removeprefix('/')}"
        )

        _tp = (args.target_prefix or "").strip()
        if _tp and _tp.lower() != "none":
            full_url = (
                f"{args.target_uri.removesuffix('/')}/"
                f"{_tp.removeprefix('/').removesuffix('/')}/"
                f"{str(args.path).removeprefix('/')}"
            )

        request_args = {
            "url": full_url,
            "headers": headers,
            "cert": cert_tuple,
            "verify": (False if args.insecure else (args.ca if args.ca else True)),
            "timeout": (5, 15),
        }
        if method in ("POST", "PUT"):
            request_args["data"] = (args.body or "").encode()

        print(f"[SENDER] {method} from {args.ip} → {full_url}")
        try:
            resp = session.request(method, **request_args)
            print(f"[SENDER] Response: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"[SENDER] Request failed: {e}")

    elif args.role == "IUT":
        print("[IUT] Not implemented yet — extend here.")
