import argparse
from http_server import run_http_server


def _csv_list(value: str):
    """
    Accept:
      - single value: "POST"
      - accidental list-string: "['POST','GET']"
    """
    if value is None:
        return []

    s = str(value).strip()

    # strip list artifacts early: [ ... ]
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    else:
        return [value]

    # strip wrapping quotes
    if (s.startswith("'") and s.endswith("'")) or (
        s.startswith('"') and s.endswith('"')
    ):
        s = s[1:-1]

    return [x.strip().strip("'\"") for x in s.split(",") if x.strip()]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--role", choices=["SENDER", "RECEIVER", "IUT"], required=True)
    parser.add_argument("--target_uri", default=None)
    parser.add_argument("--target_prefix", default=None)

    # Backward compatible:
    # - single: --path=/LogEvents --method=POST --body="file...." --response_code=201
    # - multi:  --path=/LogEvents,/Versions --method=POST,GET --body=file1,file2 --response_code=201,200
    parser.add_argument("--path", default="/")
    parser.add_argument("--method", default="POST")
    parser.add_argument("--response_code", default=None)  # NEW (optional)

    parser.add_argument("--body", default=None)

    parser.add_argument("--content_type", default=None)

    # TLS / mTLS
    parser.add_argument("--tls_min", choices=["1.2", "1.3"], default=None)
    parser.add_argument("--tls_max", choices=["1.2", "1.3"], default=None)

    # For RECEIVER (HTTPS server cert/key)
    parser.add_argument("--server_cert", default=None, help="PEM server certificate")
    parser.add_argument("--server_key", default=None, help="PEM server private key")

    # For SENDER (client auth + server verify)
    parser.add_argument("--cert", default=None, help="PEM client certificate")
    parser.add_argument("--cert_key", default=None, help="PEM client private key")

    parser.add_argument(
        "--ca", default=None, help="PEM CA bundle/file to verify server"
    )
    parser.add_argument(
        "--require_client_cert",
        action="store_true",
        help="Receiver: require client certificate (mTLS). Use with --ca",
    )

    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable certificate verification (not recommended)",
    )
    parser.add_argument(
        "--keylog",
        default=None,
        help="Path to NSS-style TLS key log file (for Wireshark/tshark decryption)",
    )

    parser.add_argument("--run_in_background", default="False")

    args = parser.parse_args()

    # Normalize to lists (for RECEIVER multi-route support)
    # Keep original single-value fields too; http_server will handle both.
    args._paths_list = _csv_list(args.path) or ["/"]
    args._methods_list = [m.upper() for m in (_csv_list(args.method) or ["POST"])]
    args._codes_list = _csv_list(args.response_code)  # may be empty
    args._bodies_list = _csv_list(args.body)  # may be empty
    args._content_types_list = _csv_list(args.content_type)  # optional per-route

    return args


if __name__ == "__main__":
    args = parse_args()
    run_http_server(args)
