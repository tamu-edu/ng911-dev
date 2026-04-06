import ipaddress
import random  # nosec B311
import string


def gen_call_id_host(local_ip: str) -> str:
    return local_ip


def gen_call_id(local_ip: str) -> str:
    rand = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"{rand}@{gen_call_id_host(local_ip)}"


def gen_tag():
    return "".join(random.choices(string.hexdigits, k=8))


def _ip_type(ip: str) -> str:
    """Return '4' or '6' depending on IP version (IPv4/IPv6)."""
    try:
        return "6" if ipaddress.ip_address(ip).version == 6 else "4"
    except Exception:
        return "4"


def default_vars(bind, remote, rtp_bind, rtp_remote):
    local_ip = bind[0]
    rtp_ip = rtp_bind[0] if rtp_bind else local_ip
    rtp_port = str(rtp_bind[1]) if rtp_bind else "0"

    vars = {
        "local_ip": local_ip,
        "local_port": str(bind[1]),
        "remote_ip": remote[0] if remote else "",
        "remote_port": str(remote[1]) if remote else "",
        "call_id": gen_call_id(local_ip),
        "from_tag": gen_tag(),
        "to_tag": gen_tag(),
        "cseq": "1",
        "rtp_local_ip": rtp_ip,
        "rtp_local_port": rtp_port,
        "rtp_remote_ip": rtp_remote[0] if rtp_remote else "",
        "rtp_remote_port": str(rtp_remote[1]) if rtp_remote else "",
        "transport": "",
        "call_number": "",
        "peer_tag_param": "",
        # auto-added media + ip types
        "media_ip": rtp_ip,
        "media_port": rtp_port,
        "local_ip_type": _ip_type(local_ip),
        "media_ip_type": _ip_type(rtp_ip),
    }
    return vars
