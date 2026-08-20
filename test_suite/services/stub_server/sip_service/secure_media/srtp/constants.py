from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SRTPProfile(str, Enum):
    """
    Supported SRTP profiles.

    The enum values use the DTLS-SRTP profile names from RFC 5764.
    SDES aliases are resolved by get_srtp_profile().
    """

    AES_CM_128_HMAC_SHA1_80 = "SRTP_AES128_CM_SHA1_80"
    AES_CM_128_HMAC_SHA1_32 = "SRTP_AES128_CM_SHA1_32"


@dataclass(frozen=True)
class SRTPProfileSpec:
    """
    Parameters required to configure one SRTP profile.
    """

    profile: SRTPProfile
    sdes_name: str
    dtls_name: str
    master_key_length: int
    master_salt_length: int

    @property
    def key_material_length(self) -> int:
        return self.master_key_length + self.master_salt_length


AES_CM_128_HMAC_SHA1_80 = SRTPProfileSpec(
    profile=SRTPProfile.AES_CM_128_HMAC_SHA1_80,
    sdes_name="AES_CM_128_HMAC_SHA1_80",
    dtls_name="SRTP_AES128_CM_SHA1_80",
    master_key_length=16,
    master_salt_length=14,
)

AES_CM_128_HMAC_SHA1_32 = SRTPProfileSpec(
    profile=SRTPProfile.AES_CM_128_HMAC_SHA1_32,
    sdes_name="AES_CM_128_HMAC_SHA1_32",
    dtls_name="SRTP_AES128_CM_SHA1_32",
    master_key_length=16,
    master_salt_length=14,
)


_PROFILE_ALIASES = {
    AES_CM_128_HMAC_SHA1_80.sdes_name: (AES_CM_128_HMAC_SHA1_80),
    AES_CM_128_HMAC_SHA1_80.dtls_name: (AES_CM_128_HMAC_SHA1_80),
    AES_CM_128_HMAC_SHA1_32.sdes_name: (AES_CM_128_HMAC_SHA1_32),
    AES_CM_128_HMAC_SHA1_32.dtls_name: (AES_CM_128_HMAC_SHA1_32),
}


def get_srtp_profile(
    profile: SRTPProfile | str,
) -> SRTPProfileSpec:
    """
    Resolve either an SDES or DTLS-SRTP profile name.
    """
    if isinstance(profile, SRTPProfile):
        normalized = profile.value
    else:
        normalized = (profile or "").strip().upper()

    specification = _PROFILE_ALIASES.get(normalized)

    if specification is None:
        supported = ", ".join(sorted(_PROFILE_ALIASES))

        raise ValueError(
            f"Unsupported SRTP profile {profile!r}. " f"Supported profiles: {supported}"
        )

    return specification


# libSRTP 2.5.0 values.
SSRC_UNDEFINED = 0
SSRC_SPECIFIC = 1
SSRC_ANY_INBOUND = 2
SSRC_ANY_OUTBOUND = 3

SRTP_MAX_TAG_LENGTH = 16
SRTP_MAX_MKI_LENGTH = 128

# Maximum bytes that srtp_protect() may append.
SRTP_MAX_TRAILER_LENGTH = SRTP_MAX_TAG_LENGTH + SRTP_MAX_MKI_LENGTH

# SRTCP additionally appends its 32-bit index.
SRTCP_MAX_TRAILER_LENGTH = SRTP_MAX_TRAILER_LENGTH + 4

DEFAULT_REPLAY_WINDOW = 128
