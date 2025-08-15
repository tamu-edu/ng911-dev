from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
    extract_non_variable_header_fields_with_values_for_sip_stimulus_and_output_message
)


def test_keeping_original_header_field(stimulus_header_fields, output_header_fields):
    """
    Test to validate if original headers fields are kept in output message
    :param stimulus_header_fields: list of header fields from stimulus SIP message
    :param output_header_fields: list of header fields from output SIP messages
    """
    for name, input_data in [('Stimulus header fields data', stimulus_header_fields),
                             ('Output header fields data', output_header_fields)]:
        if not input_data:
            return f"FAILED -> {name} is empty"
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
    for name, input_data in [('Stimulus data', stimulus), ('Output data', output)]:
        if not input_data:
            return f"FAILED -> {name} is empty"

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
    for name, input_data in [('Stimulus data', stimulus), ('Output data', output), ('Header_name data', header_name)]:
        if not input_data:
            return f"FAILED -> {name} is empty"

    try:
        assert output.sip.get(header_name), f"FAILED -> {header_name} header fields not found in output message"
        assert output.sip.get(header_name) not in extract_all_header_fields_matching_name_from_sip_message(
            header_name, stimulus), f"FAILED - top-most {header_name} entry is not the added one"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_urn_service_sos_in_request_uri(output):
    """
    Test to validate if 'urn:service:sos' is present in request URI
    :param output: Full SIP message sent by IUT
    """
    if not output:
        return "FAILED -> Cannot find BCF output message"
    try:
        request_line = output.sip.get('request_line', None)
        if request_line:
            splitted = request_line.split(' ')
        else:
            return "FAILED -> Cannot find 'urn:service:sos' in request URI"
        assert splitted[1] == 'urn:service:sos', f"FAILED -> Cannot find 'urn:service:sos' in request URI"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_urn_service_sos_in_to_header_field(output):
    """
    Test to validate if 'urn:service:sos' is present in request URI
    :param output: Full SIP message sent by IUT
    """
    if not output:
        return "FAILED -> Cannot find BCF output message"

    try:
        to_header = output.sip.get('to', None)

        first_part_of_to_header = str(to_header). \
            replace('\r', ''). \
            replace('\n', '').\
            split(';')[0]

        assert first_part_of_to_header == 'urn:service:sos', \
            f"FAILED -> Cannot find 'urn:service:sos' is in TO header field"
        return "PASSED"
    except AssertionError as e:
        return str(e)
