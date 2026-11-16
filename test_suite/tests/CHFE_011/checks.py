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
from tests.CHFE_011.constants import TIMESTAMP_THRESHOLD, DIRECTIONS


def initial_validation_incoming_data(test_data, event_type):
    """
    Validates Initial Test Data (messages and IDs existence)

    Args:
        test_data: Instance of TestData containing test data for the test case.
        event_type: Type of event to check.
    """
    try:
        assert test_data.stimulus_message, "NOT RUN -> No stimulus message found."

        assert (
            test_data.invite_ok_response_message
        ), "FAILED -> No SIP 200 OK from CHFE to ESRP found."

        assert (
            test_data.stimulus_timestamp
        ), "FAILED -> No stimulus message timestamp found."

        assert (
            test_data.stimulus_call_sip_id
        ), "FAILED -> No stimulus call sip id 'Call-ID' found."

        assert (
            test_data.stimulus_call_id
        ), "FAILED -> No stimulus call id 'Call-Info' found."

        assert (
            test_data.stimulus_incident_id
        ), "FAILED -> No stimulus incident id 'Call-Info' found."

        assert test_data.invite_ok_sdp_body, "FAILED -> No CHFE OK response body found."

        if event_type == "RecMediaStartLogEvent":
            rec_media_pyload_data = test_data.rec_media_start_payload_data
            media_payload_data = test_data.media_start_payload_data
            post_to_logger = test_data.post_to_logger_start_event_messages

        else:
            rec_media_pyload_data = test_data.rec_media_end_payload_data
            media_payload_data = test_data.media_end_payload_data
            post_to_logger = test_data.post_to_logger_end_event_messages

            assert (
                test_data.esrp_bye_message
            ), "FAILED -> No ESRP to CHFE BYE message found."
            assert (
                test_data.bye_timestamp
            ), "FAILED -> No ESRP to CHFE BYE timestamp found."

        assert (
            post_to_logger
        ), f"FAILED -> No POST to logger messages or JWS data found for {event_type}. Please check 'certificate_key' configuration value."

        assert (
            media_payload_data
        ), f"FAILED -> No initial MediaLogEvent JWS payload data found for {event_type}."

        assert isinstance(
            media_payload_data, dict
        ), f"FAILED - Invalid initial MediaLogEvent JWS payload object format for {event_type}. Actual: {media_payload_data} Expected: 'dict'"

        assert (
            rec_media_pyload_data
        ), f"FAILED -> No {event_type} JWS payload data found."

        assert isinstance(
            rec_media_pyload_data, dict
        ), f"FAILED - Invalid {event_type} JWS payload object format. Actual: {rec_media_pyload_data} Expected: 'dict'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_rec_media_start_log_events(test_data):
    event_type = "RecMediaStartLogEvent"

    try:
        initial_data_check = initial_validation_incoming_data(test_data, event_type)
        assert initial_data_check == "PASSED", initial_data_check

        rec_media_start_check = rec_media_start_validation(test_data, event_type)
        assert rec_media_start_check == "PASSED", rec_media_start_check

        return "PASSED"
    except AssertionError as e:
        return str(e)


def rec_media_start_validation(test_data, event_type):
    """
    Validates RecMediaStartLog event data against expected session and SDP context.

    Args:
        test_data: Instance of TestData containing test data for the test case.
        event_type: RecMediaStartLogEvent type.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    required_fields = (
        "logEventType",
        "timestamp",
        "sdp",
    )

    log_event_type, timestamp, sdp_value = (
        test_data.rec_media_start_payload_data.get(key) for key in required_fields
    )

    try:
        # Required Fields Check
        assert_required_payload_fields(
            event_type, test_data.rec_media_start_payload_data, required_fields
        )

        # Check RecMediaStartLogEvent logEventType
        assert (
            log_event_type == event_type
        ), f"FAILED -> 'logEventType' value error. Actual: {log_event_type}, Expected: '{event_type}'"

        # Check RecMediaStartLogEvent timestamp
        assert is_timestamp(
            timestamp
        ), f"FAILED -> Wrong timestamp format for {event_type}. Actual: {timestamp}"

        assert (
            abs(iso_to_timestamp(timestamp) - test_data.stimulus_timestamp)
            <= TIMESTAMP_THRESHOLD
        ), (
            f"FAILED -> The time between the stimulus invite message and the {event_type} timestamp is greater then 1 sec:\n"
            f"{event_type} {float_timestamp_to_iso(test_data.stimulus_timestamp)} | JWS timestamp: {float_timestamp_to_iso(iso_to_timestamp(timestamp))}"
        )

        # Check RecMediaStartLogEvent common fields
        common_validation = common_fields_validation(event_type, test_data)
        assert common_validation == "PASSED", common_validation

        # Check RecMediaStartLogEvent optional fields
        optional_fields = optional_attributes_validation(event_type, test_data)
        assert optional_fields == "PASSED", optional_fields

        # Check RecMediaStartLogEvent SDP body
        if isinstance(test_data.invite_ok_sdp_body, str) and isinstance(sdp_value, str):
            assert test_data.invite_ok_sdp_body.rstrip() == sdp_value.rstrip(), (
                f"FAILED -> 'sdp' value for {event_type} is not equal to the sdp CHFE response body.\n"
                "###### SDP Value ######\n"
                f"{sdp_value}\n"
                "###### SDP CHFE response body ######\n"
                f"{test_data.invite_ok_sdp_body}"
            )
        else:
            return f"FAILED -> 'sdp' instances are not comparable as strings. CHFE response sdp: '{type(test_data.invite_ok_sdp_body)}', sdp value: '{type(sdp_value)}'"

        validate_events_relation_values = validate_events_relation(
            test_data.rec_media_start_payload_data,
            test_data.media_start_payload_data,
            event_type,
            "MediaStartLogEvent",
        )

        assert (
            validate_events_relation_values == "PASSED"
        ), validate_events_relation_values

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_rec_media_end_log_events(test_data):
    event_type = "RecMediaEndLogEvent"

    try:
        initial_data_check = initial_validation_incoming_data(test_data, event_type)
        assert initial_data_check == "PASSED", initial_data_check

        rec_media_end_check = rec_media_end_validation(test_data, event_type)
        assert rec_media_end_check == "PASSED", rec_media_end_check

        return "PASSED"
    except AssertionError as e:
        return str(e)


def rec_media_end_validation(test_data, event_type):
    """
    Validates RecMediaEndLog event data against expected session and SDP context.

    Args:
        test_data: Instance of TestData containing test data for the test case.
        event_type: RecMediaEndLogEvent type.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    required_fields = (
        "logEventType",
        "timestamp",
        "mediaQualityStats",
    )

    log_event_type, timestamp, media_quality_stats = (
        test_data.rec_media_end_payload_data.get(key) for key in required_fields
    )

    try:
        # Required Fields Check
        assert_required_payload_fields(
            event_type, test_data.rec_media_end_payload_data, required_fields
        )

        # Check RecMediaEndLogEvent logEventType
        assert (
            log_event_type == event_type
        ), f"FAILED -> 'logEventType' value error. Actual: {log_event_type}, Expected: '{event_type}'"

        # Check RecMediaEndLogEvent timestamp
        assert is_timestamp(
            timestamp
        ), f"FAILED -> Wrong timestamp format for {event_type}. Actual: {timestamp}"

        assert (
            abs(iso_to_timestamp(timestamp) - test_data.bye_timestamp)
            <= TIMESTAMP_THRESHOLD
        ), (
            f"FAILED - The time between the BYE CHFE message and the {event_type} timestamp is greater then 1 sec:\n"
            f"{event_type} {float_timestamp_to_iso(test_data.bye_timestamp)} | JWS timestamp: {float_timestamp_to_iso(iso_to_timestamp(timestamp))}"
        )

        # Check RecMediaEndLogEvent common fields
        common_validation = common_fields_validation(event_type, test_data)
        assert common_validation == "PASSED", common_validation

        # Check RecMediaEndLogEvent optional fields
        optional_fields = optional_attributes_validation(event_type, test_data)
        assert optional_fields == "PASSED", optional_fields

        # Check MediaQualityStats
        stats_dict = media_quality_stats_to_dict(media_quality_stats)
        validate_stats = validate_media_quality_stats(stats_dict)

        assert validate_stats == "PASSED", validate_stats

        validate_events_relation_values = validate_events_relation(
            test_data.rec_media_end_payload_data,
            test_data.media_end_payload_data,
            event_type,
            "MediaEndLogEvent",
        )

        assert (
            validate_events_relation_values == "PASSED"
        ), validate_events_relation_values

        return "PASSED"

    except AssertionError as e:
        return str(e)


def common_fields_validation(event_type: str, test_data):
    """
    Validates common fields between event payload and SDP body.

    Performs consistency checks between structured event data and SDP content,
    ensuring that required common attributes match expected values.

    Args:
        event_type (str): Event type used for assertion or error context.
        test_data: Instance of TestData containing test data for the test case.

    Returns:
        str: "PASSED" if all validations succeed, otherwise an error message string.
    """

    if event_type == "RecMediaStartLogEvent":
        payload_data = test_data.rec_media_start_payload_data
    else:
        payload_data = test_data.rec_media_end_payload_data

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
        equality_check = is_test_data_the_same(
            _extract_value(test_data.stimulus_call_id), call_id, error_msg
        )
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
            _extract_value(test_data.stimulus_incident_id), incident_id, error_msg
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
            _extract_value(test_data.stimulus_call_sip_id), call_id_sip, error_msg
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
        test_data.chfe_response_media_labels = extract_sdp_labels_from_string(
            test_data.invite_ok_sdp_body
        ) or [""]

        assert (
            test_data.chfe_response_media_labels
        ), "FAILED -> No CHFE SDP response media labels found."

        assert isinstance(media_label, list) or isinstance(
            media_label, str
        ), f"FAILED -> Invalid media_label value format for Event Type: '{event_type}'. Actual: '{media_label}' {type(media_label)} Expected: 'array' or 'string' type."

        if isinstance(media_label, list):
            assert all(
                isinstance(x, str) for x in media_label
            ), f"FAILED -> Not all 'mediaLabel' elements for Event Type: '{event_type}' are strings. Actual: {media_label}"
            assert (
                test_data.chfe_response_media_labels == media_label
            ), f"FAILED -> SDP Labels are not the same for Event Type: '{event_type}'. CHFE response: '{test_data.chfe_response_media_labels}', 'mediaLabel' value: '{media_label}'"
        elif isinstance(media_label, str):
            assert "+" in media_label and all(media_label.split("+")), (
                "FAILED -> 'mediaLabel' member on the mixed media stream should be a string \n"
                f"with value e.g. 'audio1+audio3'. Actual: '{media_label}'"
            )

        media_label_start = test_data.media_start_payload_data.get("mediaLabel")
        er_msg = f"'mediaLabel' value is not equal for '{event_type}' and 'MediaStartLogEvent'"

        media_labels_check = is_test_data_the_same(
            media_label, media_label_start, er_msg
        )
        assert media_labels_check == "PASSED", media_labels_check

        return "PASSED"

    except AssertionError as e:
        return str(e)


def optional_attributes_validation(event_type, test_data) -> str:
    """
    Validates optional attributes in an event payload.

    Performs checks on optional fields within the provided payload and
    validates their presence or correctness depending on expected rules.

    Args:
        event_type (str): Event type used for contextual assertion messages.
        test_data: Instance of TestData containing test data for the test case.

    Returns:
        str: "PASSED" if validation succeeds, otherwise an error message string.
    """

    if event_type == "RecMediaStartLogEvent":
        payload_data = test_data.rec_media_start_payload_data
    else:
        payload_data = test_data.rec_media_end_payload_data

    test_data.chfe_response_media_labels = extract_sdp_labels_from_string(
        test_data.invite_ok_sdp_body
    ) or [""]

    try:
        optional_fields = [
            "protocol",
            "ipAddressPort",
            "clientAssignedIdentifier",
            "agencyAgentId",
            "agencyPositionId",
            "extension",
            "mediaTranscodeFrom",
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

                if optional_field_name == "mediaTranscodeFrom":
                    assert (
                        optional_field_value in test_data.chfe_response_media_labels
                    ), (
                        "FAILED -> 'mediaTranscodeFrom' value is not in the original incoming stream media labels list.\n"
                        f"Original list: '{test_data.chfe_response_media_labels}', Transcoding: '{optional_field_value}'"
                    )

                else:
                    assert (
                        result := is_type(
                            optional_field_value, optional_field_name, str
                        )
                    ) == "PASSED", f"FAILED -> {result} Event: '{event_type}', field name: '{optional_field_name}'"

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_events_relation(
    rec_event: dict, media_event: dict, rec_event_type: str, media_event_type: str
) -> str:
    """
    Validates relation between start and end event payloads by comparing key fields.

    Ensures that both events belong to the same logical session by checking
    equality of required attributes.

    Args:
        rec_event (dict): RecMedia LogEvent payload data.
        media_event (dict): Media LogEvent payload data.
        rec_event_type (str): RecMedia Event type used for contextual assertion messages.
        media_event_type (str): Media Event type used for contextual assertion messages.

    Returns:
        str: "PASSED" if all required fields match, otherwise an error message
        describing the first mismatch found.
    """

    fields = ["callId", "incidentId", "callIdSip", "mediaLabel"]

    try:
        for field in fields:
            start_value = rec_event.get(field, None)
            end_value = media_event.get(field, None)
            assert start_value == end_value, (
                f"FAILED -> Values '{field}' between {rec_event_type} and {media_event_type} are not identical.\n"
                f"{rec_event_type}: '{start_value}' and {media_event_type}: '{end_value}'"
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
    event_type = "RecMediaEndLogEvent"

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


def _extract_value(s):
    return s.partition("<")[2].partition(">")[0] if "<" in s and ">" in s else s
