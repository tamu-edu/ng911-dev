import re
from services.aux.aux_services import extract_header_value_by_separator
from .constants import (
    EMERGENCY_IDENTIFIER_URN_PATTERN,
    INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN,
    FQDN_PATTERN,
    STRING_ID_PATTERN
)


def test_emergency_call_id_header(emergency_call_id_header):
    """
    Test to validate Emergency Call Identifier header.
    """
    try:
        assert emergency_call_id_header, "FAILED to find Emergency Call Identifier header"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_emergency_call_id_urn(emergency_call_id_header) -> str:
    """
    Test to validate Emergency Call Identifier URN.
    """
    try:
        assert emergency_call_id_header, "FAILED to find Emergency Call Identifier header"
        assert re.search(EMERGENCY_IDENTIFIER_URN_PATTERN,
                         emergency_call_id_header), "FAILED - Emergency Call Identifier URN wrong pattern"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_emergency_call_id_string_id(emergency_call_id_header):
    """
    Test to validate Emergency Call Identifier String ID.
    """
    try:
        assert emergency_call_id_header, "FAILED to find Emergency Call Identifier header"
        # Extract and validate fields from the header
        string_id = extract_header_value_by_separator(emergency_call_id_header, ":", -2)
        assert re.search(STRING_ID_PATTERN, string_id), "FAILED - Emergency Call Identifier String ID"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_emergency_call_id_fqdn(emergency_call_id_header):
    """
    Test to validate Emergency Call Identifier FQDN.
    """
    try:
        assert emergency_call_id_header, "FAILED to find Emergency Call Identifier header"
        # Extract and validate FQDN from the header
        fqdn = extract_header_value_by_separator(emergency_call_id_header, ":", -1)
        assert re.search(FQDN_PATTERN, fqdn), "FAILED - Emergency Call Identifier FQDN"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_incident_tracking_id_urn(incident_tracking_id_header):
    """
    Test to validate Incident Tracking Identifier URN.
    """
    try:
        assert incident_tracking_id_header, "FAILED to find Incident Tracking Identifier header"
        assert re.search(INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN,
                         incident_tracking_id_header), "FAILED - Incident Tracking Identifier URN wrong pattern"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_incident_tracking_id_string_id(incident_tracking_id_header):
    """
    Test to validate Incident Tracking Identifier String ID.
    """
    try:
        assert incident_tracking_id_header, "FAILED to find Incident Tracking Identifier header"
        string_id = extract_header_value_by_separator(incident_tracking_id_header, ":", -2)
        assert re.search(STRING_ID_PATTERN, string_id), "FAILED - Incident Tracking Identifier String ID"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_incident_tracking_id_fqdn(incident_tracking_id_header):
    """
    Test to validate Incident Tracking Identifier FQDN.
    """
    try:
        assert incident_tracking_id_header, "FAILED to find Incident Tracking Identifier header"
        fqdn = extract_header_value_by_separator(incident_tracking_id_header, ":", -1)
        assert re.search(FQDN_PATTERN, fqdn), "FAILED - Incident Tracking Identifier FQDN"
        return "PASSED"
    except AssertionError as e:
        return str(e)
