from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ctypes_loader import OpenSSLLibraries


class OpenSSLError(RuntimeError):
    """
    Raised when a native OpenSSL operation fails.
    """


def drain_openssl_errors(
    libraries: "OpenSSLLibraries",
) -> list[str]:
    """
    Drain the current thread's OpenSSL error queue.
    """
    errors: list[str] = []

    while True:
        error_code = libraries.crypto.ERR_get_error()

        if error_code == 0:
            break

        buffer = ctypes.create_string_buffer(256)

        libraries.crypto.ERR_error_string_n(
            error_code,
            buffer,
            len(buffer),
        )

        errors.append(
            buffer.value.decode(
                "utf-8",
                errors="replace",
            )
        )

    return errors


def format_openssl_errors(
    libraries: "OpenSSLLibraries",
) -> str:
    errors = drain_openssl_errors(libraries)

    if not errors:
        return "OpenSSL did not provide an error description"

    return "; ".join(errors)


def raise_openssl_error(
    libraries: "OpenSSLLibraries",
    operation: str,
) -> None:
    raise OpenSSLError(f"{operation} failed: " f"{format_openssl_errors(libraries)}")


def require_pointer(
    libraries: "OpenSSLLibraries",
    pointer,
    operation: str,
):
    """
    Validate that an OpenSSL operation returned a non-null pointer.
    """
    if not pointer:
        raise_openssl_error(
            libraries,
            operation,
        )

    return pointer


def require_success(
    libraries: "OpenSSLLibraries",
    result: int,
    operation: str,
    expected: int = 1,
) -> int:
    """
    Validate a conventional OpenSSL success return value.

    Most OpenSSL APIs used by this subsystem return 1 on success.
    """
    if result != expected:
        raise_openssl_error(
            libraries,
            operation,
        )

    return result
