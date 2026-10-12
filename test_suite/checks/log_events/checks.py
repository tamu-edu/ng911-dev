import re

from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import (
    EMERGENCY_IDENTIFIER_URN_PATTERN,
    STRING_ID_PATTERN,
    FQDN_PATTERN,
    INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN,
    SUBSCRIPTION_IDENTIFIER_URN_PATTERN,
)
from services.aux_services.aux_services import (
    validate_ip_port_combo,
    extract_header_value_by_separator,
)
from services.aux_services.json_services import (
    is_valid_fqdn,
    is_timestamp,
    is_valid_iso_datetime,
    iso_to_timestamp,
    float_timestamp_to_iso,
    decode_jws,
)

from typing import Any, Iterable

from services.aux_services.message_services import extract_json_data_from_http
from services.aux_services.sdp_services import media_quality_stats_to_dict
from services.aux_services.sip_msg_body_services import is_valid_dialog_id


def validate_log_event_timestamp(
    actual_timestamp: str,
    expected_timestamp: float | None,
    timestamp_threshold: float | None = None,
) -> str:
    """
    Validates that a LogEvent's 'timestamp' field is a valid ISO 8601
    datetime, and optionally that it falls within a given threshold of
    a reference SIP message time (e.g. the INVITE or BYE that triggered
    the event).

    :param actual_timestamp: The 'timestamp' value from the LogEvent
        payload, as an ISO 8601 datetime string
        (e.g. "2026-09-03T12:55:38.97+03:00").
    :param expected_timestamp: The reference SIP message time to compare
        against, as a Unix timestamp (float, e.g. from
        packet.sniff_timestamp converted via float()). If falsy
        (None/0), the check is treated as not runnable (the reference
        SIP message was never found).
    :param timestamp_threshold: Maximum allowed difference, in seconds,
        between actual_timestamp and expected_timestamp. If not
        provided, only the ISO 8601 format is validated - no threshold
        comparison is performed.
    :return: "PASSED" if validation succeeds, otherwise the error
        message encountered, formatted as "FAILED -> ..." or, if the
        reference timestamp is missing, "NOT RUN -> ...".
    """
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


def validate_timestamps(subscribe_log_events, stimulus_timestamps, threshold=3) -> str:
    """
    Validates timestamps across a sequence of SubscribeLogEvent records.

    Checks that the number of log events matches the number of expected
    timestamps, then validates each log event's timestamp against its
    corresponding expected timestamp using `validate_log_event_timestamp`.

    Args:
        subscribe_log_events: Sequence of SubscribeLogEvent records to
            validate.
        stimulus_timestamps: Sequence of expected timestamps (e.g. SIP
            INVITE timestamps), one per log event, in matching order.
        threshold: Maximum allowed difference (in seconds) between an
            actual and expected timestamp. Defaults to 3.

    Returns:
        str: "PASSED" if all timestamps validate successfully, otherwise
            a string describing the first validation error encountered.
    """
    try:
        assert subscribe_log_events, "NOT RUN -> No SubscribeLogEvent records found."
        assert len(subscribe_log_events) == len(stimulus_timestamps), (
            "FAILED -> Number of SubscribeLogEvent records doesn't match number "
            "of SIP SUBSCRIBE transactions."
        )
        for idx, (log_event, expected_ts) in enumerate(
            zip(subscribe_log_events, stimulus_timestamps)
        ):
            result = validate_log_event_timestamp(
                log_event.timestamp, expected_ts, threshold
            )
            assert result == "PASSED", f"FAILED -> 'timestamp' at index {idx}: {result}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


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
    if not string_id or not re.search(STRING_ID_PATTERN, string_id):
        errors.append("String ID")

    fqdn = extract_header_value_by_separator(call_id, ":", -1)
    if not fqdn or not re.search(FQDN_PATTERN, fqdn):
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
    if not string_id or not re.search(STRING_ID_PATTERN, string_id):
        errors.append("String ID")

    fqdn = extract_header_value_by_separator(incident_id, ":", -1)
    if not fqdn or not re.search(FQDN_PATTERN, fqdn):
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

    Checks that the query ID is present, is a string, and matches the
    pattern "urn:emergency:uid:queryid:*".

    Args:
        query_id: Query ID value to validate.
        event_type: Event type used for contextual error messages.

    Returns:
        str: "PASSED" if the format check succeeds, otherwise the error
            message encountered, formatted as "FAILED -> ...".
    """
    try:
        assert query_id, f"FAILED -> No Query ID found for Event Type: '{event_type}'"

        assert isinstance(query_id, str), (
            f"FAILED -> Query ID has invalid type for Event Type: '{event_type}'. "
            f"Expected str, got {type(query_id).__name__}. Actual: '{query_id}'"
        )

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


def verify_media_quality_stats(media_stats: str, log_event_type: str) -> str:
    """
    Validates media quality statistics parsed from a raw string.

    Converts the raw media quality stats string into a dict via
    media_quality_stats_to_dict(), then ensures that required sections
    and expected keys/values are present and contain expected data or
    data type.

    Args:
        media_stats (str): Raw media quality statistics string.
        log_event_type (str): Event type used for contextual error messages.

    Returns:
        str: "PASSED" if validation succeeds, otherwise an error message
        describing the validation failure.
    """

    required_fields = (
        "VQSessionReport",
        "SessionDesc",
        "LocalMetrics",
        "RemoteMetrics",
        "DialogID",
    )

    metric_keys = ("Jitter", "PacketLoss", "Delay", "MOSLQ")

    if not isinstance(media_stats, str) or not media_stats.strip():
        return (
            f"FAILED -> 'mediaQualityStats' must be a non-empty string for "
            f"Event Type: '{log_event_type}'. Actual: {type(media_stats).__name__}: {media_stats!r}"
        )

    try:
        media_stats_dict = media_quality_stats_to_dict(media_stats)
    except Exception as e:
        return (
            f"FAILED -> Could not parse 'mediaQualityStats' string for "
            f"Event Type: '{log_event_type}': {e!r}"
        )

    if not isinstance(media_stats_dict, dict):
        return (
            f"FAILED -> 'mediaQualityStats' did not parse into a dict for "
            f"Event Type: '{log_event_type}'. Actual: {type(media_stats_dict).__name__}"
        )

    missing_fields = [
        field for field in required_fields if field not in media_stats_dict
    ]

    if missing_fields:
        return (
            f"FAILED -> Missing required mediaQualityStats sections: {missing_fields}"
        )

    vq_session_report_value = media_stats_dict.get("VQSessionReport")

    session_desc_raw = media_stats_dict.get("SessionDesc")
    session_desc_value: dict = (
        session_desc_raw if isinstance(session_desc_raw, dict) else {}
    )

    local_metrics_raw = media_stats_dict.get("LocalMetrics")
    local_metrics_value: dict = (
        local_metrics_raw if isinstance(local_metrics_raw, dict) else {}
    )

    remote_metrics_raw = media_stats_dict.get("RemoteMetrics")
    remote_metrics_value: dict = (
        remote_metrics_raw if isinstance(remote_metrics_raw, dict) else {}
    )

    dialog_id_value = media_stats_dict.get("DialogID")

    try:
        # Check VQSessionReport
        assert (
            vq_session_report_value == "CallTerm"
        ), f"FAILED -> Wrong VQSessionReport value: Actual '{vq_session_report_value}' Expected 'CallTerm'"

        # Check SessionDesc
        assert (
            session_desc_value.values()
        ), f"FAILED -> No 'SessionDesc' values found. Actual: '{session_desc_value}'"

        # Check LocalMetrics
        assert all(
            k in local_metrics_value for k in metric_keys
        ), f"FAILED -> Missing LocalMetrics objects: {[k for k in metric_keys if k not in local_metrics_value]}"

        assert all(
            isinstance(local_metrics_value[k], (int, float)) for k in metric_keys
        ), f"FAILED -> Invalid LocalMetrics values: { {k: local_metrics_value.get(k) for k in metric_keys if not isinstance(local_metrics_value.get(k), (int, float))} }. Expected int or float value."

        # Check RemoteMetrics
        assert all(
            k in remote_metrics_value for k in metric_keys
        ), f"FAILED -> Missing RemoteMetrics objects: {[k for k in metric_keys if k not in remote_metrics_value]}"

        assert all(
            isinstance(remote_metrics_value[k], (int, float)) for k in metric_keys
        ), f"FAILED -> Invalid RemoteMetrics values: { {k: remote_metrics_value.get(k) for k in metric_keys if not isinstance(remote_metrics_value.get(k), (int, float))} }. Expected int or float value."

        # Check DialogID
        assert is_valid_dialog_id(
            dialog_id_value
        ), f"FAILED -> Invalid 'DialogID' value format. Actual: '{dialog_id_value}' Expected format: '1234567890@caller.example.com;to-tag=calleE_tag;from-tag=calleR_tag'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_event_count(actual_count, expected_count) -> str:
    """
    Validates that the actual number of SubscribeLogEvent records matches
    the expected count.

    Args:
        actual_count: Actual number of SubscribeLogEvent records found.
        expected_count: Expected number of SubscribeLogEvent records.

    Returns:
        str: "PASSED" if the counts match, otherwise a "FAILED -> ..."
            message describing the mismatch.
    """
    try:
        assert actual_count == expected_count, (
            f"FAILED -> Expected {expected_count} 'SubscribeLogEvent' record(s), "
            f"got {actual_count}."
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_parameter_sequence(subscribe_log_events, expected_parameters) -> str:
    """
    Validates the 'parameter' field across a sequence of SubscribeLogEvent
    records against expected SIP Event header parameters.

    Checks that the number of log events matches the number of expected
    parameter sets, then compares each log event's normalized parameters
    against the corresponding expected normalized parameters.

    Args:
        subscribe_log_events: Sequence of SubscribeLogEvent records to
            validate.
        expected_parameters: Sequence of expected parameter lists, one
            per log event, in matching order.

    Returns:
        str: "PASSED" if all parameter sets match, otherwise a string
            describing the first mismatch encountered.
    """

    def _normalize_parameters(parameter_list) -> dict:
        normalized = {}
        for item in parameter_list or []:
            if not isinstance(item, dict):
                continue
            if "type" in item:
                normalized[str(item.get("type"))] = str(item.get("value"))
            else:
                for key, value in item.items():
                    normalized[str(key)] = str(value)
        return normalized

    try:
        assert subscribe_log_events, "NOT RUN -> No SubscribeLogEvent records found."
        assert len(subscribe_log_events) == len(expected_parameters), (
            "FAILED -> Number of SubscribeLogEvent records doesn't match number "
            "of expected parameter sets."
        )
        for idx, (log_event, expected) in enumerate(
            zip(subscribe_log_events, expected_parameters)
        ):
            actual_normalized = _normalize_parameters(log_event.parameter)
            expected_normalized = _normalize_parameters(expected)
            assert actual_normalized == expected_normalized, (
                f"FAILED -> 'parameter' at index {idx} doesn't match SIP Event header "
                f"parameters.\n***Expected***:\n{expected_normalized}\n"
                f"***Actual***:\n{actual_normalized}"
            )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_expiration_sequence(subscribe_log_events, expected_expirations) -> str:
    """
    Validates that 'expiration' is present on each SubscribeLogEvent
    record in the sequence.

    'expiration' MUST be present; '0' is recommended, but any value is
    acceptable for PASS. Only omission fails this check. To be revisited
    in a future revision.

    Args:
        subscribe_log_events: Sequence of SubscribeLogEvent records to
            validate.
        expected_expirations: Sequence of expected 'expiration' values,
            used only to determine the expected count.

    Returns:
        str: "PASSED" if 'expiration' is present on every log event,
            otherwise a string describing the first validation error
            encountered.
    """
    # 'expiration' MUST be present; '0' is recommended, but any value is
    # acceptable for PASS. Only omission fails this check.
    # To be revisited in a future revision.
    try:
        assert subscribe_log_events, "NOT RUN -> No SubscribeLogEvent records found."
        assert len(subscribe_log_events) == len(expected_expirations), (
            "FAILED -> Number of SubscribeLogEvent records doesn't match number "
            "of expected 'expiration' values."
        )
        for idx, log_event in enumerate(subscribe_log_events):
            assert (
                log_event.expiration is not None
                and str(log_event.expiration).strip() != ""
            ), (
                f"FAILED -> 'expiration' at index {idx} is missing. "
                "'expiration' MUST be present (any value is acceptable, '0' is recommended)."
            )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_response_sequence(subscribe_log_events, expected_responses) -> str:
    """
    Validates the 'response' field across a sequence of SubscribeLogEvent
    records against expected values.

    Checks that the number of log events matches the number of expected
    responses, then compares each log event's 'response' against the
    corresponding expected value.

    Args:
        subscribe_log_events: Sequence of SubscribeLogEvent records to
            validate.
        expected_responses: Sequence of expected 'response' values, one
            per log event, in matching order.

    Returns:
        str: "PASSED" if all 'response' values match, otherwise a string
            describing the first mismatch encountered.
    """
    try:
        assert subscribe_log_events, "NOT RUN -> No SubscribeLogEvent records found."
        assert len(subscribe_log_events) == len(expected_responses), (
            "FAILED -> Number of SubscribeLogEvent records doesn't match number "
            "of expected 'response' values."
        )
        for idx, (log_event, expected) in enumerate(
            zip(subscribe_log_events, expected_responses)
        ):
            assert log_event.response == expected, (
                f"FAILED -> 'response' at index {idx} doesn't match.\n"
                f"***Expected***:\n{expected}\n***Actual***:\n{log_event.response}"
            )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_purpose_sequence(subscribe_log_events, expected_purposes) -> str:
    """
    Validates the 'purpose' field across a sequence of SubscribeLogEvent
    records against expected values.

    Checks that the number of log events matches the number of expected
    purposes, then compares each log event's 'purpose' against the
    corresponding expected value.

    Args:
        subscribe_log_events: Sequence of SubscribeLogEvent records to
            validate.
        expected_purposes: Sequence of expected 'purpose' values, one per
            log event, in matching order.

    Returns:
        str: "PASSED" if all 'purpose' values match, otherwise a string
            describing the first mismatch encountered.
    """
    try:
        assert subscribe_log_events, "NOT RUN -> No SubscribeLogEvent records found."
        assert len(subscribe_log_events) == len(expected_purposes), (
            "FAILED -> Number of SubscribeLogEvent records doesn't match number "
            "of expected 'purpose' values."
        )
        for idx, (log_event, expected) in enumerate(
            zip(subscribe_log_events, expected_purposes)
        ):
            assert log_event.purpose == expected, (
                f"FAILED -> 'purpose' at index {idx} doesn't match.\n"
                f"***Expected***:\n{expected}\n***Actual***:\n{log_event.purpose}"
            )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def verify_subscription_id_format(subscription_id: str, event_type: str) -> str:
    """
    Validates the format of a subscription ID.

    Expected format example:
        urn:emergency:uid:subid:L1v0cPDQF3ZUGiU:esrp.911.gov

    Checks that the subscription ID contains:
        - the "urn:emergency:uid:subid:" prefix (URN);
        - a String ID of 10 to 32 alphanumeric characters following
          that prefix;
        - a valid domain name (FQDN) following the String ID.

    Args:
        subscription_id: Subscription ID value to validate.
        event_type: Event type used for contextual error messages.

    Returns:
        str: "PASSED" if all format checks succeed, otherwise a summary
            of which part(s) are invalid, formatted as "FAILED -> ...".
    """

    if not isinstance(subscription_id, str):
        return (
            f"FAILED -> 'subscriptionId' has invalid type for Event Type: '{event_type}'. "
            f"Expected str, got {type(subscription_id).__name__}. Actual: '{subscription_id}'"
        )

    if not subscription_id:
        return f"FAILED -> No 'subscriptionId' found for Event Type: '{event_type}'"

    errors = []

    if not re.search(SUBSCRIPTION_IDENTIFIER_URN_PATTERN, subscription_id):
        errors.append("URN prefix")

    string_id = extract_header_value_by_separator(subscription_id, ":", -2)
    if not string_id or not re.search(STRING_ID_PATTERN, string_id):
        errors.append("String ID")

    fqdn = extract_header_value_by_separator(subscription_id, ":", -1)
    if not fqdn or not re.search(FQDN_PATTERN, fqdn):
        errors.append("FQDN")

    if errors:
        return (
            f"FAILED -> 'subscriptionId' has invalid {', '.join(errors)} "
            f"for Event Type: '{event_type}'. Actual: '{subscription_id}'"
        )

    return "PASSED"


def validate_subscription_id_consistency(subscribe_log_events) -> str:
    """
    Validates the 'subscriptionId' field of each SubscribeLogEvent record.

    Checks that every log event's 'subscriptionId' has a valid format
    (via `verify_subscription_id_format`), then, when more than one log
    event is present, checks that the 'subscriptionId' is identical
    across all of them (i.e. consistent between the initial and any
    refresh/terminate records).

    Args:
        subscribe_log_events: Sequence of SubscribeLogEvent records to
            validate.

    Returns:
        str: "PASSED" if all 'subscriptionId' values are individually
            valid and consistent across records, otherwise a string
            describing the first validation error encountered.
    """
    try:
        assert subscribe_log_events, "NOT RUN -> No SubscribeLogEvent records found."

        for idx, log_event in enumerate(subscribe_log_events):
            result = verify_subscription_id_format(
                log_event.subscriptionId, "SubscribeLogEvent"
            )
            assert (
                result == "PASSED"
            ), f"FAILED -> 'subscriptionId' at index {idx}: {result}"

        if len(subscribe_log_events) == 1:
            return "PASSED"

        subscription_ids = {
            log_event.subscriptionId for log_event in subscribe_log_events
        }
        assert len(subscription_ids) == 1, (
            "FAILED -> 'subscriptionId' differs between the initial and "
            f"refresh/terminate SubscribeLogEvent records.\nActual values: {subscription_ids}"
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)
