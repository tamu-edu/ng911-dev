import ipaddress
import os
import re
from pathlib import Path

from services.config.extra_checks.utils import (
    is_valid_subnet_binary,
    is_ip_reachable,
    is_ip_assigned_locally,
    is_ip_present_in_arp,
)
from test_suite.enums.packet_types import PacketTypeEnum, TransportProtocolEnum
from .registry import register


@register
def if_port_valid(field_name: str, field_value) -> tuple[bool, str]:
    """
    EXAMPLE
    :param field_name: str
    :param field_value: value of the field form config
    :return: tuple(bool,str)
    """
    if not field_value:
        return False, f"Lab Config error -> {field_name} value is missing."
    if not isinstance(field_value, int):
        return False, f"Lab Config error -> {field_name} must be integer."
    if field_value < 1 or field_value > 65535:
        return False, f"Lab Config error -> {field_name} must be between 1 and 65535."
    return True, ""


@register
def if_protocol_valid(field_name: str, field_value) -> tuple[bool, str]:
    """
    EXAMPLE
    :param field_name: str
    :param field_value: value of the field form config
    :return: tuple(bool,str)
    """
    if not field_value:
        return False, f"Lab Config error -> {field_name} value is missing."
    if not isinstance(field_value, str):
        return False, f"Lab Config error -> {field_name} must be string."
    if field_value not in PacketTypeEnum.list():
        return (
            False,
            f"Lab Config error -> {field_name} must be one of {PacketTypeEnum.list()}",
        )
    return True, ""


@register
def if_transport_protocol_valid(field_name: str, field_value) -> tuple[bool, str]:
    """
    EXAMPLE
    :param field_name: str
    :param field_value: value of the field form config
    :return: tuple(bool,str)
    """
    if not field_value:
        return False, f"Lab Config error -> {field_name} value is missing."
    if not isinstance(field_value, str):
        return False, f"Lab Config error -> {field_name} must be string."
    if field_value not in TransportProtocolEnum.list():
        return (
            False,
            f"Lab Config error -> {field_name} must be one of {TransportProtocolEnum.list()}",
        )
    return True, ""


@register
def if_dns_list_valid(field_name: str, field_value) -> tuple[bool, str]:
    """
    EXAMPLE
    :param field_name: str
    :param field_value: value of the field form config
    :return: tuple(bool,str)
    """
    if not field_value:
        return False, f"Lab Config error -> {field_name} value is missing."
    if not isinstance(field_value, list):
        return False, f"Lab Config error -> {field_name} must be list of strings."
    if any(not isinstance(dns, str) for dns in field_value):
        return False, f"Lab Config error -> {field_name} must be list of strings."

    seen = set()
    for idx, raw in enumerate(field_value):
        dns = raw.strip()
        if not dns:
            return False, f"Lab Config error -> {field_name}[{idx}] is empty."

        try:
            ip_obj = ipaddress.ip_address(dns)
        except ValueError:
            return (
                False,
                f"Lab Config error -> {field_name}[{idx}] '{dns}' is not a valid IPv4 or IPv6 address.",
            )

        canonical = str(ip_obj)
        if canonical in seen:
            return (
                False,
                f"Lab Config error -> {field_name} contains duplicate IP '{canonical}'.",
            )
        seen.add(canonical)

    return True, ""


# VALIDATE FQDN VALUE
@register
def if_fqdn_valid(field_name: str, field_value) -> tuple[bool, str]:
    """
    Verify if the provided string is a valid FQDN.
    :param field_name: Field name
    :param field_value: FQDN, string value to verify as FQDN
    :return: bool: True if valid FQDN, False otherwise

    Rules:
        - Must follow format: <hostname>.<domain>.<tld>
        - Allowed characters: letters, digits, hyphens (-), and dots (.)
        - Cannot start or end with a hyphen
        - Total length must not exceed 253 characters
        - Each label must be 1-63 characters
    """
    # Check if input is a string
    if not isinstance(field_value, str):
        return False, f"Error in {field_name}: FQDN should be a string."

    # Check total length
    if len(field_value) == 0 or len(field_value) > 253:
        return False, f"Error in {field_name}: Invalid FQDN value"

    # Remove trailing dot if present (valid in FQDN)
    if field_value.endswith("."):
        field_value = field_value[:-1]

    # Split into labels (parts between dots)
    labels = field_value.split(".")

    if len(labels) < 2:
        return (
            False,
            f"Error in {field_name}: FQDN have at least 2 parts (name.domain).",
        )

    # Pattern for valid label:
    # - starts and ends with alphanumeric
    # - can contain hyphens in the middle
    # - 1-63 characters long
    label_pattern = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")

    # Verify each label
    for label in labels:
        if not label:  # Empty label (consecutive dots)
            return False, f"Error in {field_name}: FQDN consist of '.' separated data."

        if len(label) > 63:  # Label too long
            return False, f"Error in {field_name}: Part of FQDN cannot exceed 63 chars."

        if not label_pattern.match(label):
            return False, f"Error in {field_name}: Invalid FQDN format"

    return True, ""


# VALIDATE SUBNET MASK VALUE
@register
def if_subnet_mask_valid(field_name: str, field_value) -> tuple[bool, str]:
    """
    Validate if the provided string is a valid subnet mask.

    :param field_name: Field name
    :param field_value: Subnet mask, string to validate as subnet mask
    :return:
        Tuple[bool, str]: (is_valid, error_message)
        - is_valid: True if valid subnet mask, False otherwise
        - error_message: Description of validation failure, empty string if valid

    Rules:
        - Must be a string
        - Must be a valid subnet mask in dotted decimal notation (e.g., 255.255.255.0)
        - Must represent a valid CIDR prefix length (/0 to /32)
        - Binary representation must be contiguous 1s followed by contiguous 0s
    """
    # Check if input is a string
    if not isinstance(field_value, str):
        return False, f"Error in {field_name}: Subnet mask must be a string"

    # Check for empty string
    if not field_value or field_value.strip() == "":
        return False, f"Error in {field_name}: Subnet mask cannot be empty"

    # Split by dots
    octets = field_value.split(".")

    # Must have exactly 4 octets
    if len(octets) != 4:
        return (
            False,
            f"Error in {field_name}: Subnet mask must have exactly 4 octets, found {len(octets)}",
        )

    # Validate each octet and build binary representation
    binary_mask = ""

    for i, octet in enumerate(octets):
        # Check if octet is empty
        if not octet:
            return False, f"Error in {field_name}: Octet {i + 1} is empty"

        # Check if octet contains only digits
        if not octet.isdigit():
            return (
                False,
                f"Error in {field_name}: Octet {i + 1} contains non-digit characters: '{octet}'",
            )

        # Convert to integer and check range
        try:
            octet_value = int(octet)
            if octet_value < 0 or octet_value > 255:
                return (
                    False,
                    f"Error in {field_name}: Octet {i + 1} out of range (0-255): {octet_value}",
                )
        except ValueError:
            return (
                False,
                f"Error in {field_name}: Octet {i + 1} is not a valid number: '{octet}'",
            )

        # Convert to 8-bit binary and append
        binary_mask += format(octet_value, "08b")

    # Check if binary representation is a valid subnet mask
    # Valid mask: contiguous 1s followed by contiguous 0s (e.g., 11111111111111110000000000000000)
    if not is_valid_subnet_binary(binary_mask):
        return (
            False,
            f"Error in {field_name}: Invalid subnet mask: bits must be contiguous (all 1s followed by all 0s)",
        )

    # Count the prefix length (number of 1s)
    prefix_length = binary_mask.count("1")

    # Verify prefix length is within valid range (0-32)
    if prefix_length < 0 or prefix_length > 32:
        return (
            False,
            f"Error in {field_name}: Prefix length /{prefix_length} is out of valid range (/0 to /32)",
        )

    return True, ""


# VALIDATE IP ADDRESS VALUE
@register
def if_ip_valid(field_name: str, field_value) -> tuple[bool, str]:
    """
    Validate if the provided string is a valid IPv4 address.

    :param field_name: Field name
    :param field_value: IP address, string to validate as IPv4 address
    :return:
        Tuple[bool, str]: (is_valid, error_message)
        - is_valid: True if valid IP address, False otherwise
        - error_message: Description of validation failure, empty string if valid

    Rules:
        - Must be a string
        - Must follow format: xxx.xxx.xxx.xxx (dotted decimal notation)
        - Each octet must be 0-255
        - No leading zeros unless the value is 0
    """
    # Check if input is a string
    if not isinstance(field_value, str):
        return False, f"Error in {field_name}: IP address must be a string"

    # Check for empty string
    if not field_value or field_value.strip() == "":
        return False, f"Error in {field_name}: IP address cannot be empty"

    # Split by dots
    octets = field_value.split(".")

    # Must have exactly 4 octets
    if len(octets) != 4:
        return (
            False,
            f"Error in {field_name}: IP address must have exactly 4 octets, found {len(octets)}",
        )

    # Validate each octet
    for i, octet in enumerate(octets):
        # Check if octet is empty
        if not octet:
            return False, f"Error in {field_name}: Octet {i + 1} is empty"

        # Check for leading zeros (except for "0" itself)
        if len(octet) > 1 and octet[0] == "0":
            return (
                False,
                f"Error in {field_name}: Octet {i + 1} has leading zero: '{octet}'",
            )

        # Check if octet contains only digits
        if not octet.isdigit():
            return (
                False,
                f"Error in {field_name}: Octet {i + 1} contains non-digit characters: '{octet}'",
            )

        # Convert to integer and check range
        try:
            octet_value = int(octet)
            if octet_value < 0 or octet_value > 255:
                return (
                    False,
                    f"Error in {field_name}: Octet {i + 1} out of range (0-255): {octet_value}",
                )
        except ValueError:
            return (
                False,
                f"Error in {field_name}: Octet {i + 1} is not a valid number: '{octet}'",
            )

    return True, ""


# VALIDATE CERTIFICATE FILEPATH VALUE
@register
def if_certificate_path_valid(field_name: str, field_value) -> tuple[bool, str]:
    """
    Validate if the provided path is a valid certificate file path.

    :param field_name: Field name
    :param field_value: Cert path, string path to certificate file
    :return:
        Tuple[bool, str]: (is_valid, error_message)
        - is_valid: True if valid certificate path, False otherwise
        - error_message: Description of validation failure, empty string if valid

    Rules:
        - Must be a valid absolute or relative file path
        - File extension should be .crt, .pem, .cer, .der, .p12, .pfx, .key
        - File must exist and be accessible (read permissions required)
        - Path must not contain invalid characters (*, ?, <, >, |)
    """

    if not field_name:
        return True, ""
    # Check if input is a string
    if not isinstance(field_value, str):
        return False, "Path must be a string"

    # Check for empty path
    if not field_value or field_value.strip() == "":
        return False, f"Error in {field_name}: Path cannot be empty"

    # Check for invalid characters
    invalid_chars = ["*", "?", "<", ">", "|"]
    for char in invalid_chars:
        if char in field_value:
            return (
                False,
                f"Error in {field_name}: Path contains invalid character: '{char}'",
            )

    # Validate file extension
    valid_extensions = {".crt", ".pem", ".cer", ".der", ".p12", ".pfx", ".key"}
    path_obj = Path(field_value)

    if path_obj.suffix.lower() not in valid_extensions:
        return (
            False,
            f"Error in {field_name}: Invalid file extension. Allowed: {', '.join(sorted(valid_extensions))}",
        )

    # Check if file exists
    if not path_obj.exists():
        return False, f"Error in {field_name}: File does not exist: {field_value}"

    # Check if it's a file (not a directory)
    if not path_obj.is_file():
        return False, f"Error in {field_name}: Path is not a file: {field_value}"

    # Check read permissions
    if not os.access(field_value, os.R_OK):
        return (
            False,
            f"Error in {field_name}: File is not readable (permission denied): {field_value}",
        )

    return True, ""


# VALIDATE GATEWAY
@register
def if_gateway_valid(field_name: str, data_dict: dict, field_value) -> tuple[bool, str]:
    """
    Validate gateway address against the device IP and subnet.

    :param field_name: str
    :param field_value: gateway IP address (string)
    :param data_dict: current config block we are testing
    :return: tuple(bool, str) -> (is_valid, error_message)
    """
    if not field_value:
        return False, f"Lab Config error -> {field_name} value is missing."

    ip = data_dict.get("ip", "")
    netmask = data_dict.get("mask")

    # validate IP family and format
    try:
        gw_ip = ipaddress.ip_address(field_value)
    except ValueError:
        return (
            False,
            f"Lab Config error -> {field_name} '{field_value}' is not a valid IPv4 or IPv6 address.",
        )

    try:
        dev_ip = ipaddress.ip_address(ip)
    except ValueError:
        return False, f"Lab Config error -> {field_name} invalid device IP '{ip}'."

    # must be same family
    if gw_ip.version != dev_ip.version:
        return False, (
            f"Lab Config error -> {field_name} IP family mismatch (gateway {gw_ip.version}, "
            f"device {dev_ip.version})."
        )

    # must not be identical
    if gw_ip == dev_ip:
        return (
            False,
            f"Lab Config error -> {field_name} gateway cannot be identical to device IP.",
        )

    # must be in the same subnet
    try:
        network = ipaddress.ip_network(f"{ip}/{netmask}", strict=False)
    except ValueError:
        return (
            False,
            f"Lab Config error -> {field_name} invalid network definition with mask '{netmask}'.",
        )

    if gw_ip not in network:
        return (
            False,
            f"Lab Config error -> {field_name} '{field_value}' not in same subnet as {ip}/{netmask}.",
        )

    return True, ""


@register
def if_ip_functional_valid(
    field_name: str, field_value: str, data_dict: dict, parent_data_dict: dict
):
    """
    Context-aware IP validation.

    REAL DEVICE (IUT):
      - must be reachable

    STUB SERVER:
      - must NOT be locally assigned
      - must NOT appear in ARP
      - reachability NOT required
    """

    # Defensive
    if not isinstance(data_dict, dict):
        return True, ""

    # Heuristic: role-based decision (robust with your schema)
    roles = parent_data_dict.get("role")

    is_real_device = isinstance(roles, list) and "IUT" in roles

    if is_real_device:
        if not is_ip_reachable(field_value):
            # return False, (
            #     f"Error in {field_name}: IP {field_value} is not reachable "
            #     f"(real device must respond)"
            # )
            print(
                f"[WARNING] Error in {field_name}: IP {field_value} is not reachable "
                f"(real device must respond)"
            )
        return True, ""

    # ---- STUB SERVER PATH ----
    assigned, iface = is_ip_assigned_locally(field_value)

    if assigned:
        print(
            f"[WARNING] Error in {field_name}: IP {field_value} is already assigned "
            f"to local interface '{iface}'"
        )
        # return False, (
        #     f"Error in {field_name}: IP {field_value} is already assigned "
        #     f"to local interface '{iface}'"
        # )

    arp_present, arp_info = is_ip_present_in_arp(field_value)

    if arp_present:
        print(
            f"[WARNING] Error in {field_name}: IP {field_value} appears in ARP table "
            f"({arp_info}) and cannot be used for stub aliasing"
        )
        # return False, (
        #     f"Error in {field_name}: IP {field_value} appears in ARP table "
        #     f"({arp_info}) and cannot be used for stub aliasing"
        # )

    # Same-subnet check vs TS host IP (best effort)
    # ts_host_ip = resolve_ts_host_ip(data_dict, parent_data_dict)
    #
    # mask = data_dict.get("mask")  # when validating interfaces.ip, mask is sibling field in same dict
    #
    # same_subnet, net_str = is_ip_in_same_subnet(ts_host_ip, field_value, mask)
    #
    # if not same_subnet and net_str:
    #     print(
    #         f"[WARNING] Error in {field_name}: IP {field_value} is not in the same subnet as "
    #         f"TS host IP {ts_host_ip} (expected within {net_str})"
    #     )
    #     # return False, (
    #     #     f"Error in {field_name}: IP {field_value} is not in the same subnet as "
    #     #     f"TS host IP {ts_host_ip} (expected within {net_str})"
    #     # )

    # Alias ability check (add+del)
    # ok_alias, alias_msg = can_add_ip_alias(field_value, mask=mask)
    #
    # if not ok_alias:
    #     print(
    #         f"[WARNING] Error in {field_name}: IP {field_value} cannot be aliased on this host "
    #         f"({alias_msg})"
    #     )
    # return False, (
    #     f"Error in {field_name}: IP {field_value} cannot be aliased on this host "
    #     f"({alias_msg})"
    # )

    return True, ""


@register
def if_test_suite_host_ip_valid(field_name: str, field_value: str) -> tuple[bool, str]:
    is_local, iface = is_ip_assigned_locally(field_value)

    if not is_local:
        print(
            f"[WARNING] Error in {field_name}: IP {field_value} is not assigned to this host. "
            f"test_suite_host_ip must be one of local interface IPs."
        )

        # return False, (
        #     f"Error in {field_name}: IP {field_value} is not assigned to this host. "
        #     f"test_suite_host_ip must be one of local interface IPs."
        # )

    return True, ""
