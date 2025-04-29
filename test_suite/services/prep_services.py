from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed448
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta

from services.aux.json_services import generate_jws


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

    with open(output_certificate_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

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
