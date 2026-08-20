import re

TYPE_NAMES = {
    "str": "a string",
    "int": "an integer",
    "list": "a list",
    "dict": "a dictionary",
}


def validate_response_code(expected_response_code, response_code):
    """
    Validation of expected response code.
    """
    try:
        assert expected_response_code, "NOT RUN -> No expected response code found."
        assert response_code, "FAILED -> No response code found."
        assert (
            response_code == expected_response_code
        ), f"FAILED-> Response code is not {expected_response_code}. Actual response code - {response_code}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_response_code_class(expected_response_code_class, response_code):
    """
    Validation of response code class, example 1XX, 2XX, 3XX, 4XXX, 5XX.
    """
    pattern_template = r"^{prefix}\d{{2}}$"

    try:
        assert (
            expected_response_code_class
        ), "NOT RUN -> No expected response code class found."
        assert response_code, "FAILED -> No response code found."
        assert (
            expected_response_code_class
        ), "FAILED-> Response code class cannot be None"
        assert response_code, "FAILED-> Response code cannot be None"
        code_class_first_digit = str(expected_response_code_class)[0]
        assert bool(
            re.match(
                pattern_template.format(prefix=code_class_first_digit), response_code
            )
        ), f"FAILED-> Response code class is not {code_class_first_digit}XX. Actual response code - {response_code}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def is_valid_url(url: str, check_ip_as_host: bool = False) -> bool:
    """Validates that a string is a well-formed HTTP/HTTPS URL.

    Args:
        url (str): The URL string to validate.
        check_ip_as_host (bool, optional): Whether or not to check the IP address as a host. Defaults to False.)

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        if not parsed.path:
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Reject trailing dot in hostname
        if hostname.endswith("."):
            return False

        ip_pattern = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
        is_ip = bool(ip_pattern.match(hostname))

        if is_ip:
            if not check_ip_as_host:
                return False

            octets = hostname.split(".")
            if not all(0 <= int(o) <= 255 for o in octets):
                return False
            return True

        # Validate each label in the hostname
        label_pattern = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$")
        for label in hostname.split("."):
            if not label_pattern.match(label):
                return False

        return True

    except Exception:
        return False


def is_type(param, param_name, expected_type) -> str:
    if not param:
        return "FAILED-> No input data found for type verification."
    if isinstance(expected_type, tuple):
        type_name = "an array"
    else:
        type_name = TYPE_NAMES[expected_type.__name__]
    return (
        "PASSED"
        if isinstance(param, expected_type)
        else f"FAILED-> '{param_name}' is not {type_name} type."
    )
