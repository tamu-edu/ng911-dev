from checks.general.checks import is_data_present, is_test_data_the_same
from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.checks import (
    test_emergency_call_id_urn,
    test_emergency_call_id_string_id,
    test_emergency_call_id_fqdn,
    test_incident_tracking_id_urn,
    test_incident_tracking_id_string_id,
    test_incident_tracking_id_fqdn,
)
from services.aux_services.aux_services import validate_ip_port_combo
from services.aux_services.json_services import (
    is_valid_fqdn,
    iso_to_timestamp,
    float_timestamp_to_iso,
    is_timestamp,
)
from services.aux_services.sdp_services import (
    extract_sdp_labels_from_string,
    media_quality_stats_to_dict,
)
from services.aux_services.sip_msg_body_services import (
    is_valid_sip_call_id,
    is_valid_dialog_id,
)
from tests.CHFE_009.constants import TIMESTAMP_THRESHOLD, DIRECTIONS


def validate_media_start_end_log_events(
    stimulus_message,
    invite_ok_response_message,
    esrp_bye_message,
    key_found,
    post_to_logger_messages,
    media_start_payload_data,
    media_end_payload_data,
    stimulus_timestamp,
    bye_timestamp,
    invite_ok_sdp_body,
    stimulus_call_id,
    stimulus_incident_id,
    stimulus_call_sip_id,
):
    try:
        assert stimulus_message, "NOT RUN -> No stimulus message found."

        assert (
            invite_ok_response_message
        ), "FAILED -> No SIP 200 OK from CHFE to ESRP found."

        assert esrp_bye_message, "FAILED -> No SIP BYE message from ESRP to CHFE found."

        assert key_found, "FAILED -> JWS is signed but Certificate Key was not found."

        assert (
            post_to_logger_messages
        ), "FAILED -> No HTTP POST to logger messages found."

        assert (
            media_start_payload_data
        ), "FAILED -> No MediaStartLogEvent JWS payload data found."

        assert (
            media_end_payload_data
        ), "FAILED -> No MediaEndLogEvent JWS payload data found."

        assert isinstance(
            media_start_payload_data, dict
        ), f"FAILED - Invalid MediaStartLogEvent JWS payload object format. Actual: {media_start_payload_data} Expected: 'dict'"

        assert isinstance(
            media_end_payload_data, dict
        ), f"FAILED - Invalid MediaEndLogEvent JWS payload object format. Actual: {media_end_payload_data} Expected: 'dict'"

        assert stimulus_timestamp, "FAILED -> No stimulus message timestamp found."

        assert bye_timestamp, "FAILED -> No BYE message timestamp found."

        assert invite_ok_sdp_body, "FAILED -> No CHFE OK response body found."

        assert (
            stimulus_call_sip_id
        ), "FAILED -> No stimulus call sip id 'Call-ID' found."

        assert stimulus_call_id, "FAILED -> No stimulus call id 'Call-Info' found."

        assert (
            stimulus_incident_id
        ), "FAILED -> No stimulus incident id 'Call-Info' found."

        media_start_check = media_start_log_validation(
            media_start_payload_data,
            stimulus_timestamp,
            invite_ok_sdp_body,
            stimulus_call_sip_id,
            stimulus_call_id,
            stimulus_incident_id,
        )
        media_end_check = media_end_log_validation(
            media_end_payload_data,
            bye_timestamp,
            invite_ok_sdp_body,
            stimulus_call_sip_id,
            stimulus_call_id,
            stimulus_incident_id,
        )

        assert media_start_check == "PASSED", media_start_check

        assert media_end_check == "PASSED", media_end_check

        validate_events_relation_values = validate_events_relation(
            media_start_payload_data, media_end_payload_data
        )
        assert (
            validate_events_relation_values == "PASSED"
        ), validate_events_relation_values

        return "PASSED"
    except AssertionError as e:
        return str(e)


def media_start_log_validation(
    payload_data,
    stimulus_timestamp,
    invite_ok_sdp_body,
    stimulus_call_sip_id,
    stimulus_call_id,
    stimulus_incident_id,
):
    """
    Validates MediaStartLog event data against expected session and SDP context.

    Args:
        payload_data (dict): MediaEndLog event payload data.
        stimulus_timestamp (Any): Timestamp of the ыешьгдгы event used for validation.
        invite_ok_sdp_body (str): SDP body from the corresponding INVITE session.
        stimulus_call_sip_id (str): Call-ID from the corresponding STIMULUS session.
        stimulus_call_id (str): Call-Info from the corresponding STIMULUS session.
        stimulus_incident_id (str): Call-Info from the corresponding STIMULUS session.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    event_type = "MediaStartLogEvent"

    required_fields = (
        "logEventType",
        "timestamp",
        "sdp",
    )

    log_event_type, timestamp, sdp_value = (
        payload_data.get(key) for key in required_fields
    )

    try:
        # Required Fields Check
        assert_required_payload_fields(event_type, payload_data, required_fields)

        # Check MediaStartLogEvent logEventType
        assert (
            log_event_type == event_type
        ), f"FAILED -> 'logEventType' value error. Actual: {log_event_type}, Expected: '{event_type}'"

        # Check MediaStartLogEvent timestamp
        assert is_timestamp(
            timestamp
        ), f"FAILED -> Wrong timestamp format for {event_type}. Actual: {timestamp}"

        assert (
            abs(iso_to_timestamp(timestamp) - stimulus_timestamp) <= TIMESTAMP_THRESHOLD
        ), (
            f"FAILED -> The time between the stimulus invite message and the {event_type} timestamp is greater then 1 sec:\n"
            f"{event_type} {float_timestamp_to_iso(stimulus_timestamp)} | JWS timestamp: {float_timestamp_to_iso(iso_to_timestamp(timestamp))}"
        )

        # Check MediaStartLogEvent common fields
        common_validation = common_fields_validation(
            event_type,
            payload_data,
            invite_ok_sdp_body,
            stimulus_call_sip_id,
            stimulus_call_id,
            stimulus_incident_id,
        )
        assert common_validation == "PASSED", common_validation

        # Check MediaStartLogEvent optional fields
        optional_fields = optional_attributes_validation(event_type, payload_data)
        assert optional_fields == "PASSED", optional_fields

        # Check MediaStartLogEvent SDP body
        if isinstance(invite_ok_sdp_body, str) and isinstance(sdp_value, str):
            assert invite_ok_sdp_body.rstrip() == sdp_value.rstrip(), (
                f"FAILED -> 'sdp' value for {event_type} is not equal to the sdp CHFE response body.\n"
                "###### SDP Value ######\n"
                f"{sdp_value}\n"
                "###### SDP CHFE response body ######\n"
                f"{invite_ok_sdp_body}"
            )
        else:
            return f"FAILED -> 'sdp' instances are not comparable as strings. CHFE response sdp: '{type(invite_ok_sdp_body)}', sdp value: '{type(sdp_value)}'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def media_end_log_validation(
    payload_data,
    bye_timestamp,
    invite_ok_sdp_body,
    stimulus_call_sip_id,
    stimulus_call_id,
    stimulus_incident_id,
):
    """
    Validates MediaEndLog event data against expected session and SDP context.

    Args:
        payload_data (dict): MediaEndLog event payload data.
        bye_timestamp (Any): Timestamp of the BYE event used for validation.
        invite_ok_sdp_body (str): SDP body from the corresponding INVITE session.
        stimulus_call_sip_id (str): Call-ID from the corresponding STIMULUS session.
        stimulus_call_id (str): Call-Info from the corresponding STIMULUS session.
        stimulus_incident_id (str): Call-Info from the corresponding STIMULUS session.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    event_type = "MediaEndLogEvent"

    required_fields = (
        "logEventType",
        "timestamp",
        "mediaQualityStats",
    )

    log_event_type, timestamp, media_quality_stats = (
        payload_data.get(key) for key in required_fields
    )

    try:
        # Required Fields Check
        assert_required_payload_fields(event_type, payload_data, required_fields)

        # Check MediaEndLogEvent logEventType
        assert (
            log_event_type == event_type
        ), f"FAILED -> 'logEventType' value error. Actual: {log_event_type}, Expected: '{event_type}'"

        # Check MediaEndLogEvent timestamp
        assert is_timestamp(
            timestamp
        ), f"FAILED -> Wrong timestamp format for {event_type}. Actual: {timestamp}"

        assert (
            abs(iso_to_timestamp(timestamp) - bye_timestamp) <= TIMESTAMP_THRESHOLD
        ), (
            f"FAILED - The time between the BYE CHFE message and the {event_type} timestamp is greater then 1 sec:\n"
            f"{event_type} {float_timestamp_to_iso(bye_timestamp)} | JWS timestamp: {float_timestamp_to_iso(iso_to_timestamp(timestamp))}"
        )

        # Check MediaEndLogEvent common fields
        common_validation = common_fields_validation(
            event_type,
            payload_data,
            invite_ok_sdp_body,
            stimulus_call_sip_id,
            stimulus_call_id,
            stimulus_incident_id,
        )
        assert common_validation == "PASSED", common_validation

        # Check MediaEndLogEvent optional fields
        optional_fields = optional_attributes_validation(event_type, payload_data)
        assert optional_fields == "PASSED", optional_fields

        # Check mediaQualityStats
        stats_dict = media_quality_stats_to_dict(media_quality_stats)
        validate_stats = validate_media_quality_stats(stats_dict)

        assert validate_stats == "PASSED", validate_stats

        return "PASSED"
    except AssertionError as e:
        return str(e)


def common_fields_validation(
    event_type: str,
    payload_data: dict,
    invite_ok_sdp_body: str,
    stimulus_call_sip_id: str,
    stimulus_call_id: str,
    stimulus_incident_id: str,
):
    """
    Validates common fields between event payload and SDP body.

    Performs consistency checks between structured event data and SDP content,
    ensuring that required common attributes match expected values.

    Args:
        event_type (str): Event type used for assertion or error context.
        payload_data (dict): Event payload data to validate against.
        invite_ok_sdp_body (str): SDP body used for comparison with payload data.
        stimulus_call_sip_id (str): Call-ID from the corresponding STIMULUS session.
        stimulus_call_id (str): Call-Info from the corresponding STIMULUS session.
        stimulus_incident_id (str): Call-Info from the corresponding STIMULUS session.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """
    required_fields = (
        "elementId",
        "agencyId",
        "callId",
        "incidentId",
        "callIdSip",
        "direction",
        "mediaLabel",
    )

    element_id, agency_id, call_id, incident_id, call_id_sip, direction, media_label = (
        payload_data.get(key) for key in required_fields
    )

    try:
        # Required Fields Check
        assert_required_payload_fields(event_type, payload_data, required_fields)

        # elementId check
        assert is_valid_fqdn(
            element_id
        ), f"FAILED - 'elementId' in {event_type} JWS should be a valid FQDN format. Actual: '{element_id}'"

        # agencyId check
        assert is_valid_fqdn(
            agency_id
        ), f"FAILED - 'agencyId' in {event_type} JWS should be a valid FQDN format. Actual: '{agency_id}'"

        # callId check
        error_msg = (
            f"'{event_type}' 'callId' not the same as in Stimulus 'Call-Info callId'"
        )
        equality_check = is_test_data_the_same(stimulus_call_id, call_id, error_msg)
        assert equality_check == "PASSED", equality_check

        assert (
            result := test_emergency_call_id_urn(call_id)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        assert (
            result := test_emergency_call_id_string_id(call_id)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        assert (
            result := test_emergency_call_id_fqdn(call_id)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        # incidentId check
        error_msg = f"'{event_type}' 'incidentId' not the same as in Stimulus 'Call-Info incidentId'"
        equality_check = is_test_data_the_same(
            stimulus_incident_id, incident_id, error_msg
        )
        assert equality_check == "PASSED", equality_check
        assert (
            result := test_incident_tracking_id_urn(incident_id)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        assert (
            result := test_incident_tracking_id_string_id(incident_id)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        assert (
            result := test_incident_tracking_id_fqdn(incident_id)
        ) == "PASSED", f"FAILED -> {result} for Event Type: '{event_type}'"

        # callIdSip check
        error_msg = f"'{event_type}' 'callIdSip' not the same as in Stimulus 'Call-ID callIdSip'"
        equality_check = is_test_data_the_same(
            stimulus_call_sip_id, call_id_sip, error_msg
        )
        assert equality_check == "PASSED", equality_check
        assert is_valid_sip_call_id(
            call_id_sip
        ), f"FAILED - 'callIdSip' in '{event_type}' JWS should be a valid SIP Call ID. Actual: '{call_id_sip}'"

        # direction check
        assert (
            direction.lower() in DIRECTIONS
        ), f"FAILED - 'direction' value in '{event_type}' JWS should be one of {DIRECTIONS}. Actual: '{direction}'"

        # Check media_label
        assert isinstance(
            media_label, list
        ), f"FAILED -> Invalid media_label value format for Event Type: '{event_type}'. Actual: '{media_label}' {type(media_label)} Expected: 'list' []"

        chfe_response_labels = extract_sdp_labels_from_string(invite_ok_sdp_body) or [
            ""
        ]
        assert all(
            isinstance(x, str) for x in media_label
        ), f"FAILED -> Not all 'mediaLabel' elements for Event Type: '{event_type}' are strings. Actual: {media_label}"
        assert (
            chfe_response_labels == media_label
        ), f"FAILED -> SDP Labels are not the same for Event Type: '{event_type}'. CHFE response: '{chfe_response_labels}', 'mediaLabel' value: '{media_label}'"

        return "PASSED"

    except AssertionError as e:
        return str(e)


def optional_attributes_validation(event_type, payload_data: dict) -> str:
    """
    Validates optional attributes in an event payload.

    Performs checks on optional fields within the provided payload and
    validates their presence or correctness depending on expected rules.

    Args:
        event_type (str): Event type used for contextual assertion messages.
        payload_data (dict): Event payload data to validate.

    Returns:
        str: "PASSED" if validation succeeds, otherwise an error message string.
    """
    try:
        optional_fields = [
            "protocol",
            "ipAddressPort",
            "clientAssignedIdentifier",
            "agencyAgentId",
            "agencyPositionId",
            "extension",
        ]

        for optional_field_name in optional_fields:
            optional_field_value = payload_data.get(optional_field_name, None)
            if optional_field_value is not None:
                if optional_field_name == "ipAddressPort":
                    ip_address_value = payload_data.get("ipAddressPort", None)

                    if ip_address_value is not None:
                        assert validate_ip_port_combo(
                            ip_address_value
                        ) or is_valid_fqdn(
                            ip_address_value
                        ), f"FAILED -> Invalid IP:PORT or FQDN value for '{event_type}'. Received: '{ip_address_value}'"
                else:
                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, str
                        )
                    ) == "PASSED", f"FAILED -> {result} Event: '{event_type}', field name: '{optional_field_name}'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_events_relation(start_event: dict, end_event: dict) -> str:
    """
    Validates relation between start and end event payloads by comparing key fields.

    Ensures that both events belong to the same logical session by checking
    equality of required attributes.

    Args:
        start_event (dict): MediaStartLogEvent payload data.
        end_event (dict): MediaEndLogEvent payload data.

    Returns:
        str: "PASSED" if all required fields match, otherwise an error message
        describing the first mismatch found.
    """

    fields = ["callId", "incidentId", "callIdSip", "mediaLabel"]

    try:
        for field in fields:
            start_value = start_event.get(field, None)
            end_value = end_event.get(field, None)
            assert start_value == end_value, (
                f"FAILED -> Field values '{field}' between MediaStartLogEvent and MediaEndLogEvent are not identical.\n"
                f"MediaStartLogEvent: '{start_value}' and MediaEndLogEvent: '{end_value}'"
            )

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_media_quality_stats(media_stats: dict) -> str:
    """
    Validates parsed media quality statistics structure.

    Ensures that required sections and expected keys, values are present and
    contain expected data or data type.

    Args:
        media_stats (dict): Parsed media quality statistics dictionary.

    Returns:
        str: "PASSED" if validation succeeds, otherwise an error message
        describing the validation failure.
    """
    event_type = "MediaEndLogEvent"

    required_fields = (
        "VQSessionReport",
        "SessionDesc",
        "LocalMetrics",
        "RemoteMetrics",
        "DialogID",
    )

    metric_keys = ("Jitter", "PacketLoss", "Delay", "MOSLQ")

    (
        vq_session_report_value,
        session_desc_value,
        local_metrics_value,
        remote_metrics_value,
        dialog_id_value,
    ) = (media_stats.get(key) for key in required_fields)

    try:
        # Required Fields Check
        assert_required_payload_fields(event_type, media_stats, required_fields)

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
        ), f"FAILED -> Missing LocalMetrics objects: {[k for k in metric_keys if k not in remote_metrics_value]}"

        assert all(
            isinstance(remote_metrics_value[k], (int, float)) for k in metric_keys
        ), f"FAILED -> Invalid RemoteMetrics values: { {k: remote_metrics_value.get(k) for k in metric_keys if not isinstance(remote_metrics_value.get(k), (int, float))} }. Expected int or float value."

        # Check DialogID
        assert is_valid_dialog_id(
            dialog_id_value
        ), f"FAILED -> Invalid 'DialogID' value format. Actual: '{dialog_id_value}' Expected: '<anything>@<FQDN>;to-tag=<value>;from-tag=<value>'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def assert_required_payload_fields(
    event_type: str, payload_data: dict, fields: tuple[str, ...]
) -> None:
    for field in fields:
        value = payload_data.get(field)
        error_msg = f"FAILED -> No '{field}' object found in {event_type} payload data."
        msg = is_data_present(value, error_msg)
        assert msg == "PASSED", msg
