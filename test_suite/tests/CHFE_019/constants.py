NOT_RUN = "NOT RUN -> No stimulus message found."

# Service URNs registered in RFC 5031 (counseling / sos hierarchies), plus the
# test and emergency URNs accepted by the CHFE_019 test case.
SERVICE_URNS = frozenset(
    {
        "urn:service:sos",
        "urn:service:sos.ambulance",
        "urn:service:sos.animal-control",
        "urn:service:sos.fire",
        "urn:service:sos.gas",
        "urn:service:sos.marine",
        "urn:service:sos.mountain",
        "urn:service:sos.physician",
        "urn:service:sos.poison",
        "urn:service:sos.police",
        "urn:service:test.sos",
        "urn:emergency:service",
    }
)

VARIATION_SIP_URI = "Refer_To_TRANSFER_TARGET_SIP_URI"
VARIATION_TEL_NUMBER = "Refer_To_TRANSFER_TARGET_TEL_NUM"
VARIATION_LOCATION = "Refer_To_TRANSFER_TARGET_LOCATION"
VARIATIONS = (VARIATION_SIP_URI, VARIATION_TEL_NUMBER, VARIATION_LOCATION)
