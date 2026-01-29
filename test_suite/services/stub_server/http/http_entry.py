import argparse
from http_server import run_http_server


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--role", choices=["SENDER", "RECEIVER", "IUT"], required=True)
    parser.add_argument("--target_uri", default=None)
    parser.add_argument("--target_prefix", default=None)
    parser.add_argument("--path", default="/")
    parser.add_argument("--method", default="POST")
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

    parser.add_argument("--ca", default=None, help="PEM CA bundle/file to verify server")
    # add this flag near other TLS args
    parser.add_argument("--require_client_cert", action="store_true",
                        help="Receiver: require client certificate (mTLS). Use with --ca")

    parser.add_argument("--insecure", action="store_true", help="Disable certificate verification (not recommended)")
    parser.add_argument("--keylog", default=None,
                        help="Path to NSS-style TLS key log file (for Wireshark/tshark decryption)")

    parser.add_argument("--run_in_background", default="False")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_http_server(args)
