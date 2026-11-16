from checks.jws.checks import (
    validate_jws_payload_serialization_format,
)
from services.aux_services.json_services import is_x5t_s256


def validate_jws_protection_and_format(
    test_data,
) -> str:
    """
    Validates that the CHFE-to-Logger JWS payload uses the correct
    flattened serialization format and, when applicable, verifies the
    x5t#256 thumbprint against the leaf certificate.

    Delegates the actual validation to
    validate_jws_payload_serialization_format(), automatically enabling
    the x5t#256 check only when the payload's protected header
    actually declares an x5t#256 parameter (via is_x5t_s256()) - if the
    header omits it, the check is skipped rather than failed.

    Args:
        test_data: TestData instance holding the CHFE-to-Logger JWS
            body (chfe_logger_body, chfe_logger_body_dict) and the
            certificate/key paths (cert_filepath, key_filepath) needed
            for signature and x5t#256 verification.

    Returns:
        str: "PASSED" if the format (and, if applicable, x5t#256)
        validation succeeds, otherwise a "FAILED -> ..." message
        describing the first validation error encountered.
    """
    try:
        jws_validation = validate_jws_payload_serialization_format(
            test_data.chfe_logger_body,
            test_data.chfe_logger_body_dict,
            test_data.cert_filepath,
            test_data.key_filepath,
            check_x5t=is_x5t_s256(test_data.chfe_logger_body_dict),
        )
        assert jws_validation == "PASSED", jws_validation

        return "PASSED"
    except AssertionError as e:
        return str(e)
