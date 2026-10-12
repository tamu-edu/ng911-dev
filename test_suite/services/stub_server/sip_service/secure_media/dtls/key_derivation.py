from __future__ import annotations

from dataclasses import dataclass

from ..srtp import (
    SRTPProfile,
    SRTPProfileSpec,
    get_srtp_profile,
)
from .constants import DTLSRole


@dataclass(frozen=True)
class SRTPKeys:
    """
    Directional SRTP key material.

    tx_key:
        Master key and master salt used for outbound SRTP/SRTCP.

    rx_key:
        Master key and master salt used for inbound SRTP/SRTCP.
    """

    tx_key: bytes
    rx_key: bytes
    profile: SRTPProfileSpec


def get_exporter_length(
    profile: SRTPProfile | str,
) -> int:
    """
    Return the RFC 5764 exporter length for an SRTP profile.

    Exported material contains:

        client master key
        server master key
        client master salt
        server master salt
    """
    specification = get_srtp_profile(profile)

    return 2 * (specification.master_key_length + specification.master_salt_length)


def derive_srtp_keys(
    exporter_keying_material: bytes,
    role: DTLSRole | str,
    profile: SRTPProfile | str,
) -> SRTPKeys:
    """
    Split RFC 5764 exporter material into local TX and RX keys.

    RFC 5764 exporter layout:

        client_write_SRTP_master_key
        server_write_SRTP_master_key
        client_write_SRTP_master_salt
        server_write_SRTP_master_salt
    """
    specification = get_srtp_profile(profile)

    expected_length = get_exporter_length(specification.profile)

    if len(exporter_keying_material) != expected_length:
        raise ValueError(
            "Invalid DTLS-SRTP exporter length: "
            f"expected {expected_length}, "
            f"received {len(exporter_keying_material)}"
        )

    try:
        resolved_role = (
            role if isinstance(role, DTLSRole) else DTLSRole(str(role).lower())
        )
    except ValueError as exc:
        raise ValueError("DTLS role must be 'client' or 'server'") from exc

    key_length = specification.master_key_length
    salt_length = specification.master_salt_length

    offset = 0

    client_master_key = exporter_keying_material[offset : offset + key_length]
    offset += key_length

    server_master_key = exporter_keying_material[offset : offset + key_length]
    offset += key_length

    client_master_salt = exporter_keying_material[offset : offset + salt_length]
    offset += salt_length

    server_master_salt = exporter_keying_material[offset : offset + salt_length]

    client_material = client_master_key + client_master_salt

    server_material = server_master_key + server_master_salt

    if resolved_role == DTLSRole.CLIENT:
        tx_key = client_material
        rx_key = server_material
    else:
        tx_key = server_material
        rx_key = client_material

    return SRTPKeys(
        tx_key=tx_key,
        rx_key=rx_key,
        profile=specification,
    )
