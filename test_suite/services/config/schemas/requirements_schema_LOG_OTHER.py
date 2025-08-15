REQUIREMENTS_SCHEMA = {
    "RQ_LOG-OTHER_001": {
        "requirement_text": "All forms of media described in this document MUST be logged (see the Media section for details)",
        "document_section": "4.12",
        "description": "All forms of media described must be logged, as detailed in the Media section.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_006": {
        "requirement_text": "Clients to the Logging Service MUST support logging to at least two Logging Services",
        "document_section": "4.12.1",
        "description": "Clients to the Logging Service must support logging to at least two Logging Services.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_011": {
        "requirement_text": "at least one element in the call path MUST deploy the SRC interface.",
        "document_section": "4.12.2",
        "description": "At least one element in the call path must deploy the SRC interface.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_012": {
        "requirement_text": "All Bridge elements (Section 5.7), Gateway elements (Section 7), BCF elements that anchor media, and PSAP Call Handling elements, MUST implement the SRC interface.",
        "document_section": "4.12.2",
        "description": "All Bridge, Gateway, BCF, and PSAP Call Handling elements must implement the SRC interface.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_013": {
        "requirement_text": "Overall ESInet design determines which elements may be provisioned to record. Such designs MUST assure that media are always recorded, even when calls are handled out-of-area, which may make different assumptions than the local ESInet on such matters.",
        "document_section": "4.12.2",
        "description": "ESInet design determines which elements record media, ensuring that media is always recorded even for out-of-area calls.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_014": {
        "requirement_text": "Elements that implement the SRC interface MUST be capable of supporting redundant implementations of the SRS (RFC 7866) [116]",
        "document_section": "4.12.2",
        "description": "Elements with the SRC interface must support redundant implementations of the SRS (RFC 7866).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_015": {
        "requirement_text": "Elements that implement the SRC interface MUST be capable of supporting redundant implementations of the SRS (RFC 7866) [116] and MUST insert the Call Identifier and Incident Tracking Identifier (Call-Info header fields) defined in this document into the INVITE sent to the Logging Service.",
        "document_section": "4.12.2",
        "description": "SRC interface elements must support redundant implementations of the SRS and include Call Identifier and Incident Tracking Identifier in the SIPREC INVITE and associated SiprecMetadata LogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_017": {
        "requirement_text": "When an SRC sends SIPREC Metadata, it MUST generate a SiprecMetadata LogEvent to the Logging Service.",
        "document_section": "4.12.2",
        "description": "When an SRC sends SIPREC Metadata, it must generate a SiprecMetadata LogEvent to the Logging Service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_018": {
        "requirement_text": "The SRC MUST include the CallId and IncidentId for the emergency call being recorded in the SIPREC INVITE it generates and when generating an associated SiprecMetadata LogEvent.",
        "document_section": "4.12.2",
        "description": "The SRC must include CallId and IncidentId for the emergency call in the SIPREC INVITE and associated SiprecMetadata LogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_019": {
        "requirement_text": "Each emergency call (that is, each Communication Session), MUST result in a separate Recording Session. More than one Recording Session MAY be logged for a single call.",
        "document_section": "4.12.2",
        "description": "Each emergency call must result in a separate Recording Session, with more than one possible for a single call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_020": {
        "requirement_text": "Each emergency call (that is, each Communication Session), MUST result in a separate Recording Session.",
        "document_section": "4.12.2",
        "description": "Each emergency call must result in a separate Recording Session.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_021": {
        "requirement_text": "SRCs MUST support recording of media to at least two SRSes.",
        "document_section": "4.12.2",
        "description": "SRCs must support recording of media to at least two SRSes.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_023": {
        "requirement_text": "All SRCs and SRSes MUST implement RTCP on the recording session.",
        "document_section": "4.12.2",
        "description": "All SRCs and SRSes must implement RTCP on the recording session.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_025": {
        "requirement_text": "The SRC MUST send wall clock time in sender reports.",
        "document_section": "4.12.2",
        "description": "The SRC must send wall clock time in sender reports.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_027": {
        "requirement_text": "(common LogEvent prologue (base object/header) table)",
        "document_section": "4.12.3.1",
        "description": "Common LogEvent prologue (base object/header) table applies to all LogEvents.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_029": {
        "requirement_text": "(LogEvents GET parameters)",
        "document_section": "4.12.3.1.1",
        "description": "Parameters for the LogEvents GET request must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_031": {
        "requirement_text": "(LogEvents/{logEventId} GET parameters)",
        "document_section": "4.12.3.1.1",
        "description": "Parameters for the LogEvents/{logEventId} GET request must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_040": {
        "requirement_text": "(LogEventIds GET parameters)",
        "document_section": "4.12.3.3",
        "description": "Parameters for the LogEventIds GET request must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_043": {
        "requirement_text": "( .../CallIds GET parameters)",
        "document_section": "4.12.3.4",
        "description": "Parameters for the CallIds GET request must be defined (Section 4.12.3.4).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_046": {
        "requirement_text": "( .../IncidentIds GET parameters)",
        "document_section": "4.12.3.5",
        "description": "Parameters for the IncidentIds GET request must be defined (Section 4.12.3.5).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_049": {
        "requirement_text": "( .../AgencyIds GET parameters)",
        "document_section": "4.12.3.6",
        "description": "Parameters for the AgencyIds GET request must be defined (Section 4.12.3.6).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_051": {
        "requirement_text": "The replicator MUST replicate LogEvents exactly as they were received without modifying any field.",
        "document_section": "4.12.3.9",
        "description": "The replicator must replicate LogEvents exactly as they were received without modifying any field (Section 4.12.3.9).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_052": {
        "requirement_text": "All agencies and NG9 1 1 functional elements MUST have access to a conformant Logging Service and log all relevant events in that service.",
        "document_section": "4.12.4",
        "description": "All agencies and NG9-1-1 functional elements must have access to a conformant Logging Service and log all relevant events in that service (Section 4.12.4).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_053": {
        "requirement_text": "Each element that is call stateful logs the beginning and end of its processing of a call, including non-interactive calls, with Start Call and End Call events. Elements that log CallStartLogEvent/CallEndLogEvent MUST also log the actual SIP message with CallSignalingMessageLogEvent for SIP parts of a call and GatewayCallLogEvent for TDM parts of a call. For CallStartLogEvent and CallEndLogEvent, the Timestamp MUST be the time the INVITE, MESSAGE, BYE or equivalents to these messages, or the final status code was received or sent by the element logging the event.",
        "document_section": "4.12.3.7",
        "description": "Call stateful elements must log the beginning and end of call processing, including non-interactive calls, and log SIP or TDM message details with the appropriate events.",
        "test_id": "LOG_008",
        "subtests": []
    },
    "RQ_LOG-OTHER_056": {
        "requirement_text": "CallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallStartLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "LOG_008",
        "subtests": []
    },
    "RQ_LOG-OTHER_057": {
        "requirement_text": "CallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallEndLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "LOG_008",
        "subtests": []
    },
    "RQ_LOG-OTHER_060": {
        "requirement_text": "RecCallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecCallStartLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_061": {
        "requirement_text": "RecCallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecCallEndLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_062": {
        "requirement_text": "When a call is transferred, the transfer is logged by the transferor (the entity that had the call prior to transferring it). The transfer target URI is logged in a target member. Elements that log CallTransferLogEvent MUST also log the actual SIP targetCallIdSIP member that contains the SIP CallId of the new session with the transfer target, when known. Note that the PSAP may not know this CallId, but the bridge would.",
        "document_section": "4.12.3.7",
        "description": "Call transfers must be logged by the transferor with the transfer target URI, including the SIP CallId of the new session if known.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_064": {
        "requirement_text": "CallTransferLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallTransferLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_066": {
        "requirement_text": "RouteLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RouteLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_068": {
        "requirement_text": "MediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MediaStartLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_070": {
        "requirement_text": "MediaEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MediaEndLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_072": {
        "requirement_text": "RecMediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecMediaStartLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_075": {
        "requirement_text": "RecordingFailedLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecordingFailedLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_076": {
        "requirement_text": "MessageLogEvent states: Elements that log Message MUST also log the actual SIP message with CallSignalingMessageLogEvent.",
        "document_section": "",
        "description": "MessageLogEvent: Elements logging Message events must also log the SIP message with CallSignalingMessageLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_078": {
        "requirement_text": "MessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MessageLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_079": {
        "requirement_text": "MessageLogEvent: Elements that log Message MUST also log the actual SIP message with CallSignalingMessageLogEvent.",
        "document_section": "4.12.3.7",
        "description": "MessageLogEvent: Elements logging Message events must also log the SIP message with CallSignalingMessageLogEvent (Section 4.12.3.7).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_081": {
        "requirement_text": "AdditionalAgencyLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalAgencyLogEvent members must include specific details as outlined in Section 4.12.3.7.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_082": {
        "requirement_text": "When an agency becomes aware that another agency may be involved, in any way, with a call, it MUST log an AdditionalAgencyLogEvent.",
        "document_section": "4.12.3.7",
        "description": "When an agency becomes aware that another agency may be involved with a call, it must log an AdditionalAgencyLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_084": {
        "requirement_text": "IncidentMergeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentMergeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_086": {
        "requirement_text": "IncidentUnMergeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentUnMergeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_088": {
        "requirement_text": "IncidentSplitLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentSplitLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_090": {
        "requirement_text": "IncidentLinkLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentLinkLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_092": {
        "requirement_text": "IncidentUnLinkLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentUnLinkLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_094": {
        "requirement_text": "IncidentClearLogEvent",
        "document_section": "4.12.3.7",
        "description": "IncidentClearLogEvent must be logged when an incident is cleared.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_096": {
        "requirement_text": "IncidentReopenLogEvent",
        "document_section": "4.12.3.7",
        "description": "IncidentReopenLogEvent must be logged when an incident is reopened.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_098": {
        "requirement_text": "LostQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LostQueryLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_099": {
        "requirement_text": "LostQueryLogEvent: A “queryId” member is used to relate the request to the response. The id is generated locally, MUST be globally unique",
        "document_section": "4.12.3.7",
        "description": "LostQueryLogEvent: A \"queryId\" member relates the request to the response, and must be globally unique.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_101": {
        "requirement_text": "LostResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LostResponseLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_102": {
        "requirement_text": "LostResponseLogEvent: A “responseId” member is used to relate the request to the response, and MUST match the id used in the LostQueryLogEvent.",
        "document_section": "4.12.3.7",
        "description": "LostResponseLogEvent: A \"responseId\" member relates the request to the response, matching the \"queryId\" in LostQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_103": {
        "requirement_text": "CallSignalingMessageLogEvent: An element MUST always log messages it receives (with “direction” set to “incoming”).",
        "document_section": "4.12.3.7",
        "description": "CallSignalingMessageLogEvent: An element must always log incoming messages with \"direction\" set to \"incoming.\"",
        "test_id": "LOG_008",
        "subtests": []
    },
    "RQ_LOG-OTHER_104": {
        "requirement_text": "CallSignalingMessageLogEvent: An element MUST log outgoing messages it originates.",
        "document_section": "4.12.3.7",
        "description": "CallSignalingMessageLogEvent: An element must log outgoing messages it originates.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_106": {
        "requirement_text": "CallSignalingMessageLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "CallSignalingMessageLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_107": {
        "requirement_text": "SipRecMetadataLogEvent: The SRS MUST create LogEvents for any metadata received via the SIPREC metadata interface (RFC 7865) [117]. It does this by logging a SIPRECMetadataLogEvent to itself",
        "document_section": "4.12.3.7",
        "description": "SipRecMetadataLogEvent: The SRS must create LogEvents for metadata received via the SIPREC metadata interface and log a SIPRECMetadata LogEvent to itself.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_108": {
        "requirement_text": "SipRecMetadataLogEvent: The SRS MUST fill in the header fields for which the values are known, such as the CallId and IncidentId supplied by the Session Recording Client.",
        "document_section": "4.12.3.7",
        "description": "SipRecMetadataLogEvent: The SRS must fill in known header fields, such as CallId and IncidentId, in the metadata log event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_110": {
        "requirement_text": "SipRecMetadataLogEvent members",
        "document_section": "4.12.3.7",
        "description": "SipRecMetadataLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_111": {
        "requirement_text": "NonRtpMediaMessageLogEvent: An element MUST always log messages it receives (with “direction” set to “incoming”).",
        "document_section": "4.12.3.7",
        "description": "NonRtpMediaMessageLogEvent: An element must log incoming media messages with \"direction\" set to \"incoming.\"",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_112": {
        "requirement_text": "NonRtpMediaMessageLogEvent: An element MUST log outgoing messages it originates.",
        "document_section": "4.12.3.7",
        "description": "NonRtpMediaMessageLogEvent: An element must log outgoing media messages it originates.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_114": {
        "requirement_text": "NonRtpMediaMessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "NonRtpMediaMessageLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_115": {
        "requirement_text": "AliLocationQueryLogEvent: A “queryId” member is used to relate the request to the response. The id is generated locally, MUST be globally unique",
        "document_section": "4.12.3.7",
        "description": "AliLocationQueryLogEvent: A \"queryId\" member is used to relate the request to the response, and must be globally unique.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_117": {
        "requirement_text": "AliLocationQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AliLocationQueryLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_118": {
        "requirement_text": "An LSRG MUST log the response it sends to or receives from its query to an ALI server with the AliLocationResponseLogEvent.",
        "document_section": "4.12.3.7",
        "description": "An LSRG must log the response to or from an ALI server using the AliLocationResponseLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_119": {
        "requirement_text": "AliLocationResponseLogEvent: An LPG MUST also use this LogEvent when it responds to an ALI query from the legacy PSAP.",
        "document_section": "4.12.3.7",
        "description": "AliLocationResponseLogEvent: An LPG must log this event when responding to an ALI query from a legacy PSAP.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_120": {
        "requirement_text": "AliLocationResponseLogEvent: A “responseId” member is used to relate the request to the response and MUST match the id used in the AliLocationQueryLogEvent.",
        "document_section": "4.12.3.7",
        "description": "AliLocationResponseLogEvent: A \"responseId\" member is used to relate the request to the response, and must match the \"queryId\" used in AliLocationQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_122": {
        "requirement_text": "AliLocationResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AliLocationResponseLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_124": {
        "requirement_text": "MalformedMessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MalformedMessageLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_125": {
        "requirement_text": "EidoLogEvent: Any element that sends or receives an Emergency Incident Data Document [111] MUST log it with the EidoLogEvent.",
        "document_section": "4.12.3.7",
        "description": "EidoLogEvent: Elements sending or receiving an Emergency Incident Data Document must log it using the EidoLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_126": {
        "requirement_text": "EidoLogEvent: If an EIDO is sent or received by reference, the EIDO URI MUST be logged with a “reference” member.",
        "document_section": "4.12.3.7",
        "description": "EidoLogEvent: If an EIDO is sent or received by reference, the EIDO URI must be logged with a \"reference\" member.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_127": {
        "requirement_text": "EidoLogEvent: When the URI is dereferenced, another EIDOLogEvent MUST be created with the “reference” and “body” by both the client and server.",
        "document_section": "4.12.3.7",
        "description": "EidoLogEvent: When the URI is dereferenced, a new EidoLogEvent must be created with both \"reference\" and \"body\" members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_129": {
        "requirement_text": "EidoLogEvent members",
        "document_section": "4.12.3.7",
        "description": "EidoLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_130": {
        "requirement_text": "DiscrepancyReportLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "DiscrepancyReportLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_131": {
        "requirement_text": "DiscrepancyReportLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "DiscrepancyReportLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_132": {
        "requirement_text": "ElementStateChangeLogEvent: When an element sends a notification of state change as described in the Element State section of this document, it MUST log the ElementStateChangeLogEvent.",
        "document_section": "4.12.3.7",
        "description": "ElementStateChangeLogEvent: When an element notifies a state change, it must log an ElementStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_134": {
        "requirement_text": "ElementStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "ElementStateChangeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_135": {
        "requirement_text": "ServiceStateChangeLogEvent: When a Service sends a notification of state change as described in the Service State section of this document, which includes Security Posture, it MUST log the ServiceStateChangeLogEvent.",
        "document_section": "4.12.3.7",
        "description": "ServiceStateChangeLogEvent: When a service notifies a state change, including security posture, it must log a ServiceStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_137": {
        "requirement_text": "ServiceStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "ServiceStateChangeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_138": {
        "requirement_text": "AdditionalDataQueryLogEvent: A server for AdditionalData that is located inside an ESInet, or LNG, or LSRG operated by, or on behalf of, a 9-1-1 Authority, MUST log all queries it receives.",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataQueryLogEvent: Servers for AdditionalData within an ESInet, LNG, or LSRG must log all queries received.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_139": {
        "requirement_text": "AdditionalDataQueryLogEvent: A “queryId” member is used to relate the request to the response. The id is generated locally, MUST be globally unique",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataQueryLogEvent: A \"queryId\" member must be globally unique and relate the request to the response.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_141": {
        "requirement_text": "AdditionalDataQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataQueryLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_142": {
        "requirement_text": "AdditionalDataResponseLogEvent: Any Additional Data that is retrieved by a client MUST be logged using the AdditionalDataResponseLogEvent.",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataResponseLogEvent: Any retrieved Additional Data must be logged using the AdditionalDataResponseLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_143": {
        "requirement_text": "AdditionalDataResponseLogEvent: A server for AdditionalData that is located inside an ESInet, and an LNG, LPG, or LSRG operated by, or on behalf of, a 9 1 1 Authority, MUST log all responses it sends.",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataResponseLogEvent: Servers within an ESInet, LNG, or LSRG must log all responses sent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_144": {
        "requirement_text": "AdditionalDataResponseLogEvent: A “responseId” member is used to relate the request to the response and MUST match the id used in the AdditionalDataQueryLogEvent.",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataResponseLogEvent: A \"responseId\" member must match the \"queryId\" in AdditionalDataQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_146": {
        "requirement_text": "AdditionalDataResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataResponseLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_147": {
        "requirement_text": "LocationQueryLogEvent: Logging these is OPTIONAL at the client and REQUIRED at the server if the server is located inside an ESInet, or is an LNG or LSRG operated by, or on behalf of, a 9-1-1 Authority.",
        "document_section": "4.12.3.7",
        "description": "LocationQueryLogEvent: Logging is optional at the client but required at the server within an ESInet or LSRG operated on behalf of a 9-1-1 Authority.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_148": {
        "requirement_text": "LocationQueryLogEvent: A “queryId” member is used to relate the request or subscription to the response or notifications. The id is generated locally, MUST be globally unique,",
        "document_section": "4.12.3.7",
        "description": "LocationQueryLogEvent: A \"queryId\" member must be globally unique and relate the request or subscription to the response or notifications.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_150": {
        "requirement_text": "LocationQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LocationQueryLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_151": {
        "requirement_text": "LocationResponseLogEvent: All clients and servers, if the server is located inside an ESInet, or is an LNG or LSRG operated by, or on behalf of, a 9-1-1 Authority, MUST log responses.",
        "document_section": "4.12.3.7",
        "description": "LocationResponseLogEvent: Clients and servers within an ESInet, LNG, or LSRG must log responses.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_152": {
        "requirement_text": "LocationResponseLogEvent: A “responseId” member is used to relate the request or subscription to the response or notifications and MUST match the id used in the LocationQueryLogEvent.",
        "document_section": "4.12.3.7",
        "description": "LocationResponseLogEvent: A \"responseId\" member must match the \"queryId\" in LocationQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_154": {
        "requirement_text": "LocationResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LocationResponseLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_155": {
        "requirement_text": "CallStateChangeLogEvent MUST be logged by all elements that change the state of the call, which would include a bridge and all entities within the ESInet that request bridge actions when an emergency call is on a bridge.",
        "document_section": "4.12.3.7",
        "description": "CallStateChangeLogEvent must be logged by all elements that change the state of a call, including bridges and entities requesting bridge actions.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_157": {
        "requirement_text": "CallStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallStateChangeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_158": {
        "requirement_text": "GatewayCallLogEvent: It contains the following parameters which are OPTIONAL, but MUST be included if known:",
        "document_section": "4.12.3.7",
        "description": "GatewayCallLogEvent: Contains optional parameters, but must include them if known.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_160": {
        "requirement_text": "GatewayCallLogEvent members",
        "document_section": "4.12.3.7",
        "description": "GatewayCallLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_161": {
        "requirement_text": "HookflashLogEvent: An identifier for the line on which the event occurred is included in a “lineId” member, which is OPTIONAL but MUST be provided if known.",
        "document_section": "4.12.3.7",
        "description": "HookflashLogEvent: Includes a \"lineId\" member, which is optional but must be provided if known.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_163": {
        "requirement_text": "HookflashLogEvent member",
        "document_section": "4.12.3.7",
        "description": "HookflashLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_165": {
        "requirement_text": "LegacyDigitsLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LegacyDigitsLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_166": {
        "requirement_text": "AgentStateChangeLogEvent:If the device whose state has changed is not the element identified in the header field, the identifier of the device MUST be included in a “deviceID” member.",
        "document_section": "4.12.3.7",
        "description": "AgentStateChangeLogEvent: If the device's state change is not identified in the header, the device must be included in a \"deviceID\" member.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_167": {
        "requirement_text": "AgentStateChangeLogEvent: All elements supporting agents MUST support the “primaryAgentState”",
        "document_section": "4.12.3.7",
        "description": "AgentStateChangeLogEvent: Elements supporting agents must support \"primaryAgentState.\"",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_169": {
        "requirement_text": "AgentStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AgentStateChangeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_170": {
        "requirement_text": "A queue manager MUST log a change in the state of the queue with the QueueStateChangeLogEvent.",
        "document_section": "4.12.3.7",
        "description": "A queue manager must log state changes with the QueueStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_171": {
        "requirement_text": "QueueStateChangeLogEvent: Elements that receive changes in QueueState MAY log receipt of such changes and MUST log a state change to “unreachable”.",
        "document_section": "4.12.3.7",
        "description": "QueueStateChangeLogEvent: Elements may log receipt of changes and must log when the state changes to \"unreachable.\"",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_173": {
        "requirement_text": "QueueStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "QueueStateChangeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_174": {
        "requirement_text": "KeepAliveFailureLogEvent: Malformed, invalid, or responses not received from the other element MUST be logged in a “responseStatus” member that contains text and a status code from the Status Codes Registry (Section 10.29). There is a TimeOut status in that registry that is used for a timeout failure of OPTIONS.",
        "document_section": "4.12.3.7",
        "description": "KeepAliveFailureLogEvent: Invalid or missing responses must be logged with a \"responseStatus\" member containing text and a status code.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_176": {
        "requirement_text": "KeepAliveFailureLogEvent members",
        "document_section": "4.12.3.7",
        "description": "KeepAliveFailureLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_178": {
        "requirement_text": "RouteRuleMsgLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RouteRuleMsgLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_180": {
        "requirement_text": "PolicyChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "PolicyChangeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_182": {
        "requirement_text": "VersionsLogEvent members",
        "document_section": "4.12.3.7",
        "description": "VersionsLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_183": {
        "requirement_text": "SubscribeLogEvent: The Server MUST log this event",
        "document_section": "4.12.3.7",
        "description": "SubscribeLogEvent: The server must log this event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_184": {
        "requirement_text": "SubscribeLogEvent: The id is generated locally, MUST be globally unique",
        "document_section": "4.12.3.7",
        "description": "SubscribeLogEvent: The id is generated locally and must be globally unique.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG-OTHER_186": {
        "requirement_text": "SubscribeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "SubscribeLogEvent members must be defined.",
        "test_id": "",
        "subtests": []
    }
}