from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
)
from tests.BCF_009.constants import SUPPORTED_STR, REPLACE_STR, SIP_ATTR_STR


def validate_extra_header(stimulus_message, output_message) -> str:
    """
    Validation the 'Supported: replaces' or 'replaces' header and value were added during forwarding through BCF.
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

        sip_out = getattr(output_message, SIP_ATTR_STR, None)
        if not sip_out:
            return f"FAILED -> Output messages from BCF doesn't contain the {SIP_ATTR_STR} attribute."

        supported = getattr(sip_out, SUPPORTED_STR, None)
        if not supported:
            return f"FAILED -> '{SUPPORTED_STR}' field was not found."

        supported_values = [value.strip() for value in supported.split(",")]

        if REPLACE_STR not in supported_values:
            return f"FAILED -> {SUPPORTED_STR}' field doesn't contain the '{REPLACE_STR}' value. Found: '{supported_values}'"

        return "PASSED"
    except AssertionError as e:
        return str(e)
