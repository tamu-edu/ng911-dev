import base64
import binascii
import json
from typing import Any

from checks.jws.checks import (
    is_valid_algorithm,
    validate_jws_payload_serialization_format,
)
from services.aux_services.json_services import is_unsigned_jws


def get_raw_http_body(message) -> str | None:
    """Extract the raw (undecoded JSON) HTTP body of a packet as a string.

    :param message: Parsed HTTP packet.
    :return: Body string, or None if the packet has no body.
    """
    try:
        hex_body = str(message.http.file_data).replace(":", "")
        return bytes.fromhex(hex_body).decode("utf-8", errors="ignore")
    except (AttributeError, ValueError):
        return None


def _decode_protected_header(raw_body: str) -> tuple[str | None, str | None]:
    """Return (raw protected header string, error) for a flattened JWS body."""
    try:
        protected_b64 = json.loads(raw_body)["protected"]
        padding = "=" * (-len(protected_b64) % 4)
        return base64.urlsafe_b64decode(protected_b64 + padding).decode("utf-8"), None
    except (TypeError, KeyError, ValueError, binascii.Error) as e:
        return None, f"FAILED -> Cannot decode JWS Protected Header: {e}"


def check_protected_header_alg_present_once(raw_body: str) -> str:
    """Verify the raw decoded Protected Header contains the "alg" key exactly once
    (guards against duplicate key injection like {"alg":"none","alg":"EdDSA"}).

    :param raw_body: Raw HTTP body of the LogEvents POST request.
    :return: "PASSED" or a failure message.
    """
    header, error = _decode_protected_header(raw_body)
    if error:
        return error
    occurrences = header.count('"alg"')
    if occurrences != 1:
        return f"FAILED -> Expected exactly one 'alg' in Protected Header. Actual: {occurrences}. Header: {header}"
    return "PASSED"


def _check_alg_matches_signing_state(raw_body: str) -> str:
    """'alg' must be 'none' with an empty signature, or 'EdDSA' with a signature."""
    header, error = _decode_protected_header(raw_body)
    if error:
        return error
    try:
        alg = json.loads(header).get("alg")
    except (ValueError, AttributeError) as e:
        return f"FAILED -> Protected Header is not a valid JSON object: {e}"
    if not is_valid_algorithm(raw_body):
        state = (
            "unsigned (empty signature)"
            if is_unsigned_jws(raw_body)
            else "signed (non-empty signature)"
        )
        expected = "none" if is_unsigned_jws(raw_body) else "EdDSA"
        return f"FAILED -> JWS is {state}: expected 'alg':'{expected}', got '{alg}'"
    return "PASSED"


def validate_jws_format(
    raw_body: str, jws_data: Any, cert_filepath: str, key_filepath: str
) -> str:
    """Validate the LogEvents POST body as a flattened JWS (structure, alg, signature,
    certificate chain via x5c or x5u + x5t#256, payload).

    :param raw_body: Raw HTTP body of the LogEvents POST request.
    :param jws_data: Parsed JSON body.
    :param cert_filepath: Path to BRIDGE certificate file from lab config.
    :param key_filepath: Path to BRIDGE private key file from lab config.
    :return: "PASSED" or a failure message.
    """
    if not raw_body:
        return "FAILED -> No LogEvents POST body found."
    alg_result = _check_alg_matches_signing_state(raw_body)
    if alg_result != "PASSED":
        return alg_result
    if not is_unsigned_jws(raw_body) and (not cert_filepath or not key_filepath):
        return (
            "NOT RUN -> BRIDGE certificate/key not found in the lab config "
            "for the LOGGER-facing entity"
        )
    return validate_jws_payload_serialization_format(
        raw_body, jws_data, cert_filepath, key_filepath, check_x5t=True
    )


def get_first_sip_response(messages, cseq_method: str):
    """Return the first final (non-1xx) SIP response to a request of the given CSeq method.

    :param messages: SIP messages (responder -> requester direction).
    :param cseq_method: CSeq method of the request being answered, e.g. "SUBSCRIBE".
    :return: Response message, or None if no such response was found.
    """
    for message in messages or []:
        sip = getattr(message, "sip", None)
        if (
            sip is not None
            and hasattr(sip, "status_code")
            and getattr(sip, "cseq_method", None) == cseq_method
            and not str(sip.status_code).startswith("1")
        ):
            return message
    return None
