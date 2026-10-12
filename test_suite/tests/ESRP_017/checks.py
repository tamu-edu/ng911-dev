from urllib.parse import urlparse

from services.aux_services.json_services import (
    float_timestamp_to_iso,
    is_valid_fqdn,
    is_valid_iso_datetime,
    iso_to_timestamp,
)
from services.aux_services.sip_msg_body_services import (
    is_valid_sip_call_id,
    is_valid_sip_uri,
)
from tests.ESRP_017.constants import (
    POLICY_TYPES,
    TIMESTAMP_THRESHOLD,
)


def _extract_fqdn_from_uri(uri: str) -> str:
    """Extract hostname from SIP, SIPS, HTTP, or HTTPS URI."""
    parsed = urlparse(uri)
    if parsed.hostname:
        return parsed.hostname
    # urlparse places the sip/sips host inside 'path' (no double-slash in scheme)
    if parsed.scheme in ("sip", "sips") and parsed.path:
        host_part = parsed.path.split("@", 1)[-1]
        host_part = host_part.split(":")[0].split(";")[0]
        return host_part
    if "@" in uri:
        host_part = uri.split("@", 1)[-1]
        host_part = host_part.split(":")[0].split(";")[0]

        return host_part
    return ""


def validate_policy_owner(policy_owner):
    try:
        assert (
            policy_owner is not None
        ), "FAILED -> No 'policyOwner' member found in RouteLogEvent"
        assert isinstance(policy_owner, str), "FAILED -> 'policyOwner' must be a string"
        if is_valid_fqdn(policy_owner):
            return "PASSED"
        fqdn = _extract_fqdn_from_uri(policy_owner)
        assert fqdn and is_valid_fqdn(
            fqdn
        ), "FAILED -> 'policyOwner' must be an FQDN or a URI containing an FQDN"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_policy_type(policy_type):
    try:
        assert (
            policy_type is not None
        ), "FAILED -> No 'policyType' member found in RouteLogEvent"
        assert isinstance(policy_type, str), "FAILED -> 'policyType' must be a string"
        assert (
            policy_type in POLICY_TYPES
        ), f"FAILED -> 'policyType' value '{policy_type}' is not in the Policy Types registry (Section 10.33)"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_policy_id(policy_type, policy_id):
    """
    policyId must be present when policyType == 'OtherRoutePolicy', absent for all other types.
    """
    try:
        assert (
            policy_type is not None
        ), "FAILED -> Cannot validate 'policyId'; 'policyType' is absent"
        if policy_type == "OtherRoutePolicy":
            assert (
                policy_id is not None
            ), "FAILED -> 'policyId' must be present when 'policyType' is 'OtherRoutePolicy'"
        else:
            assert (
                policy_id is None
            ), f"FAILED -> 'policyId' must not be present when 'policyType' is '{policy_type}'"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_policy_queue_name(policy_type, policy_queue_name):
    """
    policyQueueName must be present (and a SIP URI) when policyType is
    'OriginationRoutePolicy' or 'NormalNextHopRoutePolicy', absent for all other types.
    """
    try:
        assert (
            policy_type is not None
        ), "FAILED-> Cannot validate 'policyQueueName'; 'policyType' is absent"
        if policy_type in ("OriginationRoutePolicy", "NormalNextHopRoutePolicy"):
            assert (
                policy_queue_name is not None
            ), f"FAILED -> 'policyQueueName' must be present when 'policyType' is '{policy_type}'"
            assert isinstance(
                policy_queue_name, str
            ), "FAILED -> 'policyQueueName' must be a string"
            assert is_valid_sip_uri(
                policy_queue_name
            ), f"FAILED -> '{policy_queue_name}' is not a valid URL"
        else:
            assert (
                policy_queue_name is None
            ), f"FAILED -> 'policyQueueName' must not be present when 'policyType' is '{policy_type}'"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_timestamp(fe_timestamp, init_timestamp):
    try:
        assert (
            init_timestamp
        ), "NOT RUN -> SIP INVITE receipt timestamp is not available"
        assert (
            fe_timestamp is not None
        ), "FAILED -> No 'timestamp' member found in RouteLogEvent"
        assert isinstance(fe_timestamp, str), "FAILED -> 'timestamp' must be a string"
        assert is_valid_iso_datetime(
            fe_timestamp
        ), "FAILED -> 'timestamp' is not a valid ISO 8601 date-time"
        delta = abs(iso_to_timestamp(fe_timestamp) - init_timestamp)
        assert delta < TIMESTAMP_THRESHOLD, (
            f"FAILED -> 'timestamp' differs from SIP INVITE receipt time by more than "
            f"{TIMESTAMP_THRESHOLD}s.\n"
            f"SIP INVITE:    {float_timestamp_to_iso(init_timestamp)}\n"
            f"RouteLogEvent: {fe_timestamp}"
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_call_id_sip(call_id_sip, sip_call_id):
    try:
        assert (
            call_id_sip is not None
        ), "FAILED -> No 'callIdSip' member found in RouteLogEvent"
        assert isinstance(call_id_sip, str), "FAILED -> 'callIdSip' must be a string"
        assert is_valid_sip_call_id(
            call_id_sip
        ), "FAILED -> 'callIdSip' is not a valid SIP Call-ID"
        assert sip_call_id, (
            "NOT RUN -> Cannot compare 'callIdSip' with SIP INVITE; "
            "no Call-ID header found in stimulus SIP INVITE"
        )
        assert call_id_sip == sip_call_id, (
            f"FAILED -> 'callIdSip' in RouteLogEvent ('{call_id_sip}') does not match "
            f"'Call-ID' in SIP INVITE ('{sip_call_id}')"
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)
