import re

from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
    extract_non_variable_header_fields_with_values_for_sip_stimulus_and_output_message,
    get_list_of_all_header_fields_from_sip_message,
)

_TAG_PARAM_PATTERN = re.compile(r";tag=[^;>\s\r\n]+")
_HOST_ONLY_HEADERS = {"via", "from"}
_VALID_VERSTAT_VALUES = {
    "TN-Validation-Passed",
    "TN-Validation-Failed",
    "No-TN-Validation",
}
_VALID_RESOURCE_PRIORITY_PATTERN = re.compile(r"^esnet\.[012]$")


def _extract_host(header: str) -> str | None:
    """Extract the first IP address or FQDN found in a SIP header line."""
    match = re.search(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", header)
    if match:
        return match.group(1)
    match = re.search(r"\b([a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z]{2,})\b", header)
    if match:
        return match.group(1)
    return None


def _extract_single_header_value(message, header_name: str):
    """Return the stripped value of the first matching header, or None if absent."""
    headers = extract_all_header_fields_matching_name_from_sip_message(
        message, header_name
    )
    if not headers:
        return None
    try:
        _, _, value = headers[0].partition(":")
    except ValueError:
        return None
    return value.strip()


def test_keeping_original_header_field(stimulus, output, header_field_name: str):
    """
    Test to validate if original headers fields are kept in output message
    :param stimulus: Full SIP message received by IUT
    :param output: Full SIP message sent by IUT
    :param header_field_name: Name of header field to check
    """
    for name, input_data in [
        ("Stimulus header fields data", stimulus),
        ("Output header fields data", output),
        ("Header field name", header_field_name),
    ]:
        if not input_data:
            return f"FAILED -> {name} is empty"

    try:
        assert extract_all_header_fields_matching_name_from_sip_message(
            stimulus, header_field_name
        ) <= extract_all_header_fields_matching_name_from_sip_message(
            output, header_field_name
        ), "FAILED -> output SIP message does not contain all header fields from original message"
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
    for name, input_data in [("Stimulus data", stimulus), ("Output data", output)]:
        if not input_data:
            return f"FAILED -> {name} is empty"

    try:
        stimulus_headers, output_headers = (
            extract_non_variable_header_fields_with_values_for_sip_stimulus_and_output_message(
                stimulus, output
            )
        )
        assert (
            stimulus_headers
        ), "FAILED - not found non-variable header fields for stimulus SIP message"
        assert (
            output_headers
        ), "FAILED - not found non-variable header fields for output SIP message"
        output_map: dict = {}
        for entry in output_headers:
            for key, value in entry.items():
                output_map.setdefault(key, []).append(value)

        missing_headers = []
        for header in stimulus_headers:
            for key, value in header.items():
                output_values = output_map.get(key)
                if not output_values or not any(
                    value in output_value for output_value in output_values
                ):
                    missing_headers.append(header)

        def _format_header(entry):
            if isinstance(entry, dict):
                return "\n".join(f"{k}: {v}" for k, v in entry.items())
            return str(entry)

        assert not missing_headers, (
            "FAILED - output SIP message is missing the following header fields "
            "from original message:\n"
            + "\n".join(_format_header(h) for h in missing_headers)
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_adding_header_field_on_top_of_its_section(
    stimulus, output, header_field_name: str, is_incremented_expected=True
):
    """
    Test to validate if added header field is a top-most entry in its section
    :param stimulus: Full SIP message received by IUT
    :param output: Full SIP message sent by IUT
    :param header_field_name: Name of header field to check
    :param is_incremented_expected: by default there should be +1 record with added to Route, Via, From
    in case we compare between to INVITE messages. Shouldn't be applicable when comparing INVITE and 200 OK
    """
    for name, input_data in [
        ("Stimulus header fields data", stimulus),
        ("Output header fields data", output),
        ("Header field name", header_field_name),
    ]:
        if not input_data:
            return f"FAILED -> {name} is empty"

    stimulus_headers = extract_all_header_fields_matching_name_from_sip_message(
        stimulus, header_field_name
    )
    output_headers = extract_all_header_fields_matching_name_from_sip_message(
        output, header_field_name
    )

    try:
        assert output_headers and all(
            header_field_name in header for header in output_headers
        ), f"FAILED -> {header_field_name} header fields not found in output message"

        if is_incremented_expected:
            assert (
                stimulus_headers != output_headers
            ), "FAILED -> Not found any added header fields"
            new_host = _extract_host(output_headers[0])
            assert new_host and not any(
                new_host in s for s in stimulus_headers
            ), f"FAILED -> Top-most {header_field_name} is not added item"

        assert all(
            (host := _extract_host(s)) and any(host in h for h in output_headers)
            for s in stimulus_headers
        ), f"FAILED -> Some {header_field_name} header fields were removed in output message"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_header_unchanged_if_equals(
    stimulus_value: str, output_values: list, expected_value: str
):
    """
    If stimulus_value equals expected_value, all output_values must also equal expected_value.
    If stimulus had a different value, change is allowed (exception).
    :param stimulus_value: Extracted header value from stimulus message
    :param output_values: List of extracted header values from output messages
    :param expected_value: Value that triggers the unchanged requirement
    """
    if not output_values:
        return "FAILED -> Output values list is empty"

    if all((x is None for x in output_values)):
        return "FAILED -> Output values cannot be 'None'"

    if stimulus_value == expected_value:
        return "PASSED"

    try:
        for idx, output_value in enumerate(output_values, start=1):
            # output_valu.strip(;) and find expected_value in strips
            assert (
                expected_value in output_value
            ), f"FAILED -> Header changed from '{expected_value}' in output {idx}.\n  Actual: {output_value}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_resource_priority_unchanged_if_valid(
    stimulus_rp, outputs: list, message_descriptions_list: list
):
    """
    Validates Resource-Priority header across output messages based on the stimulus value.

    Two scenarios:

    1. Stimulus has NO Resource-Priority or an INVALID value (not esnet.0/1/2):
       No output message may introduce a valid esnet Resource-Priority value.

    2. Stimulus has a VALID Resource-Priority value (esnet.0, esnet.1, or esnet.2):
       Every output must preserve that exact value unchanged.

    :param stimulus_rp: Extracted Resource-Priority value from the stimulus message, or None
    :param outputs: List of extracted Resource-Priority values from output messages
    """
    if not outputs:
        return "FAILED -> Outputs list is empty"

    try:
        if not stimulus_rp or not _VALID_RESOURCE_PRIORITY_PATTERN.match(stimulus_rp):
            for idx, output_rp in enumerate(outputs, start=1):
                assert output_rp and _VALID_RESOURCE_PRIORITY_PATTERN.match(
                    output_rp
                ), f"FAILED -> Resource-Priority in output {message_descriptions_list[idx-1]} has unexpected esnet value.\n  Actual: {output_rp}"
        else:
            for idx, output_rp in enumerate(outputs, start=1):
                assert (
                    stimulus_rp == output_rp
                ), f"FAILED -> Resource-Priority changed in output {idx}.\nExpected: {stimulus_rp}\n  Actual: {output_rp}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_from_unchanged_if_valid_verstat(
    stimulus: str, outputs: list, message_descriptions_list: list
):
    """
    Validates the From header's verstat parameter across output messages based on
    whether the stimulus contained a valid or invalid verstat value.

    Two scenarios:

    1. Stimulus has NO verstat param, OR a VALID verstat value
       (TN-Validation-Passed, TN-Validation-Failed, No-TN-Validation):
       The From header must remain byte-for-byte identical in every output message.

    2. Stimulus has an INVALID verstat value (any value outside the valid set):
       The verstat parameter must be removed — no output message may contain
       a verstat param in the From header. If an output message is missing entirely,
       the result is NOT RUN for that message.

    :param stimulus: From header value string from the stimulus message
    :param outputs: List of From header value strings from output messages
    :param message_descriptions_list: Human-readable labels for each output message,
                                      used in failure/not-run descriptions
    """
    if message_descriptions_list is None:
        message_descriptions_list = []
    if not stimulus:
        return "FAILED -> Stimulus From header value is empty"
    if not outputs:
        return "FAILED -> Outputs list is empty"

    stimulus_from = stimulus.replace("\r", "").replace("\n", "").strip()
    verstat_match = re.search(r"verstat=([^;>\s\r\n]+)", stimulus_from)
    try:
        if verstat_match and verstat_match.group(1) not in _VALID_VERSTAT_VALUES:
            for idx, msg in enumerate(outputs, start=1):
                if not msg:
                    return f"NOT RUN -> {message_descriptions_list[idx-1]} has not been found"
                match = re.search(r"verstat=([^;>\s\r\n]+)", msg)
                if match:
                    verstat_value = match.group().strip("verstat=")
                    assert verstat_value in _VALID_VERSTAT_VALUES, (
                        f"FAILED -> 'Varstat' value for {message_descriptions_list[idx-1]} is invalid:\n"
                        f"Actual value: {verstat_value}\n"
                        f"Expected values: {_VALID_VERSTAT_VALUES}"
                    )

            return "PASSED"

        else:
            for idx, output in enumerate(outputs, start=1):
                if not output:
                    return f"NOT RUN -> {message_descriptions_list[idx-1]} has not been found"
                output_from = output.replace("\r", "").replace("\n", "").strip()
                assert (
                    stimulus_from == output_from
                ), f"FAILED -> From header changed in output {idx}.\nExpected: {stimulus_from}\n  Actual: {output_from}"
            return "PASSED"
    except AssertionError as e:
        return str(e)


def test_all_header_fields_are_same(
    messages: list,
    exception_headers: list,
    message_descriptions_list: list,
):
    """
    Validates that all header fields are the same across all provided SIP messages,
    ignoring headers listed in exception_headers.
    :param messages: List of full SIP messages to compare
    :param exception_headers: List of header field names to exclude from comparison
    """
    if not messages:
        return "FAILED -> Messages list is empty"
    if len(messages) < 2:
        return "FAILED -> At least two messages are required for comparison"

    exception_headers = [h.lower() for h in (exception_headers or [])]

    def filtered_headers(message):
        return {
            (n.lower(), v)
            for n, v in get_list_of_all_header_fields_from_sip_message(message)
            if n.lower() not in exception_headers
        }

    try:
        reference = filtered_headers(messages[0])
        assert reference, "FAILED -> No header fields found in the first message"

        def _normalize(name: str, value: str) -> str:
            if name in _HOST_ONLY_HEADERS:
                return _extract_host(value) or value
            return _TAG_PARAM_PATTERN.sub("", value)

        reference_by_name: dict[str, list[str]] = {}
        for name, value in reference:
            reference_by_name.setdefault(name, []).append(value)
        for idx, msg in enumerate(messages[1:], start=2):
            current = filtered_headers(msg)
            mismatch_details = []
            for name, value in current:
                if name in reference_by_name and _normalize(name, value) not in [
                    _normalize(name, v) for v in reference_by_name[name]
                ]:
                    mismatch_details.append(
                        f"Header '{name.capitalize()}': \nExpected: {' | '.join(reference_by_name[name])}\n  Actual: {value}"
                    )
            assert (
                not mismatch_details
            ), "FAILED -> Header fields of message {} differ from message {}:\n{}".format(
                (
                    message_descriptions_list[idx - 1]
                    if message_descriptions_list
                    else idx
                ),
                message_descriptions_list[0] if message_descriptions_list else "1",
                "\n".join(mismatch_details),
            )
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
        request_line = output.sip.get("request_line", None)
        if request_line:
            splitted = request_line.split(" ")
        else:
            return "FAILED -> Cannot find 'urn:service:sos' in request URI"
        assert (
            splitted[1] == "urn:service:sos"
        ), "FAILED -> Cannot find 'urn:service:sos' in request URI"
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
        to_header = output.sip.get("to", None)

        first_part_of_to_header = (
            str(to_header).replace("\r", "").replace("\n", "").split(";")[0]
        )

        assert (
            first_part_of_to_header == "urn:service:sos"
        ), "FAILED -> Cannot find 'urn:service:sos' is in TO header field"
        return "PASSED"
    except AssertionError as e:
        return str(e)
