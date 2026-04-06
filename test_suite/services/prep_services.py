import json
import random  # nosec B311
import secrets
import string
from typing import Optional
from typing import List, Any

import requests
import os
import time

import base64

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed448 import Ed448PrivateKey
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed448
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta

from pathlib import Path

from services.aux_services.json_services import decode_jws, is_valid_fqdn
from services.aux_services.json_services import generate_jws as gjws
from services.aux_services.aux_services import validate_ip_port_combo


def generate_jws(
    json_source,
    cert_path: str | None = None,
    key_path: str | None = None,
    key_password: str | None = None,
    output_file: str | None = None,
    cert_url: str | None = None,
    disable_cert_url_checks=False,
) -> str:
    return gjws(
        json_source=json_source,
        cert_path=cert_path,
        key_path=key_path,
        key_password=key_password,
        output_file=output_file,
        cert_url=cert_url,
        disable_cert_url_checks=disable_cert_url_checks,
    )


def get_logevent_id_list_from_json(
    json_source: str | dict,
    jws_param_name: str,
    key_path: str,
    jws_param_value: str | None = None,
    key_password: str | None = None,
) -> list:
    result: List[Any] = []
    if isinstance(json_source, str):
        with open(json_source, "r") as f:
            data = json.load(f)
    elif isinstance(json_source, dict):
        data = json_source
    else:
        print(f"❌ Param json_source has incorrect type: {type(json_source)}")
        return []
    if "logEventContainers" in data.keys():
        log_event_cont_list = data.get("logEventContainers", [])
        for log_event_container in log_event_cont_list:
            if (
                "logEvent" in log_event_container.keys()
                and "logEventId" in log_event_container.keys()
            ):
                decoded_jws = decode_jws(
                    log_event_container.get("logEvent"), key_path, key_password
                )
                if len(decoded_jws) == 2:
                    try:
                        payload_data = json.loads(decoded_jws[1].strip())
                    except json.JSONDecodeError:
                        print(
                            "⚠️ Error decoding LogEvent JSON object, returning empty dict"
                        )
                        payload_data = {}
                else:
                    payload_data = {}
                if jws_param_name in payload_data.keys():
                    if jws_param_value:
                        if payload_data.get(jws_param_name) == jws_param_value:
                            result.append(log_event_container.get("logEventId"))
                    else:
                        result.append(log_event_container.get("logEventId"))
    return result


def return_first_element_from_list(list_param: list) -> str:
    return str(list_param[0]) if list_param else ""


def send_http_request(
    url: str,
    method: str,
    content_type: str = "application/json",
    cert_path: str | None = None,
    key_path: str | None = None,
    is_https: bool = False,
    body=None,
) -> dict | str | None:
    try:
        session = requests.Session()
        headers = {"Content-Type": content_type}

        # If HTTPS and certificate is provided
        cert = (cert_path, key_path) if is_https and cert_path and key_path else None

        response = session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            data=body.encode() if isinstance(body, str) else body,
            cert=cert,
            verify=False,  # Disable certificate verification (adjust if needed)
        )

        response.raise_for_status()
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            return response.text

    except requests.RequestException as e:
        print(f"[ERROR] HTTP request failed: {e}")
        return {}


def get_value_from_json(input_json_file: str, param_name: str, save_as: str) -> dict:
    value = None
    with open(input_json_file, "r") as f:
        data = json.load(f)
        if param_name in data:
            value = data[param_name]
    return {save_as: value}


def replace_string_in_file(
    input_file: str, param_name: str, value: str | None, output_file: str
):
    """
    Replaces all occurrences of `param_name` with `value` in a text file.

    :param input_file: Path to the input file.
    :param param_name: String to be replaced.
    :param value: Replacement string.
    :param output_file: Path to save the modified file.
    """
    # if not value:
    #     print(f"⚠️ Empty value for replacing string '{param_name}' in file '{input_file}'. Skipping this step.")
    #     return
    if value is None:
        value = ""
    input_file = input_file.removeprefix("file.")
    output_file = output_file.removeprefix("file.")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        return
    except Exception as e:
        print(f"❌ Failed to read {input_file}: {e}")
        return

    updated_content = content.replace(param_name, value)

    try:
        directory = os.path.dirname(output_file)
        os.makedirs(directory, exist_ok=True)
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"⚠️ File exists, removing {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"✅ Replaced '{param_name}' with '{value}' and saved to {output_file}")
    except Exception as e:
        print(f"❌ Failed to write to {output_file}: {e}")


def remove_json_field_from_file(
    json_input_file: str, param_name: str, output_file: str, remove_all: bool = False
):
    """
    Removes a field from JSON. If remove_all is True, removes all occurrences recursively.
    Otherwise, removes only top-level fields with the given param_name.

    :param json_input_file: Path to the input JSON file.
    :param param_name: Field name to remove.
    :param output_file: Path to the output JSON file.
    :param remove_all: Whether to remove the field recursively (default: False).
    """

    def remove_field_recursive(obj):
        if isinstance(obj, dict):
            return {
                k: remove_field_recursive(v) for k, v in obj.items() if k != param_name
            }
        elif isinstance(obj, list):
            return [remove_field_recursive(item) for item in obj]
        else:
            return obj

    try:
        with open(json_input_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_input_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return

    if remove_all:
        cleaned_data = remove_field_recursive(data)
    else:
        if isinstance(data, dict):
            data.pop(param_name, None)
        cleaned_data = data

    try:
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"⚠️ File exists, removing {output_file}")
        with open(output_file, "w") as f:
            json.dump(cleaned_data, f, indent=4)
        print(f"✅ Output saved to: {output_file}")
    except Exception as e:
        print(f"❌ Failed to write output: {e}")


def modify_json_file(
    json_input_file: str, param_name: str, value: str, output_file: str
):
    """
    Load a JSON file, set or update a parameter, and save the modified JSON to a new file.

    :param json_input_file: Path to the input JSON file.
    :param param_name: Name of the parameter to modify/add.
    :param value: Value to set for the parameter.
    :param output_file: Path where the modified JSON should be saved.
    """
    try:
        with open(json_input_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Input file '{json_input_file}' not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    # Modify or add the parameter
    data[param_name] = value

    # Save to the output file
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"⚠️ File exists, removing {output_file}")
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Successfully updated '{param_name}' and saved to '{output_file}'")
    except Exception as e:
        print(f"Error saving to output file: {e}")


def extract_from_config(
    config_part: list | dict,
    extract_field: str,
    where_field: str | None = None,
    where_value=None,
):
    if isinstance(config_part, list):
        for item in config_part:
            if isinstance(item, dict) and item.get(where_field) == where_value:
                return item.get(extract_field)
    elif isinstance(config_part, dict):
        return config_part.get(extract_field)
    return None


def generate_str(string_to_modify: str, variables: list) -> str:
    return string_to_modify.format(*variables)


def generate_url(
    address: list | str,
    protocol: str = "http",
    port: str | int = "80",
    url_prefix: str | None = None,
    path: str | None = None,
) -> str:
    if isinstance(address, list) and len(address) > 0:
        address = next((a for a in address if a), None) or ""
    if not address:
        print(
            f"⚠️ Could not find FQDN or IP while generating url for: "
            f"'{protocol}://{address}:{str(port)}/{(path or "").removeprefix('/')}'"
        )
        return ""
    if path:
        if not url_prefix:
            return f"{protocol.removesuffix('://')}://{address}:{str(port)}/{path.removeprefix('/')}"
        else:
            return (
                f"{protocol.removesuffix('://')}://{address}:{str(port)}/"
                f"{url_prefix.removeprefix('/').removesuffix('/')}/"
                f"{path.removeprefix('/')}"
            )
    else:
        if not url_prefix:
            return f"{protocol.removesuffix('://')}://{address}:{str(port)}"
        else:
            return (
                f"{protocol.removesuffix('://')}://{address}:{str(port)}/"
                f"{url_prefix.removeprefix('/').removesuffix('/')}"
            )


def generate_random_certificate(
    output_certificate_file,
    output_key_file,
    common_name="Ex Common Name",
    algorithm="ed448",
):
    if algorithm.lower() == "ecdsa":
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    elif algorithm.lower() == "ed448":
        private_key = ed448.Ed448PrivateKey.generate()
    else:
        raise ValueError("Unsupported algorithm. Use 'ecdsa' or 'ed448'.")

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Example City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Example Org"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(days=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    )

    # ✨ Conditional signing logic
    if algorithm.lower() == "ecdsa":
        cert = cert_builder.sign(private_key, hashes.SHA512(), default_backend())
    else:
        cert = cert_builder.sign(private_key, algorithm=None, backend=default_backend())

    if os.path.exists(output_certificate_file):
        os.remove(output_certificate_file)
        print(f"⚠️ File exists, removing {output_certificate_file}")

    with open(output_certificate_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    if os.path.exists(output_key_file):
        os.remove(output_key_file)
        print(f"⚠️ File exists, removing {output_key_file}")

    with open(output_key_file, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    print(f"✅ Certificate saved to {output_certificate_file}")
    print(f"🔐 Private key saved to {output_key_file}")


class CertificateGenerationError(RuntimeError):
    """
    Raised when certificate generation fails in strict mode.

    This exception indicates a non-recoverable PKI operation failure,
    such as invalid key type, broken PEM format, incorrect password,
    signing failure, or filesystem write error.

    In TestSuite environments, this exception may be suppressed when
    allow_empty_on_error=True to intentionally generate invalid artifacts.
    """

    pass


def generate_pca_signed_certificate(
    pca_cert_file: str,
    pca_cert_key: str,
    output_cert_cn: str,
    output_cert_file: str,
    output_key_file: str,
    pca_cert_password: Optional[str] = None,
    output_cert_password: Optional[str] = None,
    validity_days: int = 365,
    allow_empty_on_error: bool = True,
) -> None:
    """
    Generate an Ed448 leaf certificate signed by a PCA (issuer) certificate.

    This function:
        1. Loads a PCA certificate (PEM).
        2. Loads a PCA Ed448 private key (PEM, optionally encrypted).
        3. Generates a new Ed448 key pair.
        4. Builds and signs a leaf certificate.
        5. Writes:
            - The signed certificate (PEM) to output_cert_file
            - The private key (PKCS8 PEM, optionally encrypted) to output_key_file

    Parameters
    ----------
    pca_cert_file : str
        Path to PCA (issuer) certificate in PEM format.

    pca_cert_key : str
        Path to PCA private key in PEM format.

    output_cert_cn : str
        Common Name (CN) for the generated certificate.

    output_cert_file : str
        Output path for generated certificate (PEM).

    output_key_file : str
        Output path for generated private key (PKCS8 PEM).

    pca_cert_password : Optional[str]
        Password for decrypting PCA private key (if encrypted).

    output_cert_password : Optional[str]
        Password used to encrypt the generated private key.

    validity_days : int
        Validity period of generated certificate (default: 365 days).

    allow_empty_on_error : bool
        If True:
            - Errors do NOT raise exceptions.
            - Empty certificate and key files are generated.
            - Intended for negative testing of DUT in TestSuite.
        If False:
            - Any error raises CertificateGenerationError.

    Security Notes
    --------------
    - Only Ed448 (EdDSA) keys are supported.
    - Signing uses algorithm=None as required by EdDSA.
    - Strict validation ensures key/certificate algorithm consistency.
    - No deprecated cryptography backend APIs are used.
    """

    def _b(v: Optional[str]) -> Optional[bytes]:
        """
        Convert string password to UTF-8 bytes if provided.

        Returns None if input is None.
        """
        return v.encode("utf-8") if v else None

    pca_cert_password_b = _b(pca_cert_password)
    output_cert_password_b = _b(output_cert_password)

    def save_file(path: str, content: bytes) -> None:
        """
        Write file safely, replacing existing file if present.
        Ensures parent directory exists.
        """
        directory = os.path.dirname(path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        if os.path.exists(path):
            os.remove(path)

        with open(path, "wb") as f:
            f.write(content)

    def fail_or_empty(message: str, exc: Exception | None = None) -> bool:
        """
        Handle failure according to strictness mode.

        If allow_empty_on_error is True:
            - Logs error
            - Generates empty certificate and key files
            - Returns True (caller should stop execution)

        If allow_empty_on_error is False:
            - Raises CertificateGenerationError

        Returns
        -------
        bool
            True if empty artifacts were generated and execution
            should terminate silently.
        """
        full_msg = f"❌ Certificate generation error: {message}"
        if exc:
            full_msg += f"\n   → {exc}"

        print(full_msg)

        if allow_empty_on_error:
            print("⚠️ allow_empty_on_error=True → generating empty cert/key files.")
            save_file(output_cert_file, b"")
            save_file(output_key_file, b"")
            return True
        else:
            raise CertificateGenerationError(full_msg) from exc

    # --------------------------------------------------
    # Load PCA Certificate
    # --------------------------------------------------
    try:
        with open(pca_cert_file, "rb") as f:
            pca_cert = x509.load_pem_x509_certificate(f.read())
    except Exception as e:
        if fail_or_empty(f"Failed to load PCA certificate: {pca_cert_file}", e):
            return

    # --------------------------------------------------
    # Load PCA Private Key
    # --------------------------------------------------
    try:
        with open(pca_cert_key, "rb") as f:
            pca_private_key = serialization.load_pem_private_key(
                f.read(),
                password=pca_cert_password_b,
            )
    except Exception as e:
        if fail_or_empty(f"Failed to load PCA private key: {pca_cert_key}", e):
            return

    if not isinstance(pca_private_key, ed448.Ed448PrivateKey):
        if fail_or_empty(
            f'PCA key "{pca_cert_key}" is not Ed448. '
            f"Got {type(pca_private_key).__name__}"
        ):
            return

    # Validate PCA certificate public key type
    try:
        issuer_pub = pca_cert.public_key()
        if not isinstance(issuer_pub, ed448.Ed448PublicKey):
            if fail_or_empty(
                f'PCA certificate "{pca_cert_file}" public key is not Ed448.'
            ):
                return
    except Exception as e:
        if fail_or_empty("Failed to inspect PCA certificate public key", e):
            return

    # --------------------------------------------------
    # Generate Leaf Private Key
    # --------------------------------------------------
    leaf_private_key: None | Ed448PrivateKey = None
    try:
        leaf_private_key = ed448.Ed448PrivateKey.generate()
    except Exception as e:
        if fail_or_empty("Failed to generate leaf private key", e):
            return

    # Serialize Leaf Private Key
    leaf_private_key_pem: None | bytes = None
    try:
        if leaf_private_key:
            encryption = (
                serialization.BestAvailableEncryption(output_cert_password_b)
                if output_cert_password_b
                else serialization.NoEncryption()
            )

            leaf_private_key_pem = leaf_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption,
            )
    except Exception as e:
        if fail_or_empty("Failed to serialize leaf private key", e):
            return

    # --------------------------------------------------
    # Build and Sign Certificate
    # --------------------------------------------------
    cert = None
    try:
        if leaf_private_key:
            subject = x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, output_cert_cn.strip()),
                ]
            )

            now = datetime.utcnow()

            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(pca_cert.subject)
                .public_key(leaf_private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now)
                .not_valid_after(now + timedelta(days=validity_days))
                .add_extension(
                    x509.BasicConstraints(ca=False, path_length=None),
                    critical=True,
                )
                .sign(private_key=pca_private_key, algorithm=None)
            )
    except Exception as e:
        if fail_or_empty("Failed to build/sign certificate", e):
            return

    # --------------------------------------------------
    # Write Output Files
    # --------------------------------------------------
    try:
        if cert:
            save_file(output_cert_file, cert.public_bytes(serialization.Encoding.PEM))
        else:
            raise Exception("No Certificate to save")

        if leaf_private_key_pem:
            save_file(output_key_file, leaf_private_key_pem)
        else:
            raise Exception("No Private Key to save")
    except Exception as e:
        if fail_or_empty("Failed to write output files", e):
            return

    print(f"✅ Certificate saved to {output_cert_file}")
    print(f"✅ Private key saved to {output_key_file}")


def get_file_string_content(path: str) -> str:
    path = path.removeprefix("file.")
    path = path.removeprefix("var.")
    output = ""
    if path and Path(path).exists():
        with open(path, "r") as file:
            output = file.read()
    return output


def get_first_certificate_body(cert: str) -> str:
    body: List[Any] = []
    for line in cert.strip().splitlines():
        if not any(
            marker in line for marker in ["BEGIN CERTIFICATE", "END CERTIFICATE"]
        ):
            body.append(line)
        if "END CERTIFICATE" in line:
            break
    return "".join(body)


def generate_source_id(address: list | str | None) -> str:
    if isinstance(address, list) and len(address) > 0:
        address = next((a for a in address if a), None)
    if not address:
        print("⚠️ Could not find FQDN or IP while generating source-ID")
        return ""
    return f"testsourceid{str(time.time()).replace('.', '')}@{address}"


def get_list_from_json(json_source: str | dict, json_param: str) -> list:
    data = {}
    if isinstance(json_source, str):
        data = json.loads(json_source)
    elif isinstance(json_source, dict):
        data = json_source
    if json_param in data.keys():
        result = data.get(json_param)
        if isinstance(result, list):
            return result
        elif isinstance(result, str):
            return [result]
    return []


def replace_string_in_jws_json(
    json_input_file: str,
    param_name: str,
    replace_from: str,
    replace_to: str,
    output_file: str,
):
    """
    Decodes specified JWS JSON parameter, then replaces replace_from to replace_to and encodes back to base64URL
    :param json_input_file: Path to the input JSON file.
    :param param_name: JWS JSON parameter for replacing string in its value
    :param replace_from: string to replace
    :param replace_to: replacement string
    :param output_file: Path to the output JSON file.
    """
    try:
        with open(json_input_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_input_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return
    param_data = data.get(param_name, "")
    padding_needed = 4 - (len(param_data) % 4)
    if padding_needed and padding_needed != 4:
        param_data += "=" * padding_needed
    replaced_payload = base64.b64decode(param_data).decode("utf-8")
    replaced_payload = replaced_payload.replace(replace_from, replace_to)
    replaced_payload = (
        base64.urlsafe_b64encode(replaced_payload.encode()).decode().rstrip("=")
    )
    data[param_name] = replaced_payload
    try:
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"⚠️ File exists, removing {output_file}")
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Output saved to: {output_file}")
    except Exception as e:
        print(f"❌ Failed to write output: {e}")


def save_to_file(input_str: str, filename: str):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(input_str)
    except (FileNotFoundError, PermissionError, OSError, Exception):
        print(f"❌ Error occurred while saving to file: {filename}")


def build_certificate_chain(cert_filenames: list, output_filename: str):
    certs: List[Any] = []
    for file in cert_filenames:
        try:
            with open(file, "r", encoding="utf-8") as f:
                read = f.read().strip()
                if not [cert for cert in certs if read in cert]:
                    certs.append(read)
        except (FileNotFoundError, PermissionError, OSError, Exception):
            print(f"❌ Error occurred while reading file: {file}")
    save_to_file("\n".join(certs), output_filename)


def generate_future_timestamp(seconds_ahead: int) -> str:
    now = datetime.now().astimezone()
    out = now + timedelta(seconds=seconds_ahead)
    return out.isoformat(timespec="milliseconds")


def generate_identifier(identifier_type: str, fqdn: str) -> str:
    identifiers = {
        "callid": "urn:emergency:uid:callid",
        "incidentid": "urn:emergency:uid:incidentid",
        "logid": "urn:emergency:uid:logid",
    }
    if identifier_type.lower() not in identifiers.keys():
        print(
            f"❌ Failed to generate identifier - unknown type: {identifier_type}, returning None"
        )
        return ""
    if not fqdn:
        print("❌ Failed to generate identifier - fqdn not provided, returning None")
        return ""
    length = random.randint(10, 32)
    alphabet = string.ascii_letters + string.digits
    string_id = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{identifiers[identifier_type]}:{string_id}:{fqdn}"


def get_address(addresses: list) -> str:
    """
    From given addresses tries to find FQDN at first, if failed then uses first IP
    :addresses: list of str being IP or FQDN.
    :return: FQDN or first IP from given list
    """
    fqdn = next((addr for addr in addresses if is_valid_fqdn(addr)), "")
    ip = next(
        (addr for addr in addresses if validate_ip_port_combo(f"{addr}:5060")), ""
    )
    if fqdn:
        return fqdn
    return ip


def get_interface_address(interface_name: str, lab_config: dict) -> str:
    """
    Gets FQDN of IP of given interface name
    :interface_name: f.e. IF_OSP_BCF
    :return: FQDN or IP address
    """
    if len(interface_name.split("_")) != 3:
        print(f"❌ Given interface name is incorrect: {interface_name}")
        return ""
    entity = interface_name.split("_")[1]
    interfaces = extract_from_config(
        lab_config["lab_config"]["entities"], "interfaces", "name", entity
    )
    fqdn = extract_from_config(interfaces, "fqdn", "name", interface_name)
    ip = extract_from_config(interfaces, "ip", "name", interface_name)
    return get_address([fqdn, ip])
