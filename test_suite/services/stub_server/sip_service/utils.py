import ipaddress
import random  # nosec B311
import string

DEFAULT_SRTP_PROFILE = "AES_CM_128_HMAC_SHA1_80"

DEFAULT_DTLS_SRTP_PROFILES = "SRTP_AES128_CM_SHA1_80:" "SRTP_AES128_CM_SHA1_32"


def gen_call_id_host(
    local_ip: str,
) -> str:
    return local_ip


def gen_call_id(
    local_ip: str,
) -> str:
    rand = "".join(
        random.choices(
            string.ascii_letters + string.digits,
            k=10,
        )
    )

    return f"{rand}@" f"{gen_call_id_host(local_ip)}"


def gen_tag():
    return "".join(
        random.choices(
            string.hexdigits,
            k=8,
        )
    )


def _ip_type(
    ip: str,
) -> str:
    """
    Return '4' or '6' depending on IP version.
    """
    try:
        return "6" if ipaddress.ip_address(ip).version == 6 else "4"
    except Exception:
        return "4"


def default_vars(
    bind,
    remote,
    rtp_bind,
    rtp_remote,
):
    local_ip = bind[0]

    rtp_ip = rtp_bind[0] if rtp_bind else local_ip

    rtp_port = str(rtp_bind[1]) if rtp_bind else "0"

    vars = {
        "local_ip": local_ip,
        "local_port": str(bind[1]),
        "remote_ip": (remote[0] if remote else ""),
        "remote_port": (str(remote[1]) if remote else ""),
        "call_id": gen_call_id(local_ip),
        "from_tag": gen_tag(),
        "to_tag": gen_tag(),
        "cseq": "1",
        "transport": "",
        "call_number": "",
        "peer_tag_param": "",
        # Plain RTP variables.
        "rtp_local_ip": rtp_ip,
        "rtp_local_port": rtp_port,
        "rtp_remote_ip": (rtp_remote[0] if rtp_remote else ""),
        "rtp_remote_port": (str(rtp_remote[1]) if rtp_remote else ""),
        # Common media variables.
        "media_ip": rtp_ip,
        "media_port": rtp_port,
        "media_protocol": "",
        "media_formats": "",
        "media_security_mode": "rtp",
        "media_rtcp_port": "",
        "media_rtcp_ip": "",
        "media_rtcp_mux": "false",
        "local_ip_type": _ip_type(local_ip),
        "media_ip_type": _ip_type(rtp_ip),
        # Standalone SDES-SRTP.
        #
        # These values are intentionally independent from DTLS.
        "srtp_profile": (DEFAULT_SRTP_PROFILE),
        "srtp_tx_key": "",
        "srtp_rx_key": "",
        "srtp_remote_profile": "",
        "srtp_remote_key": "",
        "srtp_crypto_tag": "1",
        # DTLS-SRTP.
        #
        # DTLS derives SRTP keys; it does not use the explicit
        # srtp_tx_key/srtp_rx_key values above.
        "dtls_role": "client",
        "dtls_remote_setup": "",
        "dtls_certificate_file": "",
        "dtls_private_key_file": "",
        "dtls_fingerprint_algorithm": ("sha-256"),
        "dtls_local_fingerprint": "",
        "dtls_remote_fingerprint": "",
        "dtls_srtp_profiles": (DEFAULT_DTLS_SRTP_PROFILES),
        "dtls_cipher_list": "DEFAULT",
        "dtls_handshake_timeout": "10",
    }

    return vars
