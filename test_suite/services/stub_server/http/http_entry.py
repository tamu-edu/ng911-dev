import argparse
from http_server import run_http_server


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--role", choices=["SENDER", "RECEIVER", "IUT"], required=True)
    parser.add_argument("--target_uri", default=None)
    parser.add_argument("--path", default="/")
    parser.add_argument("--method", default="POST")
    parser.add_argument("--body", default=None)
    parser.add_argument("--content_type", default=None)
    parser.add_argument("--cert", default=None, help="Path to client certificate file (PEM format)")
    parser.add_argument("--cert_key", default=None, help="Path to client private key file (PEM format)")
    parser.add_argument("--run_in_background", default="False")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_http_server(args)
