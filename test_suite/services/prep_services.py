import json
import requests
import os

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed448, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import UnsupportedAlgorithm
from datetime import datetime, timedelta

from services.aux_services.json_services import decode_jws, generate_jws


def get_logevent_id_list_from_json(
        json_source: str | dict,
        jws_param_name: str,
        jws_param_value: str,
        key_path: str,
        key_password: str = None
) -> list:
    result = []
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
            if "logEvent" in log_event_container.keys() and "logEventId" in log_event_container.keys():
                decoded_jws = decode_jws(log_event_container.get("logEvent"), key_path, key_password)
                if len(decoded_jws) == 2:
                    payload_data = decoded_jws[1]
                else:
                    payload_data = {}
                if jws_param_name in payload_data.keys():
                    if payload_data.get(jws_param_name) == jws_param_value:
                        result.append(log_event_container.get("logEventId"))
    return result


def send_http_request(
        url: str,
        method: str,
        content_type: str = 'application/json',
        cert_path: str = None,
        key_path: str = None,
        is_https: bool = False,
        body=None
) -> dict | str | None:
    try:
        session = requests.Session()
        headers = {'Content-Type': content_type}

        # If HTTPS and certificate is provided
        cert = (cert_path, key_path) if is_https and cert_path and key_path else None

        response = session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            data=body.encode() if isinstance(body, str) else body,
            cert=cert,
            verify=False  # Disable certificate verification (adjust if needed)
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


def replace_string_in_file(input_file: str, param_name: str, value: str, output_file: str):
    """
        Replaces all occurrences of `param_name` with `value` in a text file.

        :param input_file: Path to the input file.
        :param param_name: String to be replaced.
        :param value: Replacement string.
        :param output_file: Path to save the modified file.
        """
    if not value:
        print(f"⚠️ Empty value for replacing string '{param_name}' in file '{input_file}'. Skipping this step.")
        return
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


def remove_json_field_from_file(json_input_file: str, param_name: str, output_file: str, remove_all: bool = False):
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
            return {k: remove_field_recursive(v) for k, v in obj.items() if k != param_name}
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


def modify_json_file(json_input_file: str, param_name: str, value: str, output_file: str):
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


def extract_from_config(config_part: list | dict, extract_field: str, where_field: str = None, where_value=None):
    if isinstance(config_part, list):
        for item in config_part:
            if isinstance(item, dict) and item.get(where_field) == where_value:
                return item.get(extract_field)
    elif isinstance(config_part, dict):
        return config_part.get(extract_field)
    return None


def generate_str(string_to_modify: str, variables: list) -> str:
    return string_to_modify.format(*variables)


def generate_random_certificate(output_certificate_file, output_key_file, common_name="Ex Common Name", algorithm="ed448"):
    if algorithm.lower() == "ecdsa":
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    elif algorithm.lower() == "ed448":
        private_key = ed448.Ed448PrivateKey.generate()
    else:
        raise ValueError("Unsupported algorithm. Use 'ecdsa' or 'ed448'.")

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Example City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Example Org"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

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


def generate_pca_signed_certificate(pca_cert_file: str, pca_cert_key: str,
                                    output_cert_cn: str, output_cert_file: str, output_key_file: str,
                                    pca_cert_password: str = None, output_cert_password: str = None):

    if pca_cert_password:
        pca_cert_password = pca_cert_password.encode('utf-8')
    if output_cert_password:
        output_cert_password = output_cert_password.encode('utf-8')

    # Load PCA certificate
    with open(pca_cert_file, "rb") as f:
        cert_data = f.read().strip()
        pca_cert = x509.load_pem_x509_certificate(cert_data, backend=default_backend())

    # Load PCA private key
    with open(pca_cert_key, "rb") as f:
        key_data = f.read().strip()
        pca_private_key = serialization.load_pem_private_key(
            key_data, password=pca_cert_password, backend=default_backend()
        )
        if not isinstance(pca_private_key, ed448.Ed448PrivateKey):
            raise UnsupportedAlgorithm(f'Private key "{pca_cert_key}" does not use ECDSA with Curve448 (EdDSA)')

    # Generate a new private key for the output certificate
    private_key = ed448.Ed448PrivateKey.generate()

    if output_cert_password:
        private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(output_cert_password.encode())
        )

    # Generate subject name for the certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, output_cert_cn),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(pca_cert.subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True,
        )
        .sign(private_key=pca_private_key, algorithm=None)  # No hash needed for EdDSA
    )

    # Save signed certificate
    if os.path.exists(output_cert_file):
        os.remove(output_cert_file)
        print(f"⚠️ File exists, removing {output_cert_file}")
    with open(output_cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Save private key
    if os.path.exists(output_key_file):
        os.remove(output_key_file)
        print(f"⚠️ File exists, removing {output_key_file}")
    with open(output_key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    print(f"✅ Certificate saved to {output_cert_file}")
    print(f"✅ Private key saved to {output_key_file}")
