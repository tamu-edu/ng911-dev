#!/usr/bin/env python3
import argparse
import os
import sys

from sip_server import SIPStubServerService


def parse_args():
    # Rewrite "set NAME VALUE" triplets into "--set NAME VALUE" so users can type:
    #   python3 sip_entry.py ... set foo 123 set bar ABC
    argv = sys.argv[1:]
    rewritten = []
    i = 0
    while i < len(argv):
        if argv[i] == "set" and (i + 2) < len(argv):
            rewritten.extend(["--set", argv[i + 1], argv[i + 2]])
            i += 3
        else:
            rewritten.append(argv[i])
            i += 1

    p = argparse.ArgumentParser("sip_entry")
    # SIP bind/remote
    p.add_argument("--bind-ip", required=True)
    p.add_argument("--bind-port", type=int, required=True)
    p.add_argument("--remote-ip")
    p.add_argument("--remote-port", type=int)
    p.add_argument("--protocol", choices=["UDP", "TCP", "TLS"], default="UDP")

    # Scenario
    p.add_argument("--scenario", required=True, help="Path to YAML IR or SIPp XML")
    p.add_argument("--scenario-type", choices=["auto", "yaml", "sipp"], default="auto")

    # RTP (optional)
    p.add_argument("--rtp-bind-ip")
    p.add_argument("--rtp-bind-port", type=int)
    p.add_argument("--rtp-remote-ip")
    p.add_argument("--rtp-remote-port", type=int)

    # TLS / mTLS
    p.add_argument("--tls-cert")
    p.add_argument("--tls-key")
    p.add_argument("--tls-ca")
    p.add_argument("--require-client-cert", action="store_true")
    p.add_argument("--tls-keylog-file")

    # Misc
    p.add_argument("--log-file")
    p.add_argument("--log-level", default="INFO")
    p.add_argument("--message-timeout", type=float, default=5.0)
    p.add_argument("--transaction-timeout", type=float, default=32.0)

    # Variables:
    # 1) keep existing --var k=v
    p.add_argument("--var", action="append", default=[], help="k=v (repeatable)")
    # 2) NEW: --set NAME VALUE (repeatable); users can also write 'set NAME VALUE' via argv rewrite above
    p.add_argument("--set", dest="set_pairs", action="append", nargs=2, metavar=("NAME", "VALUE"), default=[])

    return p.parse_args(rewritten)


def main():
    a = parse_args()

    prev_sslkeylog = os.environ.get("SSLKEYLOGFILE")
    if a.tls_keylog_file:
        os.environ["SSLKEYLOGFILE"] = a.tls_keylog_file

    extra_vars = {}

    # Support --var k=v (existing)
    for kv in a.var:
        if "=" in kv:
            k, v = kv.split("=", 1)
            extra_vars[k] = v

    # Support --set NAME VALUE (or 'set NAME VALUE' rewritten)
    for name, value in (a.set_pairs or []):
        extra_vars[name] = value

    srv = SIPStubServerService(
        bind=(a.bind_ip, a.bind_port),
        remote=(a.remote_ip, a.remote_port) if a.remote_ip and a.remote_port else None,
        protocol=a.protocol,
        scenario_path=a.scenario,
        scenario_type=a.scenario_type,
        rtp_bind=(a.rtp_bind_ip, a.rtp_bind_port) if a.rtp_bind_ip and a.rtp_bind_port else None,
        rtp_remote=(a.rtp_remote_ip, a.rtp_remote_port) if a.rtp_remote_ip and a.rtp_remote_port else None,
        tls_cert=a.tls_cert, tls_key=a.tls_key, tls_ca=a.tls_ca,
        require_client_cert=a.require_client_cert,
        log_file=a.log_file, log_level=a.log_level,
        message_timeout=a.message_timeout, transaction_timeout=a.transaction_timeout,
        extra_vars=extra_vars,
    )

    try:
        srv.run()
    except KeyboardInterrupt:
        pass
    finally:
        if prev_sslkeylog is None:
            os.environ.pop("SSLKEYLOGFILE", None)
        else:
            os.environ["SSLKEYLOGFILE"] = prev_sslkeylog
        srv.shutdown()


if __name__ == "__main__":
    sys.exit(main())
