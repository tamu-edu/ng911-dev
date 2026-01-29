REQUIREMENTS_SCHEMA = {
    "RQ_LOG_002": {
        "requirement_text": "(Versions entry point result parameters)",
        "document_section": "4.12",
        "description": "Refers to the required parameters for the successful response of the Versions entry point.",
        "test_id": "LOG_001",
        "subtests": ["Verify if 'fingerprint' has string value", "Verify if 'version' is an array", "Verify if all 'versions' contain 'major' and 'minor' integer values", ]
    },
    "RQ_LOG_003": {
        "requirement_text": "The Versions entry point of the Logging Web Service MUST include, in the \"serviceInfo\" parameter, the parameter \"requiredAlgorithms\" whose value is an array of JWS algorithms (as described in 5.10)",
        "document_section": "4.12",
        "description": "The Versions entry point for the Logging Web Service MUST include the 'requiredAlgorithms' array within the 'serviceInfo' parameter, listing acceptable JWS algorithms.",
        "test_id": "LOG_001",
        "subtests": ["Verify if all 'versions' contain 'serviceInfo' with 'requiredAlgorithms' array of string values"]
    },
    "RQ_LOG_004": {
        "requirement_text": "Logging Services MUST implement a Session Recording Protocol (SIPREC - RFC 7866) interface [116] for recording the media and, if provided, the associated metadata.",
        "document_section": "4.12.1",
        "description": "Logging Services MUST implement the SIPREC (RFC 7866) interface for recording call media and any associated metadata.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_005": {
        "requirement_text": "Logging Services MUST provide a Real-time Streaming Protocol (RTSP) interface compliant with RTSP 2.0 (RFC 7826 [98]) to play back the media. RTSP 1.0 MUST NOT be used.",
        "document_section": "4.12.1",
        "description": "Logging Services MUST provide an RTSP 2.0 compliant interface for media playback; RTSP 1.0 is strictly forbidden.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_006": {
        "requirement_text": "Clients to the Logging Service MUST support logging to at least two Logging Services",
        "document_section": "4.12.1",
        "description": "Clients of the Logging Service MUST support logging to at least two Logging Services for redundancy.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_007": {
        "requirement_text": "Each Logging Service FE MUST implement the server-side of the ElementState event notification package.",
        "document_section": "4.12.1",
        "description": "Each Logging Service Functional Element (FE) MUST implement the server-side of the ElementState event notification package.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_008": {
        "requirement_text": "The Logging Service FE MUST promptly report changes in its state to its subscribed elements.",
        "document_section": "4.12.1",
        "description": "The Logging Service FE MUST promptly report any changes in its state to all subscribed elements.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_009": {
        "requirement_text": "The set of Logging Service FEs within an NGCS MUST implement the server-side of the ServiceState event notification package for the Logging Service.",
        "document_section": "4.12.1",
        "description": "The entire set of Logging Service FEs within the NGCS MUST implement the server-side of the ServiceState event notification package for the Logging Service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_010": {
        "requirement_text": "The Logging Service MUST implement the SRS interface.",
        "document_section": "4.12.2",
        "description": "The Logging Service MUST implement the SRS (Session Recording Server) interface.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_011": {
        "requirement_text": "at least one element in the call path MUST deploy the SRC interface.",
        "document_section": "4.12.2",
        "description": "At least one element within the call path MUST deploy the SRC (Session Recording Client) interface.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_016": {
        "requirement_text": "The Logging Service and its SRC interface MUST log the SIPREC Metadata LogEvent (see the LogEvent section for details).",
        "document_section": "4.12.2",
        "description": "The Logging Service and its SRC interface MUST log the SIPREC Metadata LogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_019": {
        "requirement_text": "Each emergency call (that is, each Communication Session), MUST result in a separate Recording Session. More than one Recording Session MAY be logged for a single call.",
        "document_section": "4.12.2",
        "description": "Each emergency call (Communication Session) MUST result in a separate Recording Session; multiple Recording Sessions MAY be logged for one call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_022": {
        "requirement_text": "All SRCs and SRSes MUST implement RTCP on the recording session.",
        "document_section": "4.12.2",
        "description": "All SRCs (Session Recording Clients) and SRSes (Session Recording Servers) MUST implement RTCP on the recording session.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_024": {
        "requirement_text": "The SRC MUST send wall clock time in sender reports, which MUST be recorded by the SRS.",
        "document_section": "4.12.2",
        "description": "The SRC MUST include wall clock time in its sender reports, and the SRS MUST record this information.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_026": {
        "requirement_text": "(common LogEvent prologue (base object/header) table)",
        "document_section": "4.12.3.1",
        "description": "Refers to the definition table for the common LogEvent prologue (base object/header).",
        "test_id": "LOG_003",
        "subtests": []
    },
    "RQ_LOG_027": {
        "requirement_text": "(common LogEvent prologue (base object/header) table)",
        "document_section": "4.12.3.1",
        "description": "Refers to the definition table for the common LogEvent prologue (base object/header).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_028": {
        "requirement_text": "(LogEvents GET parameters)",
        "document_section": "4.12.3.1.1",
        "description": "Refers to the parameters required for a LogEvents GET request.",
        "test_id": "LOG_002",
        "subtests": []
    },
    "RQ_LOG_030": {
        "requirement_text": "(LogEvents/{logEventId} GET parameters)",
        "document_section": "4.12.3.1.1",
        "description": "Refers to the parameters for a LogEvents/{logEventId} GET request, used to retrieve a specific log event.",
        "test_id": "LOG_004",
        "subtests": ["Validate 4xx error response"]
    },
    "RQ_LOG_032": {
        "requirement_text": "(LogEvents/{logEventId} GET response)",
        "document_section": "4.12.3.1.1",
        "description": "Refers to the required fields for the LogEvents/{logEventId} GET response.",
        "test_id": "LOG_004",
        "subtests": ["Validate JWS body from HTTP 200 OK response for HTTP GET request with correct logEventId."]
    },
    "RQ_LOG_033": {
        "requirement_text": "(The text in 4.12.3.1.1 applies to 4.12.3.1.3): When the event is a RecMediaStartEvent, the returned events will have one or more \"rtsp\" parameters inserted by the Logging Service that MUST be RTSP URIs. The RTSP URI can be used to play back the call session. The \"sdp\" and \"mediaLabel\" are also returned to indicate which media stream in the session the event refers to. These \"rtsp\" parameters MUST NOT refer to media from other SIPREC sessions that recorded the same call. Because the IRR functionality uses this interface, the Logging Service MUST ensure that it can return a usable RTSP URL as soon as recording starts. The Logging Service MUST ensure that any RTSP URL it returns remains valid for at least one hour.",
        "document_section": "4.12.3.1.3",
        "description": "For a RecMediaStartEvent, the returned events MUST contain RTSP URIs to play back the session. The Logging Service MUST return a usable RTSP URL immediately upon recording start and ensure it remains valid for at least one hour.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_034": {
        "requirement_text": "(LogEvents GET response)",
        "document_section": "4.12.3.1.1",
        "description": "Refers to the required format and fields for a LogEvents GET response.",
        "test_id": "LOG_004",
        "subtests": ["Validate JWS body from HTTP 200 OK response for HTTP GET request with correct logEventId."]
    },
    "RQ_LOG_035": {
        "requirement_text": "When the event is a RecMediaStartEvent, the returned events will have one or more \"rtsp\" parameters inserted by the Logging Service that MUST be RTSP URIs. The RTSP URI can be used to play back the call session. The \"sdp\" and \"mediaLabel\" are also returned to indicate which media stream in the session the event refers to. These \"rtsp\" parameters MUST NOT refer to media from other SIPREC sessions that recorded the same call. Because the IRR functionality uses this interface, the Logging Service MUST ensure that it can return a usable RTSP URL as soon as recording starts. The Logging Service MUST ensure that any RTSP URL it returns remains valid for at least one hour.",
        "document_section": "4.12.3.1.1",
        "description": "For a RecMediaStartEvent, the returned events MUST contain RTSP URIs for playback. The Logging Service MUST return a usable RTSP URL immediately upon recording start and ensure it remains valid for at least one hour.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_036": {
        "requirement_text": "(LogEvents POST response)",
        "document_section": "4.12.3.1.2",
        "description": "Refers to the required format and fields for a LogEvents POST response.",
        "test_id": "LOG_003",
        "subtests": []
    },
    "RQ_LOG_037": {
        "requirement_text": "(.../Conversations GET parameters)",
        "document_section": "4.12.3.2",
        "description": "Refers to the parameters required for the Conversations GET request, used to search for conversation records.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_038": {
        "requirement_text": "(.../Conversations GET response)",
        "document_section": "4.12.3.2",
        "description": "Refers to the required format and fields for the Conversations GET response.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_039": {
        "requirement_text": "(LogEventIds GET parameters)",
        "document_section": "4.12.3.3",
        "description": "Refers to the parameters required for the LogEventIds GET request, used to retrieve distinct log event types.",
        "test_id": "LOG_005",
        "subtests": ["Validate 4xx error response"]
    },
    "RQ_LOG_041": {
        "requirement_text": "(LogEventIds GET response)",
        "document_section": "4.12.3.3",
        "description": "Refers to the required format and fields for the LogEventIds GET response.",
        "test_id": "LOG_005",
        "subtests": ["Validate 200 OK + JSON response for any correct request"]
    },
    "RQ_LOG_042": {
        "requirement_text": "( .../CallIds GET parameters)",
        "document_section": "4.12.3.4",
        "description": "Refers to the parameters required for the CallIds GET request, used to search for distinct call identifiers.",
        "test_id": "LOG_006",
        "subtests": []
    },
    "RQ_LOG_044": {
        "requirement_text": "( .../CallIds GET response)",
        "document_section": "4.12.3.4",
        "description": "Refers to the required format and fields for the CallIds GET response.",
        "test_id": "LOG_006",
        "subtests": []
    },
    "RQ_LOG_045": {
        "requirement_text": "( .../IncidentIds GET parameters)",
        "document_section": "4.12.3.5",
        "description": "Refers to the parameters required for the IncidentIds GET request, used to search for distinct incident identifiers.",
        "test_id": "LOG_010",
        "subtests": []
    },
    "RQ_LOG_047": {
        "requirement_text": "( .../IncidentIds GET response)",
        "document_section": "4.12.3.5",
        "description": "Refers to the required format and fields for the IncidentIds GET response.",
        "test_id": "LOG_010",
        "subtests": []
    },
    "RQ_LOG_048": {
        "requirement_text": "( .../AgencyIds GET parameters)",
        "document_section": "4.12.3.6",
        "description": "Refers to the parameters required for the AgencyIds GET request, used to search for distinct agency identifiers.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_050": {
        "requirement_text": "( .../AgencyIds GET response)",
        "document_section": "4.12.3.6",
        "description": "Refers to the required format and fields for the AgencyIds GET response.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_052": {
        "requirement_text": "All agencies and NG9 1 1 functional elements MUST have access to a conformant Logging Service and log all relevant events in that service.",
        "document_section": "4.12.4",
        "description": "All agencies and NG9-1-1 functional elements MUST have access to a conformant Logging Service and log all relevant events.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_054": {
        "requirement_text": "CallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the CallStartLogEvent.",
        "test_id": "LOG_007",
        "subtests": []
    },
    "RQ_LOG_055": {
        "requirement_text": "CallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the CallEndLogEvent.",
        "test_id": "LOG_007",
        "subtests": []
    },
    "RQ_LOG_058": {
        "requirement_text": "RecCallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecCallStartLogEvent.",
        "test_id": "LOG_007",
        "subtests": []
    },
    "RQ_LOG_059": {
        "requirement_text": "RecCallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecCallEndLogEvent.",
        "test_id": "LOG_007",
        "subtests": []
    },
    "RQ_LOG_060": {
        "requirement_text": "RecCallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecCallStartLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_061": {
        "requirement_text": "RecCallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecCallEndLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_063": {
        "requirement_text": "CallTransferLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the CallTransferLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_065": {
        "requirement_text": "RouteLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RouteLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_067": {
        "requirement_text": "MediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the MediaStartLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_069": {
        "requirement_text": "MediaEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the MediaEndLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_071": {
        "requirement_text": "RecMediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecMediaStartLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_072": {
        "requirement_text": "RecMediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecMediaStartLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_073": {
        "requirement_text": "RecMediaEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecMediaEndLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_074": {
        "requirement_text": "RecordingFailedLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecordingFailedLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_075": {
        "requirement_text": "RecordingFailedLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RecordingFailedLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_077": {
        "requirement_text": "MessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the MessageLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_080": {
        "requirement_text": "AdditionalAgencyLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the AdditionalAgencyLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_083": {
        "requirement_text": "IncidentMergeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the IncidentMergeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_085": {
        "requirement_text": "IncidentUnMergeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the IncidentUnMergeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_087": {
        "requirement_text": "IncidentSplitLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the IncidentSplitLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_089": {
        "requirement_text": "IncidentLinkLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the IncidentLinkLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_091": {
        "requirement_text": "IncidentUnLinkLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the IncidentUnLinkLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_093": {
        "requirement_text": "IncidentClearLogEvent",
        "document_section": "4.12.3.7",
        "description": "Refers to the required members for the IncidentClearLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_095": {
        "requirement_text": "IncidentReopenLogEvent",
        "document_section": "4.12.3.7",
        "description": "Refers to the required members for the IncidentReopenLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_097": {
        "requirement_text": "LostQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the LostQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_100": {
        "requirement_text": "LostResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the LostResponseLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_105": {
        "requirement_text": "CallSignalingMessageLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the CallSignalingMessageLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_107": {
        "requirement_text": "SipRecMetadataLogEvent: The SRS MUST create LogEvents for any metadata received via the SIPREC metadata interface (RFC 7865) [117]. It does this by logging a SIPRECMetadataLogEvent to itself",
        "document_section": "4.12.3.7",
        "description": "The SRS MUST create SIPRECMetadataLogEvents for any metadata received via the SIPREC metadata interface (RFC 7865).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_108": {
        "requirement_text": "SipRecMetadataLogEvent: The SRS MUST fill in the header fields for which the values are known, such as the CallId and IncidentId supplied by the Session Recording Client.",
        "document_section": "4.12.3.7",
        "description": "For the SipRecMetadataLogEvent, the SRS MUST automatically fill in known header fields like the CallId and IncidentId provided by the SRC.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_109": {
        "requirement_text": "SipRecMetadataLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the SipRecMetadataLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_110": {
        "requirement_text": "SipRecMetadataLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the SipRecMetadataLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_113": {
        "requirement_text": "NonRtpMediaMessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the NonRtpMediaMessageLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_116": {
        "requirement_text": "AliLocationQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the AliLocationQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_121": {
        "requirement_text": "AliLocationResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the AliLocationResponseLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_123": {
        "requirement_text": "MalformedMessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the MalformedMessageLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_128": {
        "requirement_text": "EidoLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the EidoLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_130": {
        "requirement_text": "DiscrepancyReportLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the DiscrepancyReportLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_131": {
        "requirement_text": "DiscrepancyReportLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the DiscrepancyReportLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_132": {
        "requirement_text": "ElementStateChangeLogEvent: When an element sends a notification of state change as described in the Element State section of this document, it MUST log the ElementStateChangeLogEvent.",
        "document_section": "4.12.3.7",
        "description": "When an element sends a notification of a state change, it MUST log the ElementStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_133": {
        "requirement_text": "ElementStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the ElementStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_134": {
        "requirement_text": "ElementStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the ElementStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_135": {
        "requirement_text": "ServiceStateChangeLogEvent: When a Service sends a notification of state change as described in the Service State section of this document, which includes Security Posture, it MUST log the ServiceStateChangeLogEvent.",
        "document_section": "4.12.3.7",
        "description": "When a Service sends a state change notification, which includes Security Posture, it MUST log the ServiceStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_136": {
        "requirement_text": "ServiceStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the ServiceStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_137": {
        "requirement_text": "ServiceStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the ServiceStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_138": {
        "requirement_text": "AdditionalDataQueryLogEvent: A server for AdditionalData that is located inside an ESInet, or LNG, or LSRG operated by, or on behalf of, a 9-1-1 Authority, MUST log all queries it receives.",
        "document_section": "4.12.3.7",
        "description": "An AdditionalData server within the ESInet (or an LNG/LSRG operated by a 9-1-1 Authority) MUST log all queries it receives using the AdditionalDataQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_140": {
        "requirement_text": "AdditionalDataQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the AdditionalDataQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_145": {
        "requirement_text": "AdditionalDataResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the AdditionalDataResponseLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_149": {
        "requirement_text": "LocationQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the LocationQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_153": {
        "requirement_text": "LocationResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the LocationResponseLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_156": {
        "requirement_text": "CallStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the CallStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_159": {
        "requirement_text": "GatewayCallLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the GatewayCallLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_162": {
        "requirement_text": "HookflashLogEvent member",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the HookflashLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_164": {
        "requirement_text": "LegacyDigitsLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the LegacyDigitsLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_168": {
        "requirement_text": "AgentStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the AgentStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_172": {
        "requirement_text": "QueueStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the QueueStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_174": {
        "requirement_text": "KeepAliveFailureLogEvent: Malformed, invalid, or responses not received from the other element MUST be logged in a \"responseStatus\" member that contains text and a status code from the Status Codes Registry (Section 10.29). There is a TimeOut status in that registry that is used for a timeout failure of OPTIONS.",
        "document_section": "4.12.3.7",
        "description": "Malformed, invalid, or missing responses to keep-alive checks MUST be logged in the 'responseStatus' member of the KeepAliveFailureLogEvent, including text and a status code like TimeOut.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_175": {
        "requirement_text": "KeepAliveFailureLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the KeepAliveFailureLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_176": {
        "requirement_text": "KeepAliveFailureLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the KeepAliveFailureLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_177": {
        "requirement_text": "RouteRuleMsgLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the RouteRuleMsgLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_179": {
        "requirement_text": "PolicyChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the PolicyChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_181": {
        "requirement_text": "VersionsLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the VersionsLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_182": {
        "requirement_text": "VersionsLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the VersionsLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_183": {
        "requirement_text": "SubscribeLogEvent: The Server MUST log this event",
        "document_section": "4.12.3.7",
        "description": "The Server MUST log the SubscribeLogEvent when a subscription request is processed.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_185": {
        "requirement_text": "SubscribeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the SubscribeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_186": {
        "requirement_text": "SubscribeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "Describes the required members for the SubscribeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_187": {
        "requirement_text": "All protocol operations MUST be integrity-protected with TLS, using SHA-256 [62] or stronger. SHA-256 MUST be supported by all implementations.",
        "document_section": "5.7",
        "description": "All protocol operations MUST be integrity-protected using TLS with a minimum of SHA-256 or stronger.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_188": {
        "requirement_text": "All protocol operations MUST be integrity-protected with TLS, using SHA-256 [62] or stronger. SHA-256 MUST be supported by all implementations.",
        "document_section": "5.7",
        "description": "All protocol operations MUST be integrity-protected using TLS with a minimum of SHA-256 or stronger.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_189": {
        "requirement_text": "All protocol operations MUST be privacy protected via TLS, preferably using Advanced Encryption Standard (AES) [63] with a minimum key length of 256 bits (AES-256). Shorter key length MUST NOT be used. Systems currently using Data Encryption Standard (DES) or triple-DES MUST be upgraded to at least AES-256. Alternate encryption algorithms are acceptable as long as they are at least as strong as AES.",
        "document_section": "5.8",
        "description": "All protocol operations MUST be privacy protected via TLS using a minimum of AES-256 encryption; shorter key lengths are forbidden, and legacy systems must be upgraded.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_191": {
        "requirement_text": "The Logging Recorder MUST be able to provide a clean shut down by sending a BYE as specified in Section 3.1.1.3, for example when one SRS in a redundant pair is going out of service.",
        "document_section": "4.12.2.6",
        "description": "The Logging Recorder MUST be able to perform a clean shut down by sending a BYE message.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_195": {
        "requirement_text": "As described in Section 5.10, the Logging Service MUST be capable of handling signed and unsigned LogEvents and certain signing algorithms.",
        "document_section": "4.12.3.1",
        "description": "The Logging Service MUST be able to handle both signed and unsigned LogEvents, along with supporting specific signing algorithms (Section 5.10).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_196": {
        "requirement_text": "Logging Services MUST be capable of verifying the signature of a signed LogEvent during the processing of the LogEvent request (i.e., before returning the response).",
        "document_section": "4.12.3.1",
        "description": "Logging Services MUST be capable of verifying the signature of any signed LogEvent before returning a response.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_197": {
        "requirement_text": "If the signature verification fails, it MUST return a \"Signature Verification Failed\" status code as a warning",
        "document_section": "4.12.3.1",
        "description": "If signature verification fails, the Logging Service MUST return a 'Signature Verification Failed' status code as a warning.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_198": {
        "requirement_text": "Logging Services MUST be capable of verifying the signature of a signed LogEvent during the processing of the LogEvent request (i.e., before returning the response). The currently in force policy of the agency operating the Logging Service determines if the Logging Service does so. If the signature verification fails, it MUST return a \"Signature Verification Failed\" status code as a warning and SHOULD generate (subject to throttling) a Signature/Certificate Discrepancy Report (Section 3.7.22) to the logging entity. This is a warning, not an error; the LogEvent MUST be recorded",
        "document_section": "4.12.3.1",
        "description": "Logging Services MUST verify the LogEvent signature before responding. A failed signature returns a warning, SHOULD generate a Discrepancy Report, and the LogEvent MUST still be recorded as it's not an error.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_199": {
        "requirement_text": "Logging Services MUST be capable of verifying the signature of a signed LogEvent during the processing of the LogEvent request (i.e., before returning the response). The currently in force policy of the agency operating the Logging Service determines if the Logging Service does so. If the signature verification fails, it MUST return a \"Signature Verification Failed\" status code as a warning and SHOULD generate (subject to throttling) a Signature/Certificate Discrepancy Report (Section 3.7.22) to the logging entity. This is a warning, not an error; the LogEvent MUST be recorded, and the client MUST NOT retry the request.",
        "document_section": "4.12.3.1",
        "description": "Logging Services MUST verify the LogEvent signature before responding. A failed signature returns a warning, the LogEvent MUST be recorded, and the client MUST NOT retry the request.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_200": {
        "requirement_text": "A Logging Service MUST support both mechanisms (e.g., by using a certificate cache indexable by thumbprint and loaded by resolving the certificate URL).",
        "document_section": "4.12.3.1",
        "description": "A Logging Service MUST support both mechanisms for certificate handling (by reference and by value), possibly using a thumbprint-indexed certificate cache.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_201": {
        "requirement_text": "(LogEvents POST parameters)",
        "document_section": "4.12.3.1.2",
        "description": "Refers to the parameters required for a LogEvents POST request.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_202": {
        "requirement_text": "Each Web Service that has entrypoints in which a JWS is used MUST include the \"requiredAlgorithms\" parameter in the \"serviceInfo\" parameter of the object returned by its Versions entrypoint.",
        "document_section": "5.10",
        "description": "Each Web Service using a JWS MUST include the 'requiredAlgorithms' parameter within the 'serviceInfo' object returned by its Versions entry point.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_203": {
        "requirement_text": "Any element inside a PSAP that provides a call queue MUST deploy an ElementState notifier as described in Section 2.4.1.",
        "document_section": "4.6.6",
        "description": "Any element inside a PSAP providing a call queue MUST deploy an ElementState notifier (Section 2.4.1).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_204": {
        "requirement_text": "The PSAP MUST implement an NTP client interface for time of day information.",
        "document_section": "4.6.16",
        "description": "The PSAP MUST implement an NTP client interface for time of day synchronization.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_206": {
        "requirement_text": "The services, unless specified otherwise, MUST support HTTP/1.1 (RFC 7230) [162] and SHOULD support HTTP/2.0 (RFC 7540) [197].",
        "document_section": "2.8.1",
        "description": "The services, unless specified otherwise, MUST support HTTP/1.1 and SHOULD support HTTP/2.0.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_207": {
        "requirement_text": "Clients MUST appropriately handle all status codes listed for each supported entry point, and MUST react appropriately to other status codes received, based on the first digit as per RFC 7231 [223] Section 6.",
        "document_section": "2.8.2",
        "description": "Clients MUST handle all listed status codes and react to other status codes based on the first digit as per RFC 7231, Section 6.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_208": {
        "requirement_text": "Implementations MUST ignore elements of data structures they do not understand and MUST return 404 errors to entry points to the web interfaces they don't provide as a server.",
        "document_section": "2.8.3",
        "description": "Implementations MUST ignore unknown data structure elements and MUST return 404 errors for unsupported web interface entry points.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_209": {
        "requirement_text": "Each Web Service MUST implement an entry point called \"Versions\".",
        "document_section": "2.8.3",
        "description": "Each Web Service MUST implement a mandatory entry point called 'Versions'.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_210": {
        "requirement_text": "Implementations MUST ignore elements of data structures they do not understand",
        "document_section": "2.8.3",
        "description": "Implementations MUST ignore elements of data structures they do not understand.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_211": {
        "requirement_text": "Clients MUST retry transactions on redundant elements that that could not be completed on the initial element.",
        "document_section": "2.9",
        "description": "Clients MUST retry transactions on redundant elements if they could not be completed on the initial element.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_212": {
        "requirement_text": "Every implementation MUST be capable of using a DNS based implementation of redundant elements where more than one address may be returned for the URI provided.",
        "document_section": "2.9",
        "description": "Every implementation MUST be capable of using a DNS-based implementation for redundant elements when multiple addresses are returned for a URI.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_213": {
        "requirement_text": "Implementations MUST be capable of preferring the first returned address, and using the second, third and optionally additional addresses returned as representing redundant elements for the service.",
        "document_section": "2.9",
        "description": "Implementations MUST prefer the first returned address and use subsequent addresses as redundant elements for the service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_214": {
        "requirement_text": "Other mechanisms to achieve redundancy MAY be provided, but the DNS based mechanism MUST be supported by all services and clients of those services.",
        "document_section": "2.9",
        "description": "The DNS-based redundancy mechanism MUST be supported by all services and clients, although other mechanisms MAY be provided.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_215": {
        "requirement_text": "Entities implementing a notifier MUST implement RFC 3857 [26].",
        "document_section": "3.1.3.2",
        "description": "Entities implementing a notifier MUST implement RFC 3857.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_216": {
        "requirement_text": "Each database, service, and agency MUST provide a Discrepancy Reporting web service.",
        "document_section": "3.7",
        "description": "Each database, service, and agency MUST provide a Discrepancy Reporting web service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_217": {
        "requirement_text": "The functional elements described in this document MUST support the discrepancy report (DR) function.",
        "document_section": "3.7",
        "description": "All functional elements described MUST support the discrepancy report (DR) function.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_218": {
        "requirement_text": "Implementations that access JWSs MUST support certificates (and chains) both by reference and by value; implementations that generate JWSs MAY use either.",
        "document_section": "5.10",
        "description": "Implementations accessing JWSs MUST support certificates by both reference and value; implementations generating JWSs MAY use either method.",
        "test_id": "LOG_008",
        "subtests": []
    },
    "RQ_LOG_219": {
        "requirement_text": "Implementations MUST support (be capable of generating and using) algorithm \"EdDSA\" and MUST NOT use other algorithms except that implementations of the Logging Service and clients of the Logging Service MUST support (be capable of generating and using) unsigned (algorithm \"none\")",
        "document_section": "5.10",
        "description": "Implementations MUST support the 'EdDSA' algorithm and no others, except the Logging Service and its clients, which MUST also support the unsigned 'none' algorithm.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_220": {
        "requirement_text": "If a Web Service request receives an \"Unacceptable Algorithm\" error, the client MUST make a new request on the Versions entry point and retry the request with a JWS that uses a signing algorithm acceptable to the Web Service.",
        "document_section": "5.10",
        "description": "If an 'Unacceptable Algorithm' error is received, the client MUST query the Versions entry point and retry the request using an acceptable JWS signing algorithm.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_221": {
        "requirement_text": "When this document indicates that a set of Web Service interface parameters is a JWS (e.g., for LogEvents), the set of parameters is conveyed in the web service request as a string consisting of a JWS. The JWS is formed by applying the JWS algorithm to the set of parameters per the JWS standard [171]. The JWS Protected Header MUST contain exactly one \"alg\" field. The \"alg\" field MUST have a value acceptable to the Web Service. An unsigned (unprotected) JWS is indicated by an \"alg\" field set to the value \"none\". For signed LogEvents, and all other uses of JWS requiring signatures (e.g., policy documents), the JWS Protected Header MUST have its \"alg\" field set to a value acceptable to the Web Service that MUST NOT be \"none\" and MUST specify the signing entity s X.509 certificate and all intermediate certificates up to one signed by the trusted root58. The certificate is provided either by reference or by value. A certificate provided by value is contained in an \"x5c\" field. A certificate is provided by reference using the \"x5u\" and \"x5t#256\" fields. When the \"x5u\" field is present, it MUST contain a URL that is stable (resolvable) for a minimum of 10 years. The JWS Protected Header MAY contain other fields. When the \"x5u\" field is used, the \"x5t#256\" field MUST also be used, to allow an entity to more easily detect when a certificate chain needs to be retrieved.",
        "document_section": "5.10",
        "description": "Web Service parameters are conveyed as a JWS with one 'alg' field in the Protected Header. Signed JWS MUST use a non-'none' algorithm and include the X.509 certificate (by value: 'x5c' or reference: 'x5u'/'x5t#256').",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_222": {
        "requirement_text": "a JWS MUST use the Flat JSON serialization format (not JWS Compact Serialization and not General JWS JSON Serialization Syntax), and only the Edwards-curve Digital Signature Algorithm (ECDSA) with Curve448 (algorithm \"EdDSA\") [227] [228] signature method is used.",
        "document_section": "5.10",
        "description": "A JWS MUST use the Flat JSON serialization format. The only acceptable signature method is the Edwards-curve Digital Signature Algorithm (ECDSA) with Curve448 ('EdDSA').",
        "test_id": "",
        "subtests": []
    }
}