import logging
import re
from typing import Optional
import psutil
import subprocess
import ipaddress


def resolve_ts_host_ip(data_dict: dict, parent_data_dict: dict):
    """
    Tries to find test_suite_host_ip from provided dicts; falls back to best-effort local IP.
    """
    if isinstance(data_dict, dict) and data_dict.get("test_suite_host_ip"):
        return data_dict.get("test_suite_host_ip")
    if isinstance(parent_data_dict, dict) and parent_data_dict.get(
        "test_suite_host_ip"
    ):
        return parent_data_dict.get("test_suite_host_ip")
    return get_default_local_ipv4()


def get_default_local_ipv4():
    """
    Best-effort local IPv4 (non-loopback). Used as fallback if TS host ip is not provided.
    """
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name == "AF_INET":
                if addr.address and not addr.address.startswith("127."):
                    return addr.address
    return None


def get_ipv4_iface_info_by_ip(ip: str):
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name == "AF_INET" and addr.address == ip:
                return iface, addr.address, addr.netmask
    return None, None, None


def is_ip_in_same_subnet(local_ip: str, candidate_ip: str, mask: str | None):
    try:
        if not local_ip:
            return True, None
        if mask:
            net = ipaddress.IPv4Network((local_ip, mask), strict=False)
            return (ipaddress.IPv4Address(candidate_ip) in net), str(net)

        # infer mask from local_ip iface if mask not provided
        _, _, nm = get_ipv4_iface_info_by_ip(local_ip)
        if nm:
            net = ipaddress.IPv4Network((local_ip, nm), strict=False)
            return (ipaddress.IPv4Address(candidate_ip) in net), str(net)
    except Exception as e:
        _logger = logging.getLogger("LoggerService")
        _logger.debug(e)
    return True, None


def find_interface_for_ip(candidate_ip: str):
    target = ipaddress.IPv4Address(candidate_ip)
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name != "AF_INET":
                continue
            try:
                net = ipaddress.IPv4Network((addr.address, addr.netmask), strict=False)
                if target in net:
                    return iface, addr.netmask
            except Exception as e:
                _logger = logging.getLogger("LoggerService")
                _logger.debug(e)
                continue
    return None, None


def can_add_ip_alias(candidate_ip: str, mask: str | None = None):
    try:
        iface, inferred_nm = find_interface_for_ip(candidate_ip)
        if not iface:
            return False, "cannot find local interface for candidate IP subnet"
        if mask is None:
            mask = inferred_nm

        prefix = ipaddress.IPv4Network((candidate_ip, mask), strict=False).prefixlen

        add_res = subprocess.run(
            ["ip", "addr", "add", f"{candidate_ip}/{prefix}", "dev", iface],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        if add_res.returncode != 0:
            return False, (
                add_res.stderr.strip() or add_res.stdout.strip() or "ip addr add failed"
            )

        subprocess.run(
            ["ip", "addr", "del", f"{candidate_ip}/{prefix}", "dev", iface],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        return True, f"alias add/del OK on {iface}"
    except Exception as e:
        return False, str(e)


def is_ip_assigned_locally(ip: str):
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name == "AF_INET" and addr.address == ip:
                return True, iface
    return False, None


def is_ip_present_in_arp(ip: str):
    try:
        res = subprocess.run(
            ["ip", "neigh", "show", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1,
            shell=False,
        ).stdout.strip()
        if res and "FAILED" not in res:
            return True, res
    except Exception as e:
        _logger = logging.getLogger("LoggerService")
        _logger.debug(e)
    return False, None


def is_ip_reachable(ip: str):
    try:
        return (
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            ).returncode
            == 0
        )
    except Exception:
        return False


# Additional methods for subnet validation
def is_valid_subnet_binary(binary_mask: str) -> bool:
    """
    Check if binary representation is a valid subnet mask.
    Valid mask has all 1s followed by all 0s (no interleaving).

    :param: binary_mask: 32-bit binary string
    :return: bool: True if valid subnet mask pattern, False otherwise
    """

    # Find first occurrence of '0'
    first_zero = binary_mask.find("0")

    # If no zeros, mask is all 1s (valid - /32)
    if first_zero == -1:
        return True

    # If zeros exist, check that all remaining bits are 0s
    # Everything after first zero should be all zeros
    remaining = binary_mask[first_zero:]

    return remaining == "0" * len(remaining)


def get_subnet_prefix_length(subnet_mask: str) -> Optional[int]:
    """
    Get the CIDR prefix length from a subnet mask.

    :param: subnet_mask: Valid subnet mask string
    :return: int: Prefix length (0-32) or None if invalid
    """
    try:
        # Convert to binary and count 1s
        octets = subnet_mask.split(".")
        binary_mask = "".join(format(int(octet), "08b") for octet in octets)
        return binary_mask.count("1")
    except ValueError:
        return None


def subnet_mask_to_cidr(subnet_mask: str) -> Optional[str]:
    """
    Convert subnet mask to CIDR notation.

    :param: subnet_mask: Valid subnet mask string
    :return: str: CIDR notation (e.g., "/24") or None if invalid
    """
    prefix_length = get_subnet_prefix_length(subnet_mask)
    if prefix_length is None:
        return None
    return f"/{prefix_length}"


def cidr_to_subnet_mask(prefix_length: int) -> Optional[str]:
    """
    Convert CIDR prefix length to subnet mask.

    :param: prefix_length: CIDR prefix length (0-32)
    :return: str: Subnet mask in dotted decimal notation or None if invalid
    """
    if not isinstance(prefix_length, int) or prefix_length < 0 or prefix_length > 32:
        return None

    # Create binary mask with prefix_length 1s followed by 0s
    binary_mask = "1" * prefix_length + "0" * (32 - prefix_length)

    # Convert to dotted decimal
    octets = []
    for i in range(0, 32, 8):
        octet = binary_mask[i : i + 8]
        octets.append(str(int(octet, 2)))

    return ".".join(octets)


# Additional methods for IP address validations
def validate_ip_address_regex(ip_address: str) -> tuple[bool, str]:
    """
    Alternative implementation using regex pattern matching.

    :param: ip_address: String to validate as IPv4 address
    :return: Tuple[bool, str]: (is_valid, error_message)
    """
    # Check if input is a string
    if not isinstance(ip_address, str):
        return False, "IP address must be a string"

    # Check for empty string
    if not ip_address or ip_address.strip() == "":
        return False, "IP address cannot be empty"

    pattern = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$"
    )

    if pattern.match(ip_address):
        return True, ""
    else:
        return False, "Invalid IP address format"
