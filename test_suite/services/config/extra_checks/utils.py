from typing import Optional


# Additional methods for subnet validation
def is_valid_subnet_binary(binary_mask: str) -> bool:
    """
        Check if binary representation is a valid subnet mask.
        Valid mask has all 1s followed by all 0s (no interleaving).

        :param: binary_mask: 32-bit binary string
        :return: bool: True if valid subnet mask pattern, False otherwise
        """

    # Find first occurrence of '0'
    first_zero = binary_mask.find('0')

    # If no zeros, mask is all 1s (valid - /32)
    if first_zero == -1:
        return True

    # If zeros exist, check that all remaining bits are 0s
    # Everything after first zero should be all zeros
    remaining = binary_mask[first_zero:]

    return remaining == '0' * len(remaining)


def get_subnet_prefix_length(subnet_mask: str) -> Optional[int]:
    """
    Get the CIDR prefix length from a subnet mask.

    :param: subnet_mask: Valid subnet mask string
    :return: int: Prefix length (0-32) or None if invalid
    """
    try:
        # Convert to binary and count 1s
        octets = subnet_mask.split('.')
        binary_mask = ''.join(format(int(octet), '08b') for octet in octets)
        return binary_mask.count('1')
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
    binary_mask = '1' * prefix_length + '0' * (32 - prefix_length)

    # Convert to dotted decimal
    octets = []
    for i in range(0, 32, 8):
        octet = binary_mask[i:i + 8]
        octets.append(str(int(octet, 2)))

    return '.'.join(octets)


# Additional methods for IP address validations
def validate_ip_address_regex(ip_address: str) -> (bool, str):
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
        r'^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$'
    )

    if pattern.match(ip_address):
        return True, ""
    else:
        return False, "Invalid IP address format"



