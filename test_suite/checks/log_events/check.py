import re

from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import (
    EMERGENCY_IDENTIFIER_URN_PATTERN,
    STRING_ID_PATTERN,
    FQDN_PATTERN,
    INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN,
)
from services.aux_services.aux_services import (
    validate_ip_port_combo,
    extract_header_value_by_separator,
)
from services.aux_services.json_services import is_valid_fqdn, is_timestamp

from typing import Any, Iterable


def optional_attributes_validation(
    payload_data: dict[str, Any],
    optional_fields: Iterable[str],
    event_type: str,
) -> str:
    """
    Validates optional attributes in an event payload.

    Performs checks on optional fields within the provided payload and
    validates their presence or correctness depending on expected rules.
    Before running the checks, validates that the input arguments
    themselves are of the expected types.

    Args:
        payload_data: Dict payload data to validate. Used both as
            the source of field values and for contextual assertion
            messages.
        optional_fields: Iterable of optional field names (strings) to
            check within `payload_data`.
        event_type: Event type used for contextual assertion messages.
            Must be a non-empty string.

    Returns:
        str: "PASSED" if validation succeeds, otherwise a string
            describing the first validation or input error encountered.
    """

    if not isinstance(payload_data, dict):
        return (
            f"FAILED -> 'payload_data' must be a dict, "
            f"got {type(payload_data).__name__}. Event: '{event_type}'"
        )

    if not isinstance(optional_fields, (list, tuple, set)):
        return (
            f"FAILED -> 'optional_fields' must be a list/tuple/set, "
            f"got {type(optional_fields).__name__}. Event: '{event_type}'"
        )

    if not all(isinstance(f, str) for f in optional_fields):
        return (
            f"FAILED -> all items in 'optional_fields' must be strings. "
            f"Event: '{event_type}'"
        )

    if not isinstance(event_type, str) or not event_type:
        return "FAILED -> 'event_type' must be a non-empty string."

    try:
        for optional_field_name in optional_fields:
            optional_field_value = payload_data.get(optional_field_name, None)
            if optional_field_value is not None:
                if optional_field_name == "ipAddressPort":
                    ip_address_value = optional_field_value

                    assert validate_ip_port_combo(ip_address_value) or is_valid_fqdn(
                        ip_address_value
                    ), f"FAILED -> Invalid IP:PORT or FQDN value for '{event_type}'. Received: '{ip_address_value}'"

                elif optional_field_name == "extension":
                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, dict
                        )
                    ) == "PASSED", f"FAILED -> {result} Event: '{event_type}', field name: '{optional_field_name}'"
                else:
                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, str
                        )
                    ) == "PASSED", f"FAILED -> {result} Event: '{event_type}', field name: '{optional_field_name}'"

        return "PASSED"

    except AssertionError as e:
        return str(e)


def assert_required_payload_fields(
    payload_data: dict[str, Any],
    fields: Iterable[str],
    event_type: str,
) -> str:
    """
    Validates that all required fields are present in an event payload.

    Checks that each field from `fields` exists as a key in
    `payload_data`. Before running the checks, validates that the input
    arguments themselves are of the expected types.

    Args:
        payload_data: Dict payload data to validate.
        fields: List/tuple/set of required field names (strings) that
            must be present in `payload_data`.
        event_type: Event type used for contextual error messages.
            Must be a non-empty string.

    Returns:
        str: "PASSED" if all required fields are present, otherwise a
            string describing the first missing field or input error
            encountered.
    """

    if not isinstance(payload_data, dict):
        return (
            f"FAILED -> 'payload_data' must be a dict, "
            f"got {type(payload_data).__name__}. Event: '{event_type}'"
        )

    if not isinstance(fields, (list, tuple, set)):
        return (
            f"FAILED -> 'fields' must be a list/tuple/set, "
            f"got {type(fields).__name__}. Event: '{event_type}'"
        )

    if not all(isinstance(f, str) for f in fields):
        return (
            f"FAILED -> all items in 'fields' must be strings. "
            f"Event: '{event_type}'"
        )

    if not isinstance(event_type, str) or not event_type:
        return "FAILED -> 'event_type' must be a non-empty string."

    for field in fields:
        if field not in payload_data:
            return (
                f"FAILED -> No '{field}' object found in '{event_type}' payload data."
            )

    return "PASSED"


def verify_timestamp_format(timestamp: Any, error: str | None = None) -> str:
    """
    Validates that a timestamp value is correctly formatted.

    Delegates the actual check to `is_timestamp`. If validation fails,
    returns either the provided custom error message or a default one.

    Args:
        timestamp: Timestamp value to validate.
        error: Optional custom error message to return if validation
            fails. If not provided, a default message is used.

    Returns:
        str: "PASSED" if the timestamp is valid, otherwise the error
            message (custom or default), formatted as "FAILED -> ...".
    """

    default_error = f"FAILED -> Invalid timestamp value. Received: '{timestamp}'"

    if is_timestamp(timestamp):
        return "PASSED"

    return error if error is not None else default_error


def verify_call_id_format(call_id: str, event_type: str) -> str:
    """
    Validates the format of an emergency call ID.

    Expected format example:
        urn:emergency:uid:callid:1234567890:bcf.ng911.example

    Checks that the call ID contains:
        - the "urn:emergency:uid:callid:" prefix (URN);
        - a String ID of 10 to 32 alphanumeric characters following
          that prefix;
        - a valid domain name (FQDN) following the String ID.

    Args:
        call_id: Call ID value to validate.
        event_type: Event type used for contextual error messages.

    Returns:
        str: "PASSED" if all format checks succeed, otherwise a summary
            of which part(s) are invalid, formatted as "FAILED -> ...".
    """

    if not isinstance(call_id, str):
        return (
            f"FAILED -> Emergency Call Identifier has invalid type for Event Type: '{event_type}'. "
            f"Expected str, got {type(call_id).__name__}. Actual: '{call_id}'"
        )

    if not call_id:
        return f"FAILED -> No Emergency Call Identifier found for Event Type: '{event_type}'"

    errors = []

    if not re.search(EMERGENCY_IDENTIFIER_URN_PATTERN, call_id):
        errors.append("URN prefix")

    string_id = extract_header_value_by_separator(call_id, ":", -2)
    if not re.search(STRING_ID_PATTERN, string_id):
        errors.append("String ID")

    fqdn = extract_header_value_by_separator(call_id, ":", -1)
    if not re.search(FQDN_PATTERN, fqdn):
        errors.append("FQDN")

    if errors:
        return (
            f"FAILED -> Emergency Call Identifier has invalid {', '.join(errors)} "
            f"for Event Type: '{event_type}'. Actual: '{call_id}'"
        )

    return "PASSED"


def verify_incident_id_format(incident_id: str, event_type: str) -> str:
    """
    Validates the format of an incident tracking ID.

    Expected format example:
        urn:emergency:uid:incidentid:123ABCdefg123ABCdefg123ABCdefg12:test.com

    Checks that the incident ID contains:
        - the "urn:emergency:uid:incidentid:" prefix (URN);
        - a String ID of 10 to 32 alphanumeric characters following
          that prefix;
        - a valid domain name (FQDN) following the String ID.

    Args:
        incident_id: Incident tracking ID value to validate
        event_type: Event type used for contextual error messages.

    Returns:
        str: "PASSED" if all format checks succeed, otherwise a summary
            of which part(s) are invalid, formatted as "FAILED -> ...".
    """

    if not isinstance(incident_id, str):
        return (
            f"FAILED -> Incident Tracking Identifier has invalid type for Event Type: '{event_type}'. "
            f"Expected str, got {type(incident_id).__name__}. Actual: '{incident_id}'"
        )

    if not incident_id:
        return f"FAILED -> No Incident Tracking Identifier found for Event Type: '{event_type}'"

    errors = []

    if not re.search(INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN, incident_id):
        errors.append("URN prefix")

    string_id = extract_header_value_by_separator(incident_id, ":", -2)
    if not re.search(STRING_ID_PATTERN, string_id):
        errors.append("String ID")

    fqdn = extract_header_value_by_separator(incident_id, ":", -1)
    if not re.search(FQDN_PATTERN, fqdn):
        errors.append("FQDN")

    if errors:
        return (
            f"FAILED -> Incident Tracking Identifier has invalid {', '.join(errors)} "
            f"for Event Type: '{event_type}'. Actual: '{incident_id}'"
        )

    return "PASSED"


def verify_call_id_sip(call_id: str, event_type: str) -> str:
    """
    Validates the format of a SIP Call-ID header value.

    Per RFC 3261, a Call-ID is expected to be globally unique and
    typically follows the format:
        <unique-id>@<host>

    Checks that the call ID:
        - is not empty;
        - matches the pattern "<unique-id>@<host>", where both parts
          consist of alphanumeric characters, dots, hyphens, and/or
          underscores.

    Args:
        call_id: SIP Call-ID value to validate.
        event_type: Event type used for contextual error messages.

    Returns:
        str: "PASSED" if the format check succeeds, otherwise a
            "FAILED -> ..." message including the actual value.
    """

    if not isinstance(call_id, str):
        return (
            f"FAILED -> SIP Call-ID has invalid type for Event Type: '{event_type}'. "
            f"Expected str, got {type(call_id).__name__}. Actual: '{call_id}'"
        )

    if not call_id:
        return f"FAILED -> No SIP Call-ID found for Event Type: '{event_type}'"

    normalized_call_id = call_id.strip()
    pattern = r"^[a-zA-Z0-9\.\-_]+@[a-zA-Z0-9\.\-]+$"

    if not re.match(pattern, normalized_call_id):
        return (
            f"FAILED -> SIP Call-ID wrong pattern for Event Type: '{event_type}'. "
            f"Actual: '{call_id}'"
        )

    return "PASSED"


def verify_query_id(query_id: str, event_type: str) -> str:
    """
    Validates the format of a Query ID.

    Expected format example:
        urn:emergency:uid:queryid:<...>

    Checks that the query ID matches the pattern
    "urn:emergency:uid:queryid:*".

    Args:
        query_id: Query ID value to validate.
        event_type: Event type used for contextual error messages.

    Returns:
        str: "PASSED" if the format check succeeds, otherwise the error
            message encountered, formatted as "FAILED -> ...".
    """
    try:
        assert query_id, f"FAILED -> No Query ID found for Event Type: '{event_type}'"

        assert re.match(
            r"^urn:emergency:uid:queryid:.+$", query_id
        ), f"FAILED -> Wrong 'queryId' format for Event Type: '{event_type}'. Received: '{query_id}'"

        return "PASSED"

    except AssertionError as e:
        return str(e)


def extract_enclosed_value(s: str) -> str:
    """
    Extracts the value enclosed between the first '<' and '>' characters.

    Args:
        s: Input string to extract the value from.

    Returns:
        str: The extracted substring between '<' and '>', or the
            original string if no such enclosure is found or if the
            input is not a string.
    """

    if not isinstance(s, str):
        return s

    return s.partition("<")[2].partition(">")[0] if "<" in s and ">" in s else s


def get_payload_field(payload: Any, field_name: str) -> Any:
    """
    Safely reads a field from the payload, whether it's a dict or an
    object with attribute access (e.g. EasyJSON).

    Returns:
        Any: The field value if present, otherwise None.
    """
    if not payload:
        return None
    if isinstance(payload, dict):
        return payload.get(field_name)
    return getattr(payload, field_name, None)


def is_valid_ip_or_fqdn(value: str) -> bool:
    """
    Validates whether a string is a valid 'IP:PORT' combo or a valid FQDN.

    :param value: String to validate (e.g. '192.168.64.15:5060' or 'lvf.911.gov').
    :return: True if the value is a valid IP:PORT combo or a valid FQDN, else False.
    """
    return validate_ip_port_combo(value) or is_valid_fqdn(value)
