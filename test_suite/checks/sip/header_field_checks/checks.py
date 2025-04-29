from services.aux.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
    extract_non_variable_header_fields_with_values_for_sip_stimulus_and_output_message
)


def test_keeping_original_header_field(stimulus_header_fields, output_header_fields):
    """
    Test to validate if original headers fields are kept in output message
    :param stimulus_header_fields: list of header fields from stimulus SIP message
    :param output_header_fields: list of header fields from output SIP messages
    """
    try:
        assert all(stimulus_header in output_header_fields for stimulus_header in stimulus_header_fields), \
            f"FAILED -> output SIP message does not contain all header fields from original message"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_keeping_original_header_fields_in_sip_message(stimulus, output):
    """
    Test to validate if original header fields
    are kept in output message. Test is skipped for
    :param stimulus: Full SIP message received by IUT
    :param output: Full SIP message sent by IUT
    """
    try:
        stimulus_headers, output_headers = (
            extract_non_variable_header_fields_with_values_for_sip_stimulus_and_output_message(stimulus, output))
        assert stimulus_headers, "FAILED - not found non-variable header fields for stimulus SIP message"
        assert output_headers, "FAILED - not found non-variable header fields for output SIP message"
        assert all(stimulus_header in output_headers for stimulus_header in stimulus_headers), \
            "FAILED - output SIP message does not contain all non-variable header fields from original message"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_adding_header_field_on_top_of_its_section(stimulus, output, header_name: str):
    """
    Test to validate if added header field is a top-most entry in its section
    :param stimulus: Full SIP message received by IUT
    :param output: Full SIP message sent by IUT
    :param header_name: Name of header field to check
    """
    try:
        assert output.sip.get(header_name), f"FAILED -> {header_name} header fields not found in output message"
        assert output.sip.get(header_name) not in extract_all_header_fields_matching_name_from_sip_message(
            header_name, stimulus), f"FAILED - top-most {header_name} entry is not the added one"
        return "PASSED"
    except AssertionError as e:
        return str(e)
