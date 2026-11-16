import re

_SERVICE_URN_PARAM_PATTERN = re.compile(r";\s*serviceurn\s*=", re.IGNORECASE)
_QUOTED_SERVICE_URN_PATTERN = re.compile(r';\s*serviceurn\s*=\s*"[^"]*"', re.IGNORECASE)


_NO_REFER_ERROR = "FAILED -> SIP REFER message from CHFE to ESRP not found"


def _header_params_part(refer_to_raw: str | None) -> str:
    """Returns the header parameters part of a Refer-To value (after the URI)."""
    refer_to_raw = refer_to_raw or ""
    if ">" in refer_to_raw:
        return refer_to_raw.split(">", 1)[1]
    return ";" + refer_to_raw.partition(";")[2]


def validate_single_refer_to(refer_message, refer_to_count: int) -> str:
    """
    Validates that exactly one Refer-To header field is present.
    """

    if refer_message is None:
        return _NO_REFER_ERROR

    if refer_to_count != 1:
        return (
            "FAILED -> Exactly one Refer-To header field expected, "
            f"found: {refer_to_count}"
        )

    return "PASSED"


def validate_refer_to_sip_uri(refer_message, refer_to_uri: str | None) -> str:
    """
    Validates that the Refer-To URI scheme is 'sip' (case-insensitive).
    """

    if refer_message is None:
        return _NO_REFER_ERROR

    scheme = (refer_to_uri or "").strip().partition(":")[0].lower()

    if scheme != "sip":
        return (
            "FAILED -> Refer-To URI must be a SIP URI (scheme 'sip'), "
            f"found: '{refer_to_uri}'"
        )

    return "PASSED"


def validate_single_service_urn(refer_message, refer_to_raw: str | None) -> str:
    """
    Validates that the Refer-To header field contains exactly one
    'serviceurn' header parameter.
    """

    if refer_message is None:
        return _NO_REFER_ERROR

    count = len(_SERVICE_URN_PARAM_PATTERN.findall(_header_params_part(refer_to_raw)))

    if count != 1:
        return (
            "FAILED -> Exactly one serviceurn parameter expected in Refer-To, "
            f"found: {count}"
        )

    return "PASSED"


def validate_service_urn_quoted(refer_message, refer_to_raw: str | None) -> str:
    """
    Validates that the 'serviceurn' parameter value is a quoted string.
    """

    if refer_message is None:
        return _NO_REFER_ERROR

    if not _QUOTED_SERVICE_URN_PATTERN.search(_header_params_part(refer_to_raw)):
        return "FAILED -> Refer-To serviceurn parameter value is not a quoted string"

    return "PASSED"


def validate_service_urn_prefix(
    refer_message,
    service_urn: str | None,
    allowed_urns: frozenset[str],
) -> str:
    """
    Validates that the Refer-To serviceurn parameter is exactly one of
    the allowed service URNs.
    """

    if refer_message is None:
        return _NO_REFER_ERROR

    if not service_urn:
        return "FAILED -> Refer-To serviceurn parameter is not present"

    value = service_urn.strip().strip('"')

    if value.lower() not in allowed_urns:
        return (
            "FAILED -> Refer-To serviceurn parameter has invalid value: "
            f"'{service_urn}'"
        )

    return "PASSED"
