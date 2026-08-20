TIMESTAMP_THRESHOLD = 3.0  # 3 sec

# ESRP is expected to dereference 3 Additional Data references per stimulus INVITE,
# so exactly 3 AdditionalDataQueryLogEvent and 3 AdditionalDataResponseLogEvent
# HTTP POSTs are expected on the Logging Service interface.
EXPECTED_ADR_COUNT = 3

ADR_RESPONSE_LOG_EVENT_TYPE = "AdditionalDataResponseLogEvent"


OPTIONAL_STRING_FIELDS = {
    "agencyAgentId": str,
    "agencyPositionId": str,
}

STATUS_CODES_REGISTRY = {
    333: "Iterative Refer",
    432: "Already Reported",
    433: "No Such Source ID",
    434: "Signature Verification Failure",
    436: "Duplicate or Invalid Priority",
    437: "Bad Policy Structure",
    438: "Unacceptable Algorithm",
    441: "Index Beyond Available Names",
    442: "Unacceptable Parameters",
    451: "Unknown Or Bad Policy Type",
    452: "Unknown Or Bad Agency Name",
    453: "Not Available Here, No Referral Available",
    454: "Unspecified Error",
    456: "Bad Queue",
    457: "Bad Dequeue Preference",
    458: "Policy Violation",
    459: "Bad Policy Expiration Time",
    460: "Bad LogEvent",
    461: "LogEvent Too Big",
    462: "LogEvent Extension Not On Allowed List",
    463: "LogEvent Extension On Disallowed List",
    464: "No Text In This Call",
    465: "Bad Timestamp",
    466: "EndTime Occurs Before StartTime",
    467: "Bad Or Missing Geoshape",
    468: "No Address Found",
    469: "Unknown MCS/GCS",
    470: 'Unknown Service/Database ("Not Ours")',
    471: "Unauthorized Reporter",
    472: "Unauthorized Responder",
    473: "Unknown ReportId",
    474: "Resolution Already Provided",
    475: "Response Not Available Yet",
}
