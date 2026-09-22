from enum import Enum


class DTLSRole(str, Enum):
    """
    Local DTLS endpoint role.
    """

    CLIENT = "client"
    SERVER = "server"


# OpenSSL file type.
SSL_FILETYPE_PEM = 1

# SSL_get_error() values.
SSL_ERROR_NONE = 0
SSL_ERROR_SSL = 1
SSL_ERROR_WANT_READ = 2
SSL_ERROR_WANT_WRITE = 3
SSL_ERROR_WANT_X509_LOOKUP = 4
SSL_ERROR_SYSCALL = 5
SSL_ERROR_ZERO_RETURN = 6
SSL_ERROR_WANT_CONNECT = 7
SSL_ERROR_WANT_ACCEPT = 8

# Certificate verification modes.
SSL_VERIFY_NONE = 0x00
SSL_VERIFY_PEER = 0x01
SSL_VERIFY_FAIL_IF_NO_PEER_CERT = 0x02

# BIO close behavior.
BIO_NOCLOSE = 0
BIO_CLOSE = 1

# RFC 5764 exporter label.
DTLS_SRTP_EXPORTER_LABEL = b"EXTRACTOR-dtls_srtp"

# OpenSSL 3.0.13 supported DTLS-SRTP profiles used by SipService.
DEFAULT_DTLS_SRTP_PROFILES = (
    "SRTP_AES128_CM_SHA1_80",
    "SRTP_AES128_CM_SHA1_32",
)

# Supported runtime versions.
SUPPORTED_OPENSSL_VERSION_PREFIX = "OpenSSL 3.0.13"
SUPPORTED_LIBSRTP_VERSION = "2.5.0"
