from services.aux_services.message_services import normalize_string_for_comparison
from services.aux_services.xml_services import is_xml_equal, is_valid_xml


def _matches_raw_or_normalized(actual: str, expected: str) -> bool:
    """
    Returns True if `actual` matches `expected` either as an exact raw
    string, or after normalizing both values (e.g. whitespace, line
    endings) via `normalize_string_for_comparison`. Used for content
    that may not be valid XML and can't be compared structurally.
    """
    if actual == expected:
        return True
    return normalize_string_for_comparison(actual) == normalize_string_for_comparison(
        expected
    )


def validate_text_field(text_field_value: str, test_data, event_type: str) -> str:
    """
    Validates the 'text' field of an event against expected reference data.

    Depending on `variation_number`, compares `text_field_value`
    against a different reference source:
        - Variation 1: must contain the full body of the received HELD
          dereference response. Compared against
          `lis_to_chfe_response_message_body` as XML (using `is_xml_equal`).
        - Variation 2: must contain the full body of the received SIP
          NOTIFY message. If that body is empty, `text_field_value`
          must also be empty (exact equality). Otherwise, compares as
          XML if the body is valid XML, or as normalized strings. If no
          NOTIFY response/body is available, returns a "no reference
          data" failure.
        - Variation 3: must contain the exact body of the received
          malformed or invalid HTTP HELD response (the broken payload
          as received by the CHFE). Compared first as an exact raw
          string, and if that doesn't match, as normalized strings
          (via `normalize_string_for_comparison`) — not XML-parsed,
          since the body may not be valid XML. If no response was
          received at all (e.g. due to a network timeout),
          `text_field_value` must be an empty string.
        - Any other variation_number: returns an "unsupported variation"
          failure without comparing anything.

    Args:
        text_field_value: The 'text' field value extracted from the
            event payload to validate.
        test_data: TestData instance holding pcap-derived reference data
            (lis_to_chfe_response, lis_to_chfe_response_message_body,
            lis_to_chfe_notify_response, lis_to_chfe_notify_response_message_body,
            lis_to_chfe_http_response_message, variation_number, etc.).
        event_type: Event type used for contextual error messages.

    Returns:
        str: "PASSED" if validation succeeds, otherwise "FAILED -> ...".
    """
    try:
        if test_data.variation_number == 1:
            assert is_xml_equal(
                text_field_value, test_data.lis_to_chfe_response_message_body
            ), (
                f"FAILED -> 'text' field of '{event_type}' for Variation {test_data.variation_number} contains not the same value as LIS to CHFE HTTP HELD location response Body.\n"
                f"Actual: '{text_field_value}'\n"
                f"Expected: '{test_data.lis_to_chfe_response_message_body}'"
            )

        elif test_data.variation_number == 2:
            if (
                test_data.lis_to_chfe_notify_response
                and len(test_data.lis_to_chfe_notify_response_message_body) == 0
            ):

                assert (
                    text_field_value
                    == test_data.lis_to_chfe_notify_response_message_body
                ), (
                    f"FAILED -> 'text' field is not empty as LIS to CHFE NOTIFY response body.\n"
                    f"'text' field: '{text_field_value}'\n"
                    f"notify response body: '{test_data.lis_to_chfe_notify_response_message_body}'"
                )

            elif test_data.lis_to_chfe_notify_response_message_body:
                error_msg = (
                    f"FAILED -> 'text' field of '{event_type}' for Variation {test_data.variation_number} contains not the same value as LIS to CHFE NOTIFY response body.\n"
                    f"'text' field: {text_field_value}\n"
                    f"notify response body: {test_data.lis_to_chfe_notify_response_message_body}"
                )

                if is_valid_xml(test_data.lis_to_chfe_notify_response_message_body):
                    assert is_xml_equal(
                        text_field_value,
                        test_data.lis_to_chfe_notify_response_message_body,
                    ), error_msg
                else:
                    assert normalize_string_for_comparison(
                        text_field_value
                    ) == normalize_string_for_comparison(
                        test_data.lis_to_chfe_notify_response_message_body
                    ), error_msg

            else:
                return (
                    f"FAILED -> Cannot validate 'text' field for '{event_type}' "
                    f"Variation {test_data.variation_number}: no LIS to CHFE "
                    f"NOTIFY reference data available (neither NOTIFY "
                    f"response nor NOTIFY message body found)."
                )

        elif test_data.variation_number == 3:
            if not test_data.lis_to_chfe_http_response_message:
                # No HTTP response received at all
                assert text_field_value == "", (
                    f"FAILED -> No HTTP HELD response was received from LIS for "
                    f"'{event_type}' Variation {test_data.variation_number} "
                    f"(timeout), so 'text' field must be an empty string.\n"
                    f"Actual: '{text_field_value}'"
                )

            else:
                # Response received, but malformed/invalid — try an exact
                # raw match first, falling back to a normalized comparison,
                # since the body may not parse as XML.
                assert _matches_raw_or_normalized(
                    text_field_value, test_data.lis_to_chfe_response_message_body
                ), (
                    f"FAILED -> 'text' field of '{event_type}' for Variation {test_data.variation_number} does not contain the exact malformed/invalid HTTP HELD response body as received by the CHFE.\n"
                    f"Actual: '{text_field_value}'\n"
                    f"Expected: '{test_data.lis_to_chfe_response_message_body}'"
                )

        else:
            return (
                f"FAILED -> Cannot validate 'text' field for '{event_type}': "
                f"unsupported or missing variation_number "
                f"'{test_data.variation_number}'."
            )

        return "PASSED"
    except AssertionError as e:
        return str(e)
