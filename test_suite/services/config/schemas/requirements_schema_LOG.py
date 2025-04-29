REQUIREMENTS_SCHEMA = {
    "RQ_LOG_002": {
        "requirement_text": "(Versions entry point result parameters)",
        "document_section": "4.12",
        "description": "The Versions entry point should define result parameters for the Logging Web Service.",
        "test_id": "LOG_001",
        "subtests": []
    },
    "RQ_LOG_003": {
        "requirement_text": "The Versions entry point of the Logging Web Service MUST include, in the “serviceInfo” parameter, the parameter “requiredAlgorithms” whose value is an array of JWS algorithms (as described in 5.10)",
        "document_section": "4.12",
        "description": "The Logging Web Service's Versions entry must include a \"requiredAlgorithms\" parameter listing JWS algorithms.",
        "test_id": "LOG_001",
        "subtests": []
    },
    "RQ_LOG_004": {
        "requirement_text": "Logging Services MUST implement a Session Recording Protocol (SIPREC - RFC 7866) interface [116] for recording the media and, if provided, the associated metadata.",
        "document_section": "4.12.1",
        "description": "Logging Services must implement SIPREC (RFC 7866) for recording media and metadata.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_005": {
        "requirement_text": "Logging Services MUST provide a Real-time Streaming Protocol (RTSP) interface compliant with RTSP 2.0 (RFC 7826 [98]) to play back the media. RTSP 1.0 MUST NOT be used.",
        "document_section": "4.12.1",
        "description": "Logging Services must support RTSP 2.0 (RFC 7826) for media playback.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_007": {
        "requirement_text": "Each Logging Service FE MUST implement the server-side of the ElementState event notification package.",
        "document_section": "4.12.1",
        "description": "Each Logging Service FE must implement the ElementState event notification server-side.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_008": {
        "requirement_text": "The Logging Service FE MUST promptly report changes in its state to its subscribed elements.",
        "document_section": "4.12.1",
        "description": "Logging Service FE must promptly report state changes to subscribed elements.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_009": {
        "requirement_text": "The set of Logging Service FEs within an NGCS MUST implement the server-side of the ServiceState event notification package for the Logging Service.",
        "document_section": "4.12.1",
        "description": "Logging Service FEs within NGCS must implement the ServiceState event notification server-side.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_010": {
        "requirement_text": "The Logging Service MUST implement the SRS interface.",
        "document_section": "4.12.2",
        "description": "Logging Services must implement the SRS interface.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_016": {
        "requirement_text": "The Logging Service and its SRC interface MUST log the SIPREC Metadata LogEvent (see the LogEvent section for details).",
        "document_section": "4.12.2",
        "description": "The Logging Service and SRC interface must log SIPREC Metadata LogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_022": {
        "requirement_text": "All SRCs and SRSes MUST implement RTCP on the recording session.",
        "document_section": "4.12.2",
        "description": "All SRCs and SRSes must support RTCP during recording sessions.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_024": {
        "requirement_text": "The SRC MUST send wall clock time in sender reports, which MUST be recorded by the SRS.",
        "document_section": "4.12.2",
        "description": "The SRC must send wall clock time in sender reports for recording by the SRS.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_026": {
        "requirement_text": "(common LogEvent prologue (base object/header) table)",
        "document_section": "4.12.3.1",
        "description": "The LogEvent prologue should define the base object/header.",
        "test_id": "LOG_003",
        "subtests": []
    },
    "RQ_LOG_028": {
        "requirement_text": "(LogEvents GET parameters)",
        "document_section": "4.12.3.1.1",
        "description": "LogEvents GET parameters must be specified for event retrieval.",
        "test_id": "LOG_002",
        "subtests": []
    },
    "RQ_LOG_030": {
        "requirement_text": "(LogEvents/{logEventId} GET parameters)",
        "document_section": "4.12.3.1.1",
        "description": "LogEvents/{logEventId} GET parameters should allow retrieving specific events.",
        "test_id": "LOG_004",
        "subtests": []
    },
    "RQ_LOG_032": {
        "requirement_text": "(LogEvents/{logEventId} GET response)",
        "document_section": "4.12.3.1.1",
        "description": "LogEvents/{logEventId} GET responses must return event details.",
        "test_id": "LOG_004",
        "subtests": []
    },
    "RQ_LOG_033": {
        "requirement_text": "(The text in 4.12.3.1.1 applies to 4.12.3.1.3):\n \n When the event is a RecMediaStartEvent, the returned events will have one or more “rtsp” parameters inserted by the Logging Service that MUST be RTSP URIs. The RTSP URI can be used to play back the call session. The “sdp” and “mediaLabel” are also returned to indicate which media stream in the session the event refers to. These “rtsp” parameters MUST NOT refer to media from other SIPREC sessions that recorded the same call. Because the IRR functionality uses this interface, the Logging Service MUST ensure that it can return a usable RTSP URL as soon as recording starts. The Logging Service MUST ensure that any RTSP URL it returns remains valid for at least one hour.",
        "document_section": "4.12.3.1.3",
        "description": "RecMediaStartEvent should return RTSP URIs and media details, valid for one hour.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_034": {
        "requirement_text": "(LogEvents GET response)",
        "document_section": "4.12.3.1.1",
        "description": "LogEvents GET responses should provide necessary event details.",
        "test_id": "LOG_004",
        "subtests": []
    },
    "RQ_LOG_035": {
        "requirement_text": "When the event is a RecMediaStartEvent, the returned events will have one or more “rtsp” parameters inserted by the Logging Service that MUST be RTSP URIs. The RTSP URI can be used to play back the call session. The “sdp” and “mediaLabel” are also returned to indicate which media stream in the session the event refers to. These “rtsp” parameters MUST NOT refer to media from other SIPREC sessions that recorded the same call. Because the IRR functionality uses this interface, the Logging Service MUST ensure that it can return a usable RTSP URL as soon as recording starts. The Logging Service MUST ensure that any RTSP URL it returns remains valid for at least one hour.",
        "document_section": "4.12.3.1.1",
        "description": "RecMediaStartEvent responses should return valid RTSP URIs and media details for at least one hour.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_036": {
        "requirement_text": "(LogEvents POST response)",
        "document_section": "4.12.3.1.2",
        "description": "The LogEvents POST response should confirm and detail the event.",
        "test_id": "LOG_003",
        "subtests": []
    },
    "RQ_LOG_037": {
        "requirement_text": "(.../Conversations GET parameters)",
        "document_section": "4.12.3.2",
        "description": "The /Conversations GET parameters must retrieve conversation data.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_038": {
        "requirement_text": "(.../Conversations GET response)",
        "document_section": "4.12.3.2",
        "description": "The /Conversations GET response should return conversation details.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_039": {
        "requirement_text": "(LogEventIds GET parameters)",
        "document_section": "4.12.3.3",
        "description": "LogEventIds GET parameters should specify event identifiers for retrieval.",
        "test_id": "LOG_005",
        "subtests": []
    },
    "RQ_LOG_041": {
        "requirement_text": "(LogEventIds GET response)",
        "document_section": "4.12.3.3",
        "description": "The LogEventIds GET response must return details of the requested log event identifiers.",
        "test_id": "LOG_005",
        "subtests": []
    },
    "RQ_LOG_042": {
        "requirement_text": "( .../CallIds GET parameters)",
        "document_section": "4.12.3.4",
        "description": "The /CallIds GET parameters should specify call identifiers for event retrieval.",
        "test_id": "LOG_006",
        "subtests": []
    },
    "RQ_LOG_044": {
        "requirement_text": "( .../CallIds GET response)",
        "document_section": "4.12.3.4",
        "description": "The /CallIds GET response should return call-specific event data.",
        "test_id": "LOG_006",
        "subtests": []
    },
    "RQ_LOG_045": {
        "requirement_text": "( .../IncidentIds GET parameters)",
        "document_section": "4.12.3.5",
        "description": "The /IncidentIds GET parameters must specify incident identifiers for event retrieval.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_047": {
        "requirement_text": "( .../IncidentIds GET response)",
        "document_section": "4.12.3.5",
        "description": "The /IncidentIds GET response should return incident-specific event data.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_048": {
        "requirement_text": "( .../AgencyIds GET parameters)",
        "document_section": "4.12.3.6",
        "description": "The /AgencyIds GET parameters should specify agency identifiers for event retrieval.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_050": {
        "requirement_text": "( .../AgencyIds GET response)",
        "document_section": "4.12.3.6",
        "description": "The /AgencyIds GET response should return agency-specific event data.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_054": {
        "requirement_text": "CallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallStartLogEvent members define the attributes for a call start log event.",
        "test_id": "LOG_007",
        "subtests": []
    },
    "RQ_LOG_055": {
        "requirement_text": "CallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallEndLogEvent members define the attributes for a call end log event.",
        "test_id": "LOG_007",
        "subtests": []
    },
    "RQ_LOG_058": {
        "requirement_text": "RecCallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecCallStartLogEvent members define the attributes for a recorded call start event.",
        "test_id": "LOG_007",
        "subtests": []
    },
    "RQ_LOG_059": {
        "requirement_text": "RecCallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecCallEndLogEvent members define the attributes for a recorded call end event.",
        "test_id": "LOG_007",
        "subtests": []
    },
    "RQ_LOG_063": {
        "requirement_text": "CallTransferLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallTransferLogEvent members define the attributes for a call transfer event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_065": {
        "requirement_text": "RouteLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RouteLogEvent members define the attributes for a call routing event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_067": {
        "requirement_text": "MediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MediaStartLogEvent members define the attributes for the start of media in a call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_069": {
        "requirement_text": "MediaEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MediaEndLogEvent members define the attributes for the end of media in a call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_071": {
        "requirement_text": "RecMediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecMediaStartLogEvent members define the attributes for the start of recorded media.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_073": {
        "requirement_text": "RecMediaEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecMediaEndLogEvent members define the attributes for the end of recorded media.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_074": {
        "requirement_text": "RecordingFailedLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecordingFailedLogEvent members define the attributes for a failed recording event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_077": {
        "requirement_text": "MessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MessageLogEvent members define the attributes for a message event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_080": {
        "requirement_text": "AdditionalAgencyLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalAgencyLogEvent members define the attributes for events related to additional agencies.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_083": {
        "requirement_text": "IncidentMergeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentMergeLogEvent members define the attributes for an incident merge event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_085": {
        "requirement_text": "IncidentUnMergeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentUnMergeLogEvent members define the attributes for an incident unmerge event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_087": {
        "requirement_text": "IncidentSplitLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentSplitLogEvent members define the attributes for an incident split event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_089": {
        "requirement_text": "IncidentLinkLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentLinkLogEvent members define the attributes for an incident link event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_091": {
        "requirement_text": "IncidentUnLinkLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentUnLinkLogEvent members define the attributes for an incident unlink event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_093": {
        "requirement_text": "IncidentClearLogEvent",
        "document_section": "4.12.3.7",
        "description": "IncidentClearLogEvent defines the attributes for an incident clear event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_095": {
        "requirement_text": "IncidentReopenLogEvent",
        "document_section": "4.12.3.7",
        "description": "IncidentReopenLogEvent defines the attributes for an incident reopen event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_097": {
        "requirement_text": "LostQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LostQueryLogEvent members define the attributes for a lost query event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_100": {
        "requirement_text": "LostResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LostResponseLogEvent members define the attributes for a lost response event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_105": {
        "requirement_text": "CallSignalingMessageLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "CallSignalingMessageLogEvent members define the attributes for a call signaling message event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_109": {
        "requirement_text": "SipRecMetadataLogEvent members",
        "document_section": "4.12.3.7",
        "description": "SipRecMetadataLogEvent members define the attributes for metadata related to SIPREC sessions.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_113": {
        "requirement_text": "NonRtpMediaMessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "NonRtpMediaMessageLogEvent members define the attributes for non-RTP media message events.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_116": {
        "requirement_text": "AliLocationQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AliLocationQueryLogEvent members define the attributes for a location query event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_121": {
        "requirement_text": "AliLocationResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AliLocationResponseLogEvent members define the attributes for a location response event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_123": {
        "requirement_text": "MalformedMessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MalformedMessageLogEvent members define the attributes for malformed message events.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_128": {
        "requirement_text": "EidoLogEvent members",
        "document_section": "4.12.3.7",
        "description": "EidoLogEvent members define the attributes for EIDO-related log events.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_133": {
        "requirement_text": "ElementStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "ElementStateChangeLogEvent members define the attributes for an element state change event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_136": {
        "requirement_text": "ServiceStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "ServiceStateChangeLogEvent members define the attributes for a service state change event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_140": {
        "requirement_text": "AdditionalDataQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataQueryLogEvent members define the attributes for additional data query events.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_145": {
        "requirement_text": "AdditionalDataResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataResponseLogEvent members define the attributes for additional data response events.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_149": {
        "requirement_text": "LocationQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LocationQueryLogEvent members define the attributes for a location query event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_153": {
        "requirement_text": "LocationResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LocationResponseLogEvent members define the attributes for a location response event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_156": {
        "requirement_text": "CallStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallStateChangeLogEvent members define the attributes for a call state change event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_159": {
        "requirement_text": "GatewayCallLogEvent members",
        "document_section": "4.12.3.7",
        "description": "GatewayCallLogEvent members define the attributes for a gateway call event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_162": {
        "requirement_text": "HookflashLogEvent member",
        "document_section": "4.12.3.7",
        "description": "HookflashLogEvent members define the attributes for a hookflash-related log event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_164": {
        "requirement_text": "LegacyDigitsLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LegacyDigitsLogEvent members define the attributes for legacy digit-related log events.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_168": {
        "requirement_text": "AgentStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AgentStateChangeLogEvent members define the attributes for an agent state change event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_172": {
        "requirement_text": "QueueStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "QueueStateChangeLogEvent members define the attributes for a queue state change event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_175": {
        "requirement_text": "KeepAliveFailureLogEvent members",
        "document_section": "4.12.3.7",
        "description": "KeepAliveFailureLogEvent members define the attributes for a keep-alive failure event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_177": {
        "requirement_text": "RouteRuleMsgLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RouteRuleMsgLogEvent members define the attributes for a route rule message event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_179": {
        "requirement_text": "PolicyChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "PolicyChangeLogEvent members define the attributes for a policy change event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_181": {
        "requirement_text": "VersionsLogEvent members",
        "document_section": "4.12.3.7",
        "description": "VersionsLogEvent members define the attributes for a versions log event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LOG_185": {
        "requirement_text": "SubscribeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "SubscribeLogEvent members define the attributes for a subscribe log event.",
        "test_id": "",
        "subtests": []
    }
}