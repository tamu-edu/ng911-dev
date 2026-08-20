from services.aux_services.json_services import (
    iso_to_timestamp,
    float_timestamp_to_iso,
    is_valid_iso_datetime,
)
from services.aux_services.aux_services import validate_ip_port_combo
from tests.ESRP_014.constants import TIMESTAMP_THRESHOLD


def validate_optional_string_field(field_value, field_name, **kwargs) -> str:
    """Validates optional log-event field: if present it must be a string."""
    if field_value is None:
        return "PASSED"
    if not isinstance(field_value, str):
        return f"FAILED -> '{field_name}' must be a string when present"
    return "PASSED"


def validate_timestamp(actual_timestamp, expected_timestamp, **kwargs) -> str:
    """Validates timestamp ISO format and within threshold of SIP INVITE time."""
    try:
        assert expected_timestamp, "NOT RUN -> SIP INVITE timestamp not found."
        assert actual_timestamp, "FAILED -> 'timestamp' not found in log event."
        assert is_valid_iso_datetime(
            actual_timestamp
        ), f"FAILED -> 'timestamp' has invalid ISO 8601 format: '{actual_timestamp}'"
        ts_float = iso_to_timestamp(actual_timestamp)
        assert ts_float is not None, "FAILED -> 'timestamp' could not be parsed."
        assert round(ts_float - expected_timestamp, 2) <= TIMESTAMP_THRESHOLD, (
            f"FAILED -> 'timestamp' difference exceeds {TIMESTAMP_THRESHOLD}s threshold.\n"
            f"SIP INVITE: {float_timestamp_to_iso(expected_timestamp)} | "
            f"Log event: {float_timestamp_to_iso(ts_float)}"
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_optional_log_event_fields(raw_event, optional_string_fields) -> str:
    """Validates optional log event string fields and ipAddressPort if present."""
    try:
        assert raw_event, "NOT RUN -> No log event data found."
        for field_name, field_type in optional_string_fields.items():
            field_value = raw_event.get(field_name)
            if field_value is not None:
                assert isinstance(field_value, field_type), (
                    f"FAILED -> '{field_name}' must be a string when present, "
                    f"got: {type(field_value).__name__}"
                )
        ip_port = raw_event.get("ipAddressPort")
        if ip_port is not None:
            assert isinstance(
                ip_port, str
            ), "FAILED -> 'ipAddressPort' must be a string when present."
            assert validate_ip_port_combo(ip_port), (
                f"FAILED -> 'ipAddressPort' must be in '###.###.###.###:port' format, "
                f"got: '{ip_port}'"
            )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_response_direction(direction, **kwargs) -> str:
    """Validates direction is 'incoming' or 'outgoing'."""
    try:
        assert direction, "FAILED -> 'direction' not found in 'LostResponseLogEvent'."
        assert direction in (
            "incoming",
            "outgoing",
        ), f"FAILED -> 'direction' must be 'incoming' or 'outgoing', got: '{direction}'"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_malformed_response(
    field_value, field_name, is_required=False, **kwargs
) -> str:
    """Validates malformedResponse: required in Variation 2, optional otherwise."""
    try:
        if is_required:
            assert (
                field_value is not None
            ), f"FAILED -> '{field_name}' is required in Variation 2 but not found."
            assert isinstance(field_value, str), (
                f"FAILED -> '{field_name}' must be a string, "
                f"got: {type(field_value).__name__}"
            )
        else:
            if field_value is not None:
                assert isinstance(
                    field_value, str
                ), f"FAILED -> '{field_name}' must be a string when present"
        return "PASSED"
    except AssertionError as e:
        return str(e)
