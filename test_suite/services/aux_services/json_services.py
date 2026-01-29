import base64
import os
import re
import urllib.request
import urllib.error

import jwt
import json
from pathlib import Path
from flatten_json import flatten
from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm, InvalidKey, InvalidSignature
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed448
from cryptography.hazmat.backends import default_backend
from typing import Optional, List
from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from charset_normalizer import from_bytes
from datetime import datetime, timezone

def generate_jws(json_source, cert_path: str | None = None, key_path: str | None = None,
                 key_password: str | None = None, output_file: str = None, cert_url: str = None,
                 disable_cert_url_checks = False) -> str:
    """
    Generates JSON Web Signatures object:
    - signed using EdDSA with Curve448 (Ed448) algorithm (if cert_path and key_path provided)
        - with header section containing 'x5c' or 'x5u' field
        - 'x5u' contains URL to certificate chain reference. Field added only if 'cert_url' is provided with valid
        reference to certificate chain from 'cert_path'. This param disables adding 'x5c'
        - 'x5c' contains all certificates from chain given in cert_path file. It is added as a list of Base64 encoded
        certs in DER format
        - JWS object is signed with private key which should match first certificate in cert_path given chain
    - unsigned with 'alg': 'none' in header (if cert_path and key_path not provided)
    - JSON payload is at first converted to Flat JSON serialization format

    :param json_source: source of JSON payload. Can be a dict or str containing JSON,
    or str with full path to file containing JSON body
    :param cert_path: optional full path to Ed448 certificate chain file used for signing JWS.
    Certificate corresponding to private key should be first, then optionally subsequent certs used
    for signing can be added
    :param key_path: optional full path to Ed448 private key file for signing
    :param key_password: optional password for the key
    :param output_file: if provided, then signed JWS object string will be saved to the file
    :param cert_url: if provided then 'x5u' param is added to header section with URL to certificate reference
    :param disable_cert_url_checks: if set to False, then method will skip cert_url dereferencing and certificate verification
    :return: signed JWS object (if output_file not provided)
    """
    def save_file(out_file: str, content: str):
        try:
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=4)
            print(f"✅ Saved to: {out_file}")
        except Exception as e:
            print(f"❌ Error occured while saving to file: {out_file}. Error: {e}")
    def read_file(path: str):
        try:
            with open(path, 'rb') as f:
                return f.read()
        except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError, TypeError):
            return b''

    json_payload = get_json(json_source)
    if not json_payload:
        print(f"❌ Error while loading json from given source {str(json_source)}. Returning None")
        if output_file:
            save_file(output_file, "")
        return ""
    header = {}

    if cert_path and key_path:
        header["alg"] = "EdDSA"
        key_file_content = read_file(key_path)
        cert_data = read_file(cert_path)

        if key_file_content == b'' or cert_data == b'':
            print(f"❌ Error while loading {cert_path} and/or {key_path}. Returning None")
            if output_file:
                save_file(output_file, "")
            return ""

        if key_password:
            key_password = key_password.encode('utf-8')
        private_key = serialization.load_pem_private_key(key_file_content, password=key_password)
        if not isinstance(private_key, ed448.Ed448PrivateKey):
            raise UnsupportedAlgorithm(f'Private key "{key_path}" does not use ECDSA with Curve448 (EdDSA)')
        # Load all certificates from file
        certificates = []

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

        # If cert_url is provided then verify and add as x5u header field
        if cert_url:
            if "https://" not in cert_url and not disable_cert_url_checks:
                print("Error while generating JWS - provided cert_url does not use TLS! Returning None")
                if output_file:
                    save_file(output_file, "")
                return ""
            if not cert_url.startswith("https://") and not disable_cert_url_checks:
                print("Error while generating JWS - provided cert_url does not use TLS! Returning None")
                if output_file:
                    save_file(output_file, "")
                return ""
            try:
                cert_url_data = urllib.request.urlopen(cert_url).read()
            except Exception as e:
                if not disable_cert_url_checks:
                    print(f"Error while generating JWS - certificate dereferencing from given url {cert_url} has failed! "
                          f"Returning None")
                    if output_file:
                        save_file(output_file, "")
                    return ""
                else:
                    cert_url_data = b''
            if cert_url_data not in cert_data and not disable_cert_url_checks:
                print("Error while generating JWS - certificate provided in cert_url does not match certificate "
                      "provided for signing JWS! Returning None")
                if output_file:
                    save_file(output_file, "")
                return ""
            header["x5u"] = cert_url
        else:
            # Generate list of encoded certs for x5c header field
            x5c = []
            for cert in certificates:
                cert_der = cert.public_bytes(serialization.Encoding.DER)
                cert_base64 = base64.b64encode(cert_der).decode('utf-8')
                x5c.append(cert_base64)
            header["x5c"] = x5c

        jws = jwt.encode(payload=flatten(json_payload), key=private_key, algorithm="EdDSA", headers=header)
        try:
            protected, payload, signature = jws.split('.')
            result = {
                "protected": protected,
                "payload": payload,
                "signature": signature
            }
        except ValueError:
            print("Error while generating JWS! Returning None")
            if output_file:
                save_file(output_file, "")
            return ""
    else:
        header["typ"] = "JWT"
        header["alg"] = "none"
        jws = jwt.encode(payload=flatten(json_payload), key=None, algorithm="none", headers=header)
        try:
            _, payload, _ = jws.split('.')
            result = {
                "header": header,
                "payload": payload
            }
        except ValueError:
            print("Error while generating JWS! Returning None")
            if output_file:
                save_file(output_file, "")
            return ""
    if output_file:
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            print(f"✅ Saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error occured while saving to file: {output_file}. Error: {e}")
    return json.dumps(result,ensure_ascii=False, indent=4)


def decode_jws(jws_source: dict | str, key_path: str | None = None, key_password: str | None = None) -> list:
    """
    Decodes given signed or unsigned JSON Web Signature object and returns list with:
    - header of JWS
    - JSON payload

    :param jws_source: source of JWS object. Can be given as str, str with full path to file or JSON dict
    :param key_path: optional full path to private key for decoding with signature checking
    :param key_password: optional password for the key
    :return: [dict with JWS headers JSON, dict with decrypted JSON payload]
    """
    jws_object = get_json(jws_source)
    if not jws_object:
        return []

    if jws_object.get("protected") and jws_object.get("signature"):
        try:
            with open(key_path, 'rb') as key_file:
                key_data = key_file.read()
        except FileNotFoundError:
            print(f"Could not find a key file: {key_path}")
            return []

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
        if not public_key:
            print(f"Failed to read key from {key_path}")
            return []

        jws = (f"{jws_object.get('protected', '')}."
               f"{jws_object.get('payload', '')}."
               f"{jws_object.get('signature', '')}")
        decoded_payload = None
        try:
            decoded_payload = jwt.decode(jws, public_key, algorithms=["EdDSA"])
        except jwt.ExpiredSignatureError:
            print("The signature has expired.")
        except jwt.InvalidTokenError:
            print(f"Invalid JWS object {jws}")
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []
        return [jwt.get_unverified_header(jws), decoded_payload]
    elif "header" in jws_object and "payload" in jws_object:
        return [
            jws_object.get('header', None),
            decode_base64url(jws_object.get('payload', None))
        ]
    else:
        print("Error while decoding JWS. Unrecognized JSON body")
        return []


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
    try:
        with open(file_path, 'r', encoding='utf-8') as input_file:
            content = input_file.read().strip()  # Strip to remove trailing newlines
    except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError, TypeError):
        print(f"❌ Error while reading file: {file_path}. Returning ''")
        return ""

    if file_type.upper() == 'HTTP':
        parts = content.split('\n\n', maxsplit=1)
        if len(parts) > 1:
            return parts[1]  # Extract payload after headers
        return ""

    elif file_type.upper() == 'JSON':
        try:
            json_data = json.loads(content)
            flattened_data = flatten(json_data)  # Assuming `flatten` is defined elsewhere
            return json.dumps(generate_jws(flattened_data, cert_path, key_path))  # Assuming `generate_jws` is defined
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    elif file_type.lower() == 'plain':
        return content

    else:
        print("Invalid format. Supported formats: 'HTTP', 'JSON', 'PLAIN'. Returning ''")
        return ""


def is_jws(jws_body: str | dict) -> bool:
    """
    Validates correct format of JWS string or dict

    :param jws_body: String or dict representation of JWS JSON body
    :return: Bool result of check
    """
    jws_json = get_json(jws_body)
    if not jws_json:
        return False

    header, protected, payload, signature = (
        jws_json.get(p, None) for p in ('header', 'protected', 'payload', 'signature')
    )
    if protected:
        try:
            header = json.loads(decode_base64url(protected))
        except TypeError or json.JSONDecodeError:
            return False
    try:
        return all(('alg' in header.keys(),
                    header['alg'] == 'EdDSA'
                    or header['alg'] == 'none',
                    len(payload) > 0
                    ))
    except ValueError or TypeError:
        return False


def is_unsigned_jws(jws: str | dict) -> bool:
    if isinstance(jws, str):
        jws = get_json(jws)
    header = get_json(jws.get('header', {}))
    if header:
        return True if header.get('alg', '').strip().lower() == "none" else False
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


def is_signed_by_tracable_pca(jws: str, trusted_pca_pem: str) -> bool:
    def validate_cert_chain(cert_chain: List[x509.Certificate], trusted_pca_cert: x509.Certificate) -> bool:
        # Certs in x5c: [leaf, intermediate(s)...]
        for i in range(len(cert_chain) - 1):
            if not is_signed_by(cert_chain[i + 1], cert_chain[i]):
                # Cert not signed by issuer in chain
                return False
        # Last cert must be signed by PCA
        return is_signed_by(trusted_pca_cert, cert_chain[-1])

    def load_cert_chain_from_x5c(x5c_list: List[str]) -> List[x509.Certificate]:
        return [x509.load_der_x509_certificate(base64.b64decode(cert)) for cert in x5c_list]

    def is_signed_by(issuer_cert: x509.Certificate, subject_cert: x509.Certificate) -> bool:
        try:
            pubkey = issuer_cert.public_key()
            pubkey.verify(
                subject_cert.signature,
                subject_cert.tbs_certificate_bytes,
                # Algorithm is inferred in modern APIs (Ed448, RSA, etc.)
            )
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            # Signature check error: {e}
            return False

    try:
        # Parse JWS parts
        header_b64, payload_b64, signature_b64 = jws.split('.')
        header = json.loads(base64.urlsafe_b64decode(header_b64 + '==').decode())
        x5c = header.get("x5c", [])
        if not x5c:
            # Missing x5c in JWS header
            return False

        cert_chain = load_cert_chain_from_x5c(x5c)
        leaf_cert = cert_chain[0]
        public_key = leaf_cert.public_key()

        # Verify JWS signature
        signed_data = f"{header_b64}.{payload_b64}".encode()
        signature = base64.urlsafe_b64decode(signature_b64 + '==')

        public_key.verify(
            signature,
            signed_data
        )

        # Load trusted PCA
        pca_cert = x509.load_pem_x509_certificate(trusted_pca_pem.encode())

        # Validate the cert chain
        if not validate_cert_chain(cert_chain, pca_cert):
            # Cert chain is NOT traceable to PCA
            return False

        # JWS is valid and cert is traceable to PCA
        return True

    except InvalidSignature:
        # Invalid JWS signature
        return False
    except Exception as e:
        # JWS verification failed: {e}
        return False


def validate_identifier(element_record, element_name):
    """
    Validates common logic of logger messages.
    :param element_record: String with unique identifier
    :param element_name: String with that identifies name of event
    :return: "FAILED" or "PASSED" result of testing
    """
    if (result := is_type(element_record, element_name, str)) != 'PASSED':
        # Test step result FAILED in case of invalid format
        return result

    if f'urn:emergency:uid:{element_name.lower()}:' not in element_record:
        return f"FAILED-> Missing 'urn:emergency:uid:{element_name}:' in '{element_record}'"

    match = re.search(rf"{re.escape(element_name.lower())}:([^:]+):", element_record)
    logid_string = match.group(1)
    if not (10 <= len(set(logid_string)) <= 36):
        return f"FAILED-> '{element_name}' doesn't contain unique string 10 to 36 characters long"

    fqdn = element_record.split(f'{logid_string}:')[1]
    if not re.search(FQDN_PATTERN, fqdn):
        return f"FAILED-> '{element_name}' doesn't contain FQDN of Logging Service"
    return "PASSED"


def get_jws_from_http_media_layer(http_packet):
    """
    Method that extracts JWS from HTTP MEDIA layer
    @param http_packet:
    @return: JWS string representation or None
    """
    jws = ''
    try:
        hex_str = http_packet.media.type.replace(":", "")
        jws = bytes.fromhex(hex_str).decode('utf-8')
    except (AttributeError, ValueError):
        pass
    return jws


def parse_json_objects(body_str):
    """
    Parse JSON objects from body string (single, newline-separated, or concatenated)
    
    :param body_str: String containing JSON data (single object, newline-separated, or concatenated)
    :return: List of parsed JSON objects
    """
    json_objects = []

    # Try single JSON object first
    try:
        return [json.loads(body_str)]
    except json.JSONDecodeError:
        pass

    # Try newline-separated objects
    for line in body_str.strip().split('\n'):
        if line.strip():
            try:
                json_objects.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    if json_objects:
        return json_objects

    # Try concatenated JSON objects
    idx = 0
    while idx < len(body_str):
        start = body_str.find('{', idx)
        if start == -1:
            break
            
        # Find matching closing brace
        open_braces = 0
        end = -1
        for i in range(start, len(body_str)):
            if body_str[i] == '{':
                open_braces += 1
            elif body_str[i] == '}':
                open_braces -= 1
                if open_braces == 0:
                    end = i + 1
                    break
        
        if end > start:
            try:
                json_obj = json.loads(body_str[start:end])
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                pass
            idx = end
        else:
            idx += 1

    return json_objects


def get_json(json_source) -> dict:
    """
    Tries to get JSON object from json_source which can be path to file, JSON str, or dict

    :param json_source: source of JSON payload. Can be a dict or str containing JSON,
                        or str with full path to file containing JSON body
    :return: JSON object as a dict or None
    """
    json_payload = None
    if json_source and isinstance(json_source, str):
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
                return {}
        else:
            try:
                json_payload = json.loads(json_source)
            except json.JSONDecodeError:
                print(f'Unable to load JSON from str: {json_source}')
                return {}
    elif json_source and isinstance(json_source, dict):
        json_payload = json_source
    else:
        print("Parameter 'json_source' should be a file path (str type), or JSON body (dict type)")

    return json_payload


def decode_base64url(b64_string: str | None = None) -> str | None:
    if not b64_string:
        return None
    padding = '=' * (-len(b64_string) % 4)
    try:
        bytes_decoded = base64.urlsafe_b64decode(b64_string + padding)
        encoding = from_bytes(bytes_decoded).best().encoding
        return bytes_decoded.decode(encoding)
    except Exception as e:
        print(f"Failed to decode base64url {b64_string}")
        return None


def is_valid_jcard(obj):
    """
    Validates whether the given object conforms to the jCard format as defined in RFC 7095.
    :param obj: Object to be validated
    :return: True if the object is a valid jCard, False otherwise.
    """
    if not isinstance(obj, list):
        return False

    if len(obj) < 2:
        return False

    if obj[0] != "vcard":
        return False

    for prop in obj[1:]:
        if not isinstance(prop, list):
            return False
        if len(prop) < 4:
            return False
    return True


def is_valid_fqdn(fqdn_string: str) -> bool:
    """
    Validates whether the given string has valid FQDN format.
    :param fqdn_string: String object with FQDN data
    :return: True if the object has valid FQDN format else False.
    """
    # Check if input is a string
    if not isinstance(fqdn_string, str):
        return False

    # Check if input is not an IP
    if fqdn_string.replace(".", "").isdigit():
        return False

    # Check total length
    if len(fqdn_string) == 0 or len(fqdn_string) > 253:
        return False

    # Remove trailing dot if present (valid in FQDN)
    if fqdn_string.endswith('.'):
        fqdn = fqdn_string[:-1]

    # Split into labels (parts between dots)
    labels = fqdn_string.split('.')
    if len(labels) < 2:
        return False

    # Pattern for valid label:
    # - starts and ends with alphanumeric
    # - can contain hyphens in the middle
    # - 1-63 characters long
    label_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$')

    # Verify each label
    for label in labels:
        if not label:  # Empty label (consecutive dots)
            return False

        if len(label) > 63:  # Label too long
            return False

        if not label_pattern.match(label):
            return False

    return True


def iso_to_timestamp(iso_string):
    """
    Convert ISO 8601 datetime string to Unix timestamp (float).
    :param: iso_string: String like '2025-11-18T12:58:03.01-05:00'
    :returns: Float representing Unix timestamp (seconds since epoch)
    """

    if not isinstance(iso_string, str):
        return None
    try:
        # Parse the ISO 8601 string to datetime object
        dt = datetime.fromisoformat(iso_string)

        # Convert to Unix timestamp (float)
        timestamp = dt.timestamp()

        return timestamp
    except:
        return None


def float_timestamp_to_iso(timestamp_str):
    """
    Convert pyshark timestamp to ISO 8601 format with timezone.
    :param: timestamp_str: String like '1763582033.366495000'
    :returns: String like '2025-11-18T12:58:03.01-05:00'
    """
    # Convert string to float (Unix timestamp in seconds)
    timestamp_float = float(timestamp_str)

    # Create datetime object in UTC
    dt_utc = datetime.fromtimestamp(timestamp_float, tz=timezone.utc)

    # Format with 2 decimal places for milliseconds
    formatted = dt_utc.strftime('%Y-%m-%dT%H:%M:%S')
    milliseconds = f"{(dt_utc.microsecond / 1000000):.2f}"[1:4]  # Get .XX part

    # UTC timezone is always +00:00
    return f"{formatted}{milliseconds}+00:00"


def is_valid_json(data) -> bool:
    """
    Validates if the given object is well-formed JSON.

    @param: data: Data to validate.
    @return: bool: True if well-formed JSON, False otherwise.
    """
    try:
        json.loads(data)
        return True
    except (json.JSONDecodeError,TypeError) as e:
        return False

      
def is_valid_fqdn(fqdn_sting: str) -> bool:
    """
    Validates whether the given string has valid FQDN format.
    :param fqdn_sting: String object with FQDN data
    :return: True if the object has valid FQDN format else False.
    """
    # Check if input is a string
    if not isinstance(fqdn_sting, str):
        return False

    # Check total length
    if len(fqdn_sting) == 0 or len(fqdn_sting) > 253:
        return False

    # Remove trailing dot if present (valid in FQDN)
    if fqdn_sting.endswith('.'):
        fqdn = fqdn_sting[:-1]

    # Split into labels (parts between dots)
    labels = fqdn_sting.split('.')

    if len(labels) < 3:
        return False

    # Pattern for valid label:
    # - starts and ends with alphanumeric
    # - can contain hyphens in the middle
    # - 1-63 characters long
    label_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$')

    # Verify each label
    for label in labels:
        if not label:  # Empty label (consecutive dots)
            return False

        if len(label) > 63:  # Label too long
            return False

        if not label_pattern.match(label):
            return False

    return True


def iso_to_timestamp(iso_string):
    """
    Convert ISO 8601 datetime string to Unix timestamp (float).
    :param: iso_string: String like '2025-11-18T12:58:03.01-05:00'
    :returns: Float representing Unix timestamp (seconds since epoch)
    """
    # Parse the ISO 8601 string to datetime object
    dt = datetime.fromisoformat(iso_string)

    # Convert to Unix timestamp (float)
    timestamp = dt.timestamp()

    return timestamp


def float_timestamp_to_iso(timestamp_str):
    """
    Convert pyshark timestamp to ISO 8601 format with timezone.
    :param: timestamp_str: String like '1763582033.366495000'
    :returns: String like '2025-11-18T12:58:03.01-05:00'
    """
    # Convert string to float (Unix timestamp in seconds)
    timestamp_float = float(timestamp_str)

    # Create datetime object in UTC
    dt_utc = datetime.fromtimestamp(timestamp_float, tz=timezone.utc)

    # Format with 2 decimal places for milliseconds
    formatted = dt_utc.strftime('%Y-%m-%dT%H:%M:%S')
    milliseconds = f"{(dt_utc.microsecond / 1000000):.2f}"[1:4]  # Get .XX part

    # UTC timezone is always +00:00
    return f"{formatted}{milliseconds}+00:00"
