from services.aux_services.aux_services import validate_ip_port_combo
from services.aux_services.json_services import (
    decode_jws,
    is_valid_iso_datetime,
    iso_to_timestamp,
    float_timestamp_to_iso,
)
from services.aux_services.message_services import extract_json_data_from_http


def get_jws_payloads_list_by_log_event_type(
    http_post_messages: list,
    log_event_type: str,
    key_filepath: str,
    call_id=None,
) -> list:
    """Find the first HTTP POST message matching a specific JWS log event type.

    Args:
        http_post_messages: List of PyShark HTTP POST packets.
        log_event_type: The logEventType value to search for (e.g. 'LostResponseLogEvent').
        key_filepath: Path to the key file for JWS decoding.
        call_id: The callId value to search for.

    Returns:
        Tuple of (jws dict, packet) if found, otherwise (None, None).
        JWS dict may represent either a signed or unsigned payload.
    """
    result_list = []
    if http_post_messages:
        for message in http_post_messages:
            # TODO what to do with signed without a key
            if hasattr(message, "http") and hasattr(message.http, "file_data"):
                json_data_from_message = extract_json_data_from_http(message)
                try:
                    _, payload_data = decode_jws(json_data_from_message, key_filepath)
                except ValueError:
                    _, payload_data = None, None
                if payload_data:
                    l_event_type = payload_data.get("logEventType", None)
                    call_id_sip = payload_data.get("callIdSip", None)
                    if l_event_type == log_event_type:
                        if call_id:
                            if call_id_sip == call_id:
                                result_list.append(payload_data)
                        else:
                            result_list.append(payload_data)
    return result_list


def validate_log_event_timestamp(
    actual_timestamp, expected_timestamp, timestamp_threshold=None
) -> str:
    """Validates timestamp ISO format and within threshold of SIP INVITE time."""
    try:
        assert expected_timestamp, "NOT RUN -> SIP INVITE timestamp not found."
        assert actual_timestamp, "FAILED -> 'timestamp' not found in log event."
        assert is_valid_iso_datetime(
            actual_timestamp
        ), f"FAILED -> 'timestamp' has invalid ISO 8601 format: '{actual_timestamp}'"
        ts_float = iso_to_timestamp(actual_timestamp)
        assert ts_float is not None, "FAILED -> 'timestamp' could not be parsed."
        if timestamp_threshold:
            assert round(ts_float - expected_timestamp, 2) <= timestamp_threshold, (
                f"FAILED -> 'timestamp' difference exceeds {timestamp_threshold} threshold.\n"
                f"SIP INVITE: {float_timestamp_to_iso(expected_timestamp)} | "
                f"Log event: {float_timestamp_to_iso(ts_float)}"
            )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_optional_log_event_fields(log_event_class) -> str:
    """Validates optional log event string fields and ipAddressPort if present."""
    try:
        assert log_event_class, "NOT RUN -> No log event data found."
        optional_fields = log_event_class.optional_fields()
        for field_name, field_type in optional_fields.items():
            field_value = getattr(log_event_class, field_name, None)
            if field_value is not None:
                assert isinstance(field_value, field_type), (
                    f"FAILED -> '{field_name}' must be a {field_type} when present, "
                    f"got: {type(field_value).__name__}"
                )
        ip_port = log_event_class.ipAddressPort
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
