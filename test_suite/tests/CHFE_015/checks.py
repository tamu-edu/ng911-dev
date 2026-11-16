from services.aux_services.message_services import normalize_string_for_comparison
from services.aux_services.xml_services import is_xml_equal, is_valid_xml


def validate_text_field(text_field_value: str, test_data, event_type: str) -> str:
    """
    Validates the 'text' field of an event against expected reference data.

    Depending on `variation_number`, compares `text_field_value`
    against a different reference source:
        - Variation 1: compares against the CHFE to LIS HTTP POST message
          body as XML (using `is_xml_equal`).
        - Variation 2: compares against the CHFE to LIS SUBSCRIBE message
          body, if a SUBSCRIBE request was found. If that body is empty,
          `text_field_value` must also be empty (exact equality).
          Otherwise, compares as XML if the body is valid XML, or as
          normalized strings. If no SUBSCRIBE request/body is available,
          returns a "no reference data" failure.
        - Any other variation_number: returns an "unsupported variation"
          failure without comparing anything.

    Args:
        text_field_value: The 'text' field value extracted from the
            event payload to validate.
        test_data: TestData instance holding pcap-derived reference data
            (chfe_to_lis_http_post_message_body, chfe_to_lis_subscribe_request,
            chfe_to_lis_subscribe_message_body, variation_number, etc.).
        event_type: Event type used for contextual error messages.

    Returns:
        str: "PASSED" if validation succeeds, otherwise "FAILED -> ...".
    """
    try:
        if test_data.variation_number == 1:
            assert is_xml_equal(
                text_field_value, test_data.chfe_to_lis_http_post_message_body
            ), (
                f"FAILED -> 'text' field of '{event_type}' for Variation {test_data.variation_number} contains not the same value as CHFE to LIS HTTP POST Body.\n"
                f"Actual: '{text_field_value}'\n"
                f"Expected: '{test_data.chfe_to_lis_http_post_message_body}'"
            )

        elif test_data.variation_number == 2:
            if (
                test_data.chfe_to_lis_subscribe_request
                and len(test_data.chfe_to_lis_subscribe_message_body) == 0
            ):

                assert (
                    text_field_value == test_data.chfe_to_lis_subscribe_message_body
                ), (
                    f"FAILED -> 'text' field is not empty as CHFE to LIS SUBSCRIBE body.\n"
                    f"'text' field: '{text_field_value}'\n"
                    f"subscribe body: '{test_data.chfe_to_lis_subscribe_message_body}'"
                )

            elif test_data.chfe_to_lis_subscribe_message_body:
                error_msg = (
                    f"FAILED -> 'text' field of '{event_type}' for Variation {test_data.variation_number} contains not the same value as CHFE to LIS SUBSCRIBE body.\n"
                    f"'text' field: {text_field_value}\n"
                    f"subscribe body: {test_data.chfe_to_lis_subscribe_message_body}"
                )

                if is_valid_xml(test_data.chfe_to_lis_subscribe_message_body):
                    assert is_xml_equal(
                        text_field_value, test_data.chfe_to_lis_subscribe_message_body
                    ), error_msg
                else:
                    assert normalize_string_for_comparison(
                        text_field_value
                    ) == normalize_string_for_comparison(
                        test_data.chfe_to_lis_subscribe_message_body
                    ), error_msg

            else:
                return (
                    f"FAILED -> Cannot validate 'text' field for '{event_type}' "
                    f"Variation {test_data.variation_number}: no CHFE to LIS "
                    f"SUBSCRIBE reference data available (neither subscribe "
                    f"request nor subscribe message body found)."
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
