from services.aux_services.sip_msg_body_services import (
    extract_all_contents_from_message_body,
)


def validate_mime_integrity(stimulus_message, output_message) -> str:
    """
    Validate that complex multipart MIME structure is preserved
    :param stimulus_message: Messages from OSP to BCF
    :param output_message: Messages from BCF to ESRP
    :return: "PASSED" if validation passes, error message otherwise
    """
    try:
        assert stimulus_message, "NOT RUN -> No stimulus messages from OSP to BCF found"
        assert output_message, "FAILED -> No output messages from BCF to ESRP found"

        stimulus_body = extract_all_contents_from_message_body(stimulus_message)
        output_body = extract_all_contents_from_message_body(output_message)
        assert stimulus_body == output_body, "FAILED -> MIME structures doesn't match"

        return "PASSED"
    except AssertionError as e:
        return str(e)
