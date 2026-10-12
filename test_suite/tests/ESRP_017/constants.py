# Maximum tolerated delta (seconds) between the SIP INVITE receipt time on the
# stimulus interface and the RouteLogEvent timestamp emitted by the ESRP.
TIMESTAMP_THRESHOLD = 3.0

# Call-Info header URN patterns per NENA STA-010.3 for callId / incidentId
EMERGENCY_CALL_ID_URN_PREFIX = "urn:emergency:uid:callid:"
INCIDENT_ID_URN_PREFIX = "urn:emergency:uid:incidentid:"


OPTIONAL_FIELDS = {
    "ruleId": str,
    "cause": str,
    "agencyAgentId": str,
    "agencyPositionId": str,
    "clientAssignedIdentifier": str,
    "extension": dict,
}

# NENA STA-010.3f Section 10.33 "Policy Type" Registry — complete "Type" field listing
POLICY_TYPES = frozenset(
    {
        "OriginationRoutePolicy",
        "NormalNextHopRoutePolicy",
        "OtherRoutePolicy",
        "DequeueExpirationTime",
        "GISReplicas",
        "ECRF-LVFreplica",
        "TestCalls",
        "SIPcall",
        "LoST",
        "ElementState",
        "ServiceState",
        "HELDdereference",
        "AgentPresencePublish",
        "AgentPresencePut",
        "AgentPresenceSubscribe",
        "PolicyStore",
        "DiscrepancyReport",
        "QueueState",
        "DequeueRegistration",
        "ESRPNotify",
        "AbandonedCall",
        "SpatialInterface",
        "GapOverlap",
        "MCS",
        "GCS",
        "ConferenceEvent",
        "LoggingService",
        "LoggingSIPREC",
        "ServiceAgencyLocatorDereference",
        "ServiceAgencyLocatorNameSearch",
        "ServiceAgencyLocatorIndex",
        "MappingDataService",
    }
)
