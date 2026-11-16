DIRECTIONS = ["incoming", "outgoing"]
QUERY_EVENT_NAME = "LocationQueryLogEvent"
NOT_RUN = "NOT RUN -> No stimulus message found."
NO_JWS = "FAILED -> No JWS payload found"
REQUIRED_FIELDS = (
    "logEventType",
    "timestamp",
    "elementId",
    "agencyId",
    "callId",
    "incidentId",
    "callIdSip",
    "direction",
    "queryId",
    "uri",
    "text",
)

OPTIONAL_FIELDS = (
    "clientAssignedIdentifier",
    "agencyAgentId",
    "agencyPositionId",
    "extension",
)
