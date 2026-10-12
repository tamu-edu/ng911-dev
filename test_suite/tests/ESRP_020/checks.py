import re

from services.aux_services.json_services import (
    float_timestamp_to_iso,
    iso_to_timestamp,
    is_timestamp,
)
from tests.ESRP_020.constants import (
    TIMESTAMP_THRESHOLD,
    STATUS_CODES_REGISTRY,
)


def validate_event_count(events, expected, event_type_name) -> str:
    """Asserts that exactly ``expected`` log events of ``event_type_name`` were captured."""
    try:
        actual = len(events) if events else 0
        assert (
            actual == expected
        ), f"FAILED -> Expected {expected} '{event_type_name}' events, got {actual}."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def compare_timestamps(
    esrp_to_adr_timestamps,
    log_events_timestamps,
    threshold=TIMESTAMP_THRESHOLD,
):
    """Assert each log-event timestamp is within ``threshold`` seconds of the paired ESRP-to-ADR request timestamp.

    :param esrp_to_adr_timestamps: List of ESRP-to-ADR HTTP request capture
        timestamps.
    :param log_events_timestamps: List of ISO-8601 timestamps taken from
        AdditionalData log events, paired positionally with
        ``esrp_to_adr_timestamps``.
    :param threshold: Maximum allowed difference in seconds between paired
        timestamps.
    :return: ``"PASSED"`` when all pairs are within tolerance, otherwise a
        ``"FAILED -> ..."`` message.
    """
    try:
        assert (
            esrp_to_adr_timestamps
        ), "FAILED-> Cannot find find ESRP to ADR timestamps."
        assert log_events_timestamps, "FAILED-> Cannot find find log events timestamps."
        assert len(esrp_to_adr_timestamps) == len(
            log_events_timestamps
        ), "FAILED-> Number of ESRPs HTTP requests to ADR's doesn't match to number of log events"
        for idx, timestamp in enumerate(esrp_to_adr_timestamps):
            le_timestamp = log_events_timestamps[idx]
            assert is_timestamp(
                le_timestamp
            ), f"FAILED-> Invalid Timestamp: {le_timestamp}"
            iso_timestamp = iso_to_timestamp(log_events_timestamps[idx])
            assert is_timestamp(
                float_timestamp_to_iso(timestamp)
            ), f"FAILED-> Invalid Timestamp: {timestamp}"
            assert round(iso_timestamp - timestamp, 2) <= threshold, (
                f"FAILED -> 'timestamp' difference exceeds {threshold}s threshold.\n"
                f"HTTP GET: {float_timestamp_to_iso(timestamp)} | "
                f"Log event: {float_timestamp_to_iso(log_events_timestamps[idx])}"
            )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def check_response_status(additional_data_response_list, is_variation_2) -> str:
    try:
        assert (
            additional_data_response_list
        ), "FAILED-> Cannot find find ESRP AdditionalDataResponseLogEvent messages."
        for log_event_msg in additional_data_response_list:
            match = re.search(r"\d{3}", log_event_msg.response_status)
            result = int(match.group()) if match else None
            if is_variation_2:
                # find a 3-digit code
                assert (
                    result
                ), "FAILED -> Cannot find 'responseStatus' in AdditionalDataResponseLogEvent message."
                assert (
                    result in STATUS_CODES_REGISTRY.keys()
                ), f"FAILED -> Status code not found in registry: {result}"
            else:
                assert not result, (
                    "FAILED -> Status code found in registry.\n"
                    "responseStatus is {}.\n"
                    "For Variation #1 responseStatus should not be present".format(
                        result
                    )
                )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_response_id_match_to_query_id(
    additional_data_response_list, additional_data_query_list
):
    try:
        assert (
            additional_data_query_list
        ), "FAILED -> No AdditionalDataQueryLogEvent messages found."
        assert (
            additional_data_response_list
        ), "FAILED -> No AdditionalDataResponseLogEvent messages found."

        for idx, query_log_event_msg in enumerate(additional_data_query_list):
            assert (
                query_log_event_msg.query_id
                == additional_data_response_list[idx].response_id
            ), "FAILED -> 'queryId' in AdditionalDataQueryLogEvent doesn't match 'responseId' in AdditionalDataResponseLogEvent"
        return "PASSED"
    except AssertionError as e:
        return str(e)
