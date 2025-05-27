import base64
import os
import re

import jwt
import json
from pathlib import Path
from flatten_json import flatten
from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm, InvalidKey
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed448
from cryptography.hazmat.backends import default_backend
from typing import Optional
from datetime import datetime
from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN


def generate_jws(json_source: dict | str, cert_path: str, key_path: str,
                 key_password: str | None = None, output_file: str = None) -> str:
    """
    Generates JSON Web Signatures object:
    - with header section containing 'x5c' field
    - 'x5c' contains all certificates from chain given in cert_path file. It is added as a list of Base64 encoded certs
      in DER format
    - JSON payload is at first converted to Flat JSON serialization format
    - JWS object is signed with private key which should match first certificate in cert_path given chain
    - JWS is encrypted using EdDSA with Curve448 (Ed448)

    :param output_file:
    :param json_source: source of JSON payload. Can be a dict or str containing JSON,
    or str with full path to file containing JSON body
    :param cert_path: full path to Ed448 certificate chain file used for signing JWS. Certificate corresponding to private key
    should be first, then optionally subsequent certs used for signing can be added
    :param key_path: full path to Ed448 private key file for signing
    :param key_password: optional password for the key
    :return: signed JWS object
    """
    json_payload = None
    if isinstance(json_source, str):
        is_path = False
        try:
            is_path = Path(json_source).exists()
        except OSError:
            pass
        if is_path:
            try:
                with open(json_source, 'r') as json_file:
                    json_payload = json.load(json_file)
            except json.JSONDecodeError:
                print(f'Unable to load JSON from file: {json_source}')
                return ""
        else:
            try:
                json_payload = json.loads(json_source)
            except json.JSONDecodeError:
                print(f'Unable to load JSON from str: {json_source}')
                return ""
    elif isinstance(json_source, dict):
        json_payload = json_source

    # Load Ed448 private key
    with open(key_path, 'rb') as key_file:
        if key_password:
            key_password = key_password.encode('utf-8')
        private_key = serialization.load_pem_private_key(key_file.read(), password=key_password)
        if not isinstance(private_key, ed448.Ed448PrivateKey):
            raise UnsupportedAlgorithm(f'Private key "{key_path}" does not use ECDSA with Curve448 (EdDSA)')
    # Load all certificates from file
    certificates = []
    with open(cert_path, 'rb') as cert_file:
        cert_data = cert_file.read()
    for cert in cert_data.split(b'-----END CERTIFICATE-----'):
        cert = cert.strip()
        if cert:
            cert = cert + b'\n-----END CERTIFICATE-----'
            cert_loaded = load_pem_x509_certificate(cert, default_backend())
            if cert_loaded.signature_algorithm_oid != x509.SignatureAlgorithmOID.ED448:
                raise UnsupportedAlgorithm(f'Certificate "{cert_path}" does not use ECDSA with Curve448 (EdDSA)')
            certificates.append(cert_loaded)
    # Verify first cert matching private key
    if private_key.public_key() != certificates[0].public_key():
        raise InvalidKey(
            f'Private key "{key_path}" does not match following certificate from file "{cert_path}":'
            f' \n{certificates[0]}'
        )
    # Generate list of encoded certs for x5c header field
    x5c = []
    for cert in certificates:
        cert_der = cert.public_bytes(serialization.Encoding.DER)
        cert_base64 = base64.b64encode(cert_der).decode('utf-8')
        x5c.append(cert_base64)

    header = {
        "alg": "EdDSA",
        "typ": "JWT",
        "x5c": x5c
    }

    result = jwt.encode(flatten(json_payload), private_key, algorithm='EdDSA', headers=header)

    if output_file is not None:
        try:
            full_path = os.path.join(output_file)

            # Write content to file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(result)

            print(f"✅ Saved to: {full_path}")
        except Exception as e:
            pass

    return result


def decrypt_jws(jws_source: str, key_path: str, key_password: str | None = None) -> list:
    """
    Decrypts given JSON Web Signature object encrypted as Base64URL using key and returns list of dict with
    headers and another with JSON payload
    :param jws_source: source of JWS object encrypted as Base64URL. Can be given as str or str with full path to file
    :param key_path: full path to private key for decryption
    :param key_password: password for the key
    :return: [dict with JWS headers JSON, dict with decrypted JSON payload]
    """
    is_path = False
    try:
        is_path = Path(jws_source).exists()
    except OSError:
        pass
    if is_path:
        try:
            with open(jws_source, 'r') as jws_file:
                jws_object = jws_file.read()
        except PermissionError:
            print(f'Unable to read JWS from file: {jws_source}')
            return []
    else:
        jws_object = jws_source

    with open(key_path, 'rb') as key_file:
        key_data = key_file.read()

    # Try if given key is private and extract public
    try:
        private_key = serialization.load_pem_private_key(
            key_data,
            password=key_password,
            backend=default_backend()
        )
        public_key = private_key.public_key()
    except Exception as e:
        # On any error handle key as public
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    decoded_payload = None
    try:
        decoded_payload = jwt.decode(jws_object, public_key, algorithms=["EdDSA"])
    except jwt.ExpiredSignatureError:
        print("The signature has expired.")
    except jwt.InvalidTokenError:
        print("Invalid JWS object.")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []
    return [jwt.get_unverified_header(jws_object), decoded_payload]


def get_payload_data_from_file(file_path: str,
                               file_type: str = '',
                               key_path: Optional[str] = '',
                               cert_path: Optional[str] = '') -> str:
    """
    Reads and extracts payload data from a file based on the specified type.

    :param file_path : Path to the file containing the payload data.
    :param file_type : The format of the payload. Can be 'HTTP', 'JSON', or 'PLAIN'. Defaults to an empty string.
    :param key_path : Key used for signing (only applicable for JSON type). Defaults to an empty string.
    :param cert_path : Certificate used for signing (only applicable for JSON type). Defaults to an empty string.
    :return: Extracted payload data.
    raise: ValueError If an invalid type is provided.
    """
    with open(file_path, 'r', encoding='utf-8') as input_file:
        content = input_file.read().strip()  # Strip to remove trailing newlines

        if file_type.upper() == 'HTTP':
            parts = content.split('\n\n', maxsplit=1)
            if len(parts) > 1:
                return parts[1]  # Extract payload after headers
            return ""

        elif file_type.upper() == 'JSON':
            try:
                json_data = json.loads(content)
                flattened_data = flatten(json_data)  # Assuming `flatten` is defined elsewhere
                return generate_jws(flattened_data, cert_path, key_path)  # Assuming `generate_jws` is defined
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")

        elif file_type.lower() == 'plain':
            return content

        else:
            raise ValueError("Invalid format. Supported formats: 'HTTP', 'JSON', 'PLAIN'.")


def is_jws_string(jws_string: str) -> bool:
    """
    Validates correct format of JWS sting

    :param jws_string: String representation of JWS
    :return: Bool result of check
    """
    try:
        header, payload, signature = jws_string.split('.')
        decoded_header = json.loads(base64.urlsafe_b64decode(header + '==='))

        return all(('alg' in decoded_header.keys(),
                    decoded_header['alg'] == 'EdDSA',
                    'typ' in decoded_header.keys(),
                    decoded_header['typ'] == 'JWT',
                    len(payload) > 0
                    ))
    except ValueError or TypeError:
        return False


def is_valid_rtsp_url(url: str) -> bool:
    """
    Validate the format of an RTSP URL.

    :param url: RTSP URL to validate
    :return: True if the URL is valid, False otherwise
    """
    rtsp_pattern = re.compile(
        r'^rtsp://'
        r'(([^:@]+:[^:@]+)@)?'  # Optional username:password@
        r'([a-zA-Z0-9.-]+)'  # Host (IP or domain)
        r'(:\d+)?'  # Optional port
        r'(/.*)?$'  # Optional path
    )

    return bool(rtsp_pattern.match(url))


def is_valid_iso_datetime(date_string) -> bool:
    """

    Validates datetime iso format.

    :param date_string: String to validate datetime
    :return: True or False
    """
    try:
        datetime.fromisoformat(date_string)
        return True
    except ValueError:
        return False


def validate_log_event_id(log_eventid, log_event_name):
    """

    Validates common logic of logger messages.

    :param log_eventid: String with unique identifier
    :param log_event_name: String with that identifies name of event
    :return: "FAILED" or "PASSED" result of testing
    """
    if (result := is_type(log_eventid, log_event_name, str)) != 'PASSED':
        # Test step result FAILED in case of invalid format
        return result

    if f'urn:emergency:uid:{log_event_name.lower()}:' not in log_eventid:
        return f"FAILED-> Missing 'urn:emergency:uid:{log_event_name}:' in '{log_event_name}'"

    match = re.search(rf"{re.escape(log_event_name.lower())}:([^:]+):", log_eventid)
    logid_string = match.group(1)
    if not (10 <= len(set(logid_string)) <= 36):
        return f"FAILED-> '{log_event_name}' doesn't contain unique string 10 to 36 characters long"

    fqdn = log_eventid.split(f'{logid_string}:')[1]
    if not re.search(FQDN_PATTERN, fqdn):
        return f"FAILED-> '{log_event_name}' doesn't contain FQDN of Logging Service"
    return "PASSED"
