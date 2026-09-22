import base64
import binascii
import hashlib
import json
import re
from datetime import datetime, timezone

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed448

from checks.http.checks import is_valid_url
from services.aux_services.json_services import (
    get_json,
    decode_base64url,
    is_unsigned_jws,
)


def is_compact_jws(value: str) -> bool:
    """
    Check whether a string is a valid Compact JWS.

    Args:
        value: JWS string in compact serialization format.

    Returns:
        True if format is valid Compact JWS, otherwise False.
    """
    if not isinstance(value, str):
        return False

    parts = value.split(".")
    if len(parts) != 3:
        return False

    return True


def is_general_jws(value: dict) -> bool:
    """
    Check whether a value is a valid General JWS JSON Serialization object.

    Args:
        value: Input object to validate (expected dict).

    Returns:
        True if structure matches General JWS format, otherwise False.
    """

    if not isinstance(value, dict):
        return False

    if set(value.keys()) != {"payload", "signatures"}:
        return False

    if not isinstance(value["payload"], str):
        return False

    if not isinstance(value["signatures"], list) or len(value["signatures"]) < 1:
        return False

    for sig in value["signatures"]:
        if not isinstance(sig, dict):
            return False
        if "signature" not in sig or not isinstance(sig["signature"], str):
            return False
        if "protected" in sig and not isinstance(sig["protected"], str):
            return False

    return True


def verify_signed_jws_fully_with_cert_files(
    jws_string: str,
    trusted_cert_path: str,
    private_key_path: str,
    check_if_expired: bool = False,
    check_x5t: bool = False,
) -> str:
    """Validates a JWS token string by running multiple independent layers of trust.

    This function accepts either a JWS JSON Serialization string and verifies
    its integrity, key ownership, and certificate
    traceability. Specifically, the method executes the following checklist:

    1. Serialization Format Detection
    2. Header Extraction & Base64url Validation
    3. Algorithm Strictness Check
    4. Token Cryptographic Integrity Check
    5. Private Key Ownership Verification
    6. Internal Chain Cohesion Check
    7. Local Anchor Trust Verification

    Args:
        jws_string (str): The raw JWS string (JSON string).
        trusted_cert_path (str): Path to the PEM file containing the trusted root/chain.
        private_key_path (str): Path to the PEM file containing the private key.
        check_if_expired (bool): Check if cert has expired. Defaults to False.
        check_x5t (bool): Check if x5t field contains correct leaf cert. Defaults to False.

    Returns:
        str: PASSED only if ALL validation layers pass cleanly; FAILED if any layer fails.
    """
    protected_b64, payload_b64, signature_b64 = (None,) * 3

    try:
        jws_string = jws_string.strip()

        # 1. Serialization Format Detection
        if jws_string.startswith("{"):
            try:
                jws_json = json.loads(jws_string)
                protected_b64 = jws_json["protected"]
                payload_b64 = jws_json["payload"]
                signature_b64 = jws_json["signature"]

                if not isinstance(protected_b64, str):
                    return "FAILED -> 'protected' must be a string value"
                if not isinstance(payload_b64, str):
                    return "FAILED -> 'payload' must be a string value"
                if not isinstance(signature_b64, str):
                    return "FAILED -> 'signature' must be a string value"

            except KeyError as e:
                return f"FAILED -> Missing required JWS JSON key: {e}"
        else:
            return "FAILED -> Unsupported JWS format. Only Flattened JSON Serialization is accepted."

        if protected_b64 is None:
            return "FAILED -> 'protected' field is missing or could not be extracted"
        if payload_b64 is None:
            return "FAILED -> 'payload' field is missing or could not be extracted"
        if signature_b64 is None:
            return "FAILED -> 'signature' field is missing or could not be extracted"

        # 2. Header Extraction & Base64url Validation
        header_padding = "=" * (-len(protected_b64) % 4)
        try:
            header_json = json.loads(
                base64.urlsafe_b64decode(protected_b64 + header_padding).decode("utf-8")
            )
            if not isinstance(header_json, dict):
                return "FAILED -> Protected header must be a JSON object"
        except Exception as e:
            return f"FAILED -> Corrupt Protected Header Base64 structure: {e}"

        # Parse JWS Certificate Chain — x5c or x5u
        jws_certs = []

        if "x5u" in header_json and "x5c" in header_json:
            return "FAILED -> 'x5u' and 'x5c' must not be present simultaneously"

        if "x5u" in header_json and "x5c" not in header_json:
            # If x5u let's check if URL string contains correct format, then use cert from local 'trusted_cert_path' file
            x5u_value = header_json["x5u"]
            if not isinstance(x5u_value, str):
                return "FAILED -> 'x5u' must be a string value"
            if not is_valid_url(x5u_value, check_ip_as_host=True):
                return f"FAILED -> 'x5u' contains an invalid URL: '{x5u_value}'"

            print(
                "⚠️ JWS uses an x5u link to the certificate. For security purposes, the certificate provided in the 'certificate_file' lab config option will be used for the tested entity. ⚠️"
            )

            if trusted_cert_path is None or trusted_cert_path == "":
                return "INCONCLUSIVE -> 'x5u' is present in header but 'certificate_file' path was not provided."

            try:
                with open(trusted_cert_path, "r", encoding="utf-8") as rc_file:
                    remote_cert_data = rc_file.read()
                pem_blocks = re.findall(
                    r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
                    remote_cert_data,
                    re.DOTALL,
                )
                if not pem_blocks:
                    return f"FAILED -> No valid certificates found in remote_cert file: {trusted_cert_path}"
                for block in pem_blocks:
                    jws_certs.append(
                        x509.load_pem_x509_certificate(block.encode("utf-8"))
                    )
            except Exception as e:
                return f"INCONCLUSIVE -> Failed to load certificate file from lab_config 'certificate_file' path '{trusted_cert_path}': {e}"

            if check_x5t:
                # x5t#256 must be present alongside x5u
                if "x5t#256" not in header_json:
                    return "FAILED -> 'x5u' must be used together with 'x5t#256'"
                if not is_valid_x5t_s256(header_json["x5t#256"]):
                    return f"FAILED -> 'x5t#256' has invalid format or empty. Actual: '{header_json["x5t#256"]}'"

                # Verify x5t#256 matches the leaf certificate
                leaf_cert = find_leaf_cert(jws_certs)
                leaf_der = leaf_cert.public_bytes(serialization.Encoding.DER)
                expected_thumbprint = (
                    base64.urlsafe_b64encode(hashlib.sha256(leaf_der).digest())
                    .rstrip(b"=")
                    .decode()
                )

                if header_json["x5t#256"] != expected_thumbprint:
                    return "FAILED -> 'x5t#256' does not match the thumbprint of the leaf certificate"

        elif "x5c" in header_json:
            x5c_list = header_json["x5c"]
            if not isinstance(x5c_list, list):
                return "FAILED -> 'x5c' must be an array"
            if not x5c_list:
                return "FAILED -> 'x5c' array is empty"
            for idx, cert_b64 in enumerate(x5c_list):
                p = "=" * (-len(cert_b64) % 4)
                try:
                    jws_certs.append(
                        x509.load_der_x509_certificate(base64.b64decode(cert_b64 + p))
                    )
                except Exception as e:
                    return f"FAILED -> Structural ASN.1 corruption inside x5c at index {idx}: {e}"

        else:
            return "FAILED -> Missing certificate source: neither 'x5c' nor 'x5u' found in JWS Protected Header"

        if check_if_expired:
            now = datetime.now(timezone.utc)
            for i, cert in enumerate(jws_certs):
                if cert.not_valid_before_utc > now:
                    return f"FAILED -> Certificate[{i}] is not yet valid (valid from {cert.not_valid_before_utc})"
                if cert.not_valid_after_utc < now:
                    return f"FAILED -> Certificate[{i}] has expired (expired at {cert.not_valid_after_utc})"

        # Normalize chain order to leaf → intermediate → root
        jws_certs = sort_cert_chain(jws_certs)

        jws_leaf_cert = jws_certs[0]
        jws_leaf_pubkey = jws_leaf_cert.public_key()

        # 3. Algorithm Strictness Check (EdDSA + Curve448 exclusively)
        if "alg" not in header_json:
            return "FAILED -> Missing 'alg' field in protected header"
        if not isinstance(header_json["alg"], str):
            return "FAILED -> 'alg' must be a string value"
        if header_json["alg"] != "EdDSA":
            return f"FAILED -> Strict rule violation. Expected 'alg':'EdDSA', got '{header_json['alg']}'"

        if not isinstance(jws_leaf_pubkey, ed448.Ed448PublicKey):
            return f"FAILED -> Certificate algorithm mismatch. Expected Curve448 (Ed448PublicKey), got {type(jws_leaf_pubkey).__name__}"

        # 4. JWS Signature Verification
        signing_input = f"{protected_b64}.{payload_b64}".encode("utf-8")
        sig_padding = "=" * (-len(signature_b64) % 4)
        signature_bytes = base64.urlsafe_b64decode(signature_b64 + sig_padding)

        try:
            jws_leaf_pubkey.verify(signature_bytes, signing_input)
        except InvalidSignature:
            return "FAILED -> JWS Signature mismatch. The payload or header data was tampered with."
        except Exception as e:
            return f"FAILED -> Cryptographic error verifying JWS signature: {e}"

        # 5. Private Key Ownership Verification
        try:
            with open(private_key_path, "rb") as key_file:
                local_private_key = serialization.load_pem_private_key(
                    key_file.read(), password=None
                )
            local_derived_pubkey = local_private_key.public_key()

            jws_pub_bytes = jws_leaf_pubkey.public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            local_pub_bytes = local_derived_pubkey.public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            if jws_pub_bytes != local_pub_bytes:
                return "FAILED -> Private key mismatch. The token's certificate does not match local private key."
        except Exception as e:
            return f"FAILED -> Local private key configuration error: {e}"

        # 6. Internal Chain Cohesion Check (Child signed by parent)
        jws_certs = sort_cert_chain(jws_certs)
        if len(jws_certs) == 1:
            # Single self-signed certificate
            root = jws_certs[0]
            root_pubkey = root.public_key()
            if not isinstance(root_pubkey, ed448.Ed448PublicKey):
                return "FAILED -> Single certificate must use Ed448 key"
            try:
                root_pubkey.verify(root.signature, root.tbs_certificate_bytes)
            except InvalidSignature:
                return "FAILED -> Single certificate self-signature verification failed"
        else:
            # Certificate chain
            for i in range(len(jws_certs) - 1):
                child = jws_certs[i]
                parent = jws_certs[i + 1]

                if child.issuer != parent.subject:
                    return f"FAILED -> Issuer/Subject mismatch: x5c[{i}].issuer != x5c[{i + 1}].subject"

                try:
                    basic = parent.extensions.get_extension_for_class(
                        x509.BasicConstraints
                    )
                    if not basic.value.ca:
                        return f"FAILED -> x5c[{i + 1}] is not a CA certificate"
                except x509.ExtensionNotFound:
                    return f"FAILED -> x5c[{i + 1}] missing BasicConstraints extension"

                parent_pubkey = parent.public_key()
                if not isinstance(parent_pubkey, ed448.Ed448PublicKey):
                    return f"FAILED -> x5c[{i + 1}] must use Ed448 key"
                try:
                    parent_pubkey.verify(child.signature, child.tbs_certificate_bytes)
                except InvalidSignature:
                    return f"FAILED -> Chain link broken: x5c[{i}] was tampered with or not signed by x5c[{i + 1}]."

            root = jws_certs[-1]
            root_pubkey = root.public_key()
            if not isinstance(root_pubkey, ed448.Ed448PublicKey):
                return "FAILED -> Root certificate must use Ed448 key"
            try:
                root_pubkey.verify(root.signature, root.tbs_certificate_bytes)
            except InvalidSignature:
                return "FAILED -> Root certificate self-signature verification failed"

        # 7. Local Anchor Trust Verification
        try:
            with open(trusted_cert_path, "r", encoding="utf-8") as cert_file:
                local_cert_data = cert_file.read()
            local_pem_blocks = re.findall(
                r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
                local_cert_data,
                re.DOTALL,
            )
            if not local_pem_blocks:
                return f"FAILED -> Local anchor file {trusted_cert_path} contains no valid certificates."
            local_certs = [
                x509.load_pem_x509_certificate(block.encode("utf-8"))
                for block in local_pem_blocks
            ]
            local_certs = sort_cert_chain(local_certs)
        except Exception as e:
            return f"FAILED -> Failed to parse local trusted anchor storage files: {e}"

        top_jws_cert = jws_certs[-1]

        # Check explicit matching
        for anchor_cert in local_certs:
            if top_jws_cert == anchor_cert:
                return "PASSED"

        # Check for mismatching by cert fields
        for anchor_cert in local_certs:
            try:
                top_pub = top_jws_cert.public_key().public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                anc_pub = anchor_cert.public_key().public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )

                if top_pub == anc_pub:
                    reasons = []

                    if (
                        top_jws_cert.not_valid_after_utc
                        != anchor_cert.not_valid_after_utc
                    ):
                        reasons.append(
                            f"Expiration date changed (JWS: {top_jws_cert.not_valid_after_utc} vs Local: {anchor_cert.not_valid_after_utc})"
                        )
                    if top_jws_cert.subject != anchor_cert.subject:
                        reasons.append("Subject field data modified")
                    if top_jws_cert.serial_number != anchor_cert.serial_number:
                        reasons.append("Serial number altered")

                    details = (
                        ", ".join(reasons)
                        if reasons
                        else "Metadata structural changes detected"
                    )
                    return f"FAILED -> Certificate tampering detected: {details}."

                anchor_pubkey = anchor_cert.public_key()
                if not isinstance(anchor_pubkey, ed448.Ed448PublicKey):
                    continue
                try:
                    anchor_pubkey.verify(
                        top_jws_cert.signature, top_jws_cert.tbs_certificate_bytes
                    )
                    return "PASSED"
                except InvalidSignature:
                    return f"FAILED -> Cryptographic signature failure. The certificate claims authority from '{anchor_cert.subject.rfc4514_string()}' but verification failed."

            except Exception:
                continue

        return "FAILED -> The token certificate tree is completely unrecognized by your local anchors."

    except Exception as e:
        return f"FAILED -> Unhandled runtime failure: {e}"


def verify_unsigned_jws(jws_string: str) -> str:
    """Validates an unsigned JWS token string.

    1. Serialization Format Detection:
    2. Unsigned Header Verification:
    3. Payload Presence Verification:
    4. Signature Absence Verification:

    Args:
        jws_string (str): The raw JWS or JSON string.

    Returns:
        str: "PASSED" if all rules match, or "FAILED with error"
    """

    try:
        jws_string = jws_string.strip()

        # 1. Serialization Format Detection
        if not jws_string.startswith("{"):
            return "FAILED -> Unsupported JWS format. Only Flattened JSON Serialization is accepted."

        try:
            jws_json = json.loads(jws_string)
            protected_b64 = jws_json["protected"]
            payload_b64 = jws_json["payload"]
            signature_b64 = jws_json["signature"]
        except KeyError as e:
            return f"FAILED -> Missing required JWS JSON key: {e}"
        except json.JSONDecodeError as e:
            return f"FAILED -> Invalid JSON string syntax: {e}"

        # 2. Header Extraction & Validation
        header_padding = "=" * (-len(protected_b64) % 4)
        try:
            header_json = json.loads(
                base64.urlsafe_b64decode(protected_b64 + header_padding).decode("utf-8")
            )
        except Exception as e:
            return f"FAILED -> Corrupt Protected Header Base64 structure: {e}"

        if header_json.get("alg") != "none":
            return f"FAILED -> Unsigned JWS rule violation. Expected 'alg':'none', got '{header_json.get('alg')}'"

        if "x5c" in header_json:
            return "FAILED -> Security violation. Unsigned JWS must not contain an 'x5c' certificate parameter."

        # 3. Payload Presence Verification
        if not payload_b64 or payload_b64.strip() == "":
            return "FAILED -> Structural violation. The unsigned JWS payload segment is missing or completely empty."

        if len(payload_b64) < 3:
            return f"FAILED -> Structural violation. Unsigned Payload string length ({len(payload_b64)}) is too short to be a valid JSON."

        # 4. Signature Absence Verification
        if signature_b64 != "":
            return "FAILED -> Security violation. JWS claims 'alg':'none' but contains a non-empty signature block."

        return "PASSED"

    except Exception as general_error:
        return f"FAILED -> Unhandled runtime failure during parsing: {general_error}"


def validate_jws_payload_serialization_format(
    content_body, json_body, cert_filepath, key_filepath, check_x5t=False
):
    """
    Validates a JWS flattened serialization format.

    Ensures the payload is neither compact nor general JWS format, has the
    correct flattened JSON structure, passes signature verification (signed or
    unsigned), and contains accessible payload data.

    Args:
        content_body (str): Raw HTTP request body used for JWS format detection
            and signature verification.
        json_body (dict): Parsed JSON from the request body. Must contain exactly
            the keys ``protected``, ``payload``, and ``signature``.
        cert_filepath (str): Path to the certificate file used for verifying a
            signed JWS. Ignored for unsigned JWS.
        key_filepath (str): Path to the private key file used for verifying a
            signed JWS. Ignored for unsigned JWS.
        check_x5t (bool): Check if x5t field contains correct leaf cert. Defaults to False.

    Returns:
        str: ``"PASSED"`` if all validations succeed, or a ``"FAILED -> ..."``
        message describing the first validation error encountered.

    """

    jws_fields = {
        "protected",
        "payload",
        "signature",
    }

    try:

        # Check if not compact format
        assert not is_compact_jws(content_body), "FAILED -> Compact JWS format found."

        # Check if not general format
        assert not is_general_jws(json_body), "FAILED -> General JWS format found."

        assert isinstance(
            json_body, dict
        ), "FAILED -> No correct JSON structure was found in HTTP post body."

        # Check structure and trust layers
        json_body_fields = set(json_body.keys())
        assert (
            json_body_fields == jws_fields
        ), f"FAILED -> The JSON fields do not match the JWS. Actual: {json_body_fields}, Expected: {jws_fields}."

        if is_unsigned_jws(content_body):
            validation_unsigned_jws = verify_unsigned_jws(content_body)
            assert validation_unsigned_jws == "PASSED", validation_unsigned_jws

        else:
            validation_with_certs = verify_signed_jws_fully_with_cert_files(
                content_body, cert_filepath, key_filepath, check_x5t=check_x5t
            )
            assert validation_with_certs == "PASSED", validation_with_certs

        assert is_payload_data_accessible(
            json_body
        ), "FAILED -> Payload data for JWS is not accessible or missed content."

        return "PASSED"
    except AssertionError as e:
        return str(e)


def is_payload_data_accessible(json_payload) -> bool:
    """
    Validates that the JWS payload is a dict and contains at least 'logEventType' field and returns True.
    Otherwise, it returns False.
    """
    payload = get_json(decode_base64url(json_payload.get("payload")))
    if payload and isinstance(payload, dict) and payload.get("logEventType"):
        return True

    return False


def is_valid_algorithm(jws: str) -> bool:
    """
    Validates the algorithm in the JWS protected header.
    For unsigned JWS, 'alg' must be 'none'.
    For signed JWS, 'alg' must be 'EdDSA'.
    Returns False if the protected header is missing or the algorithm is invalid.
    """
    jws_dict = json.loads(jws)

    protected = jws_dict.get("protected")
    if not protected:
        return False

    try:
        padding = "=" * (-len(protected) % 4)
        header = json.loads(base64.urlsafe_b64decode(protected + padding))
    except (ValueError, binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
        return False

    if is_unsigned_jws(jws):
        return header.get("alg") == "none"
    else:
        return header.get("alg") == "EdDSA"


def is_valid_x5t_s256(x5t: str) -> bool:
    """
    Validates that x5t#256 is a base64url-encoded SHA-256 hash.
    SHA-256 is always 32 bytes, which encodes to exactly 43 base64url characters.
    """
    if not isinstance(x5t, str):
        return False
    if len(x5t) != 43:
        return False
    try:
        decoded = base64.urlsafe_b64decode(x5t + "=")
        return len(decoded) == 32
    except (ValueError, binascii.Error) as e:
        print("Invalid x5t#256:", e)
        return False


def find_leaf_cert(certs: list) -> x509.Certificate:
    for cert in certs:
        try:
            bc = cert.extensions.get_extension_for_class(x509.BasicConstraints)
            if not bc.value.ca:
                return cert
        except x509.ExtensionNotFound:
            return cert
    return certs[0]


def sort_cert_chain(certs: list) -> list:
    """
    Sorts certificates into leaf → intermediate → root order
    regardless of their original order in the chain.
    """
    by_subject = {cert.subject: cert for cert in certs}

    leaf = None
    for cert in certs:
        if cert.issuer not in by_subject or cert.issuer == cert.subject:
            if cert.issuer != cert.subject:
                leaf = cert
                break

    if leaf is None:
        return certs

    sorted_chain = []
    current = leaf
    visited = set()
    while True:
        if id(current) in visited:
            break
        visited.add(id(current))
        sorted_chain.append(current)
        if current.issuer == current.subject:
            break
        parent = by_subject.get(current.issuer)
        if parent is None:
            break
        current = parent

    return sorted_chain
