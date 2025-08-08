REQUIREMENTS_SCHEMA = {
    "RQ_BCF_001": {
        "requirement_text": "The BCF, as the first active SIP element in the path of an emergency call, MUST add to the call the emergency-Call Identifier, emergency-Incident Tracking Identifier and a SIP Resource-Priority header field with a value from the “esnet” namespace (if not already present).",
        "document_section": "4.1.2",
        "description": "The BCF must add emergency identifiers and a SIP Resource-Priority header if missing when handling an emergency call.",
        "test_id": "BCF_001",
        "subtests": []
    },
    "RQ_BCF_045": {
        "requirement_text": "The form of a Call Identifier is a Uniform Resource Name (URN) (RFC 2141) [112] formed by the prefix “urn:emergency:uid:callid:”, a unique string containing alpha and/or numeric characters, the “:” character, and the Element Identifier of the element that first handled the call. The unique string portion of the Call Identifier MUST be unique for each call the element handles over time. The length of the unique string portion of the Call Identifier MUST be a string of 10 to 32 characters.",
        "document_section": "2.1.6",
        "description": "The Call Identifier is a URN with a unique string and the element's identifier, 10-32 characters long.",
        "test_id": "BCF_001",
        "subtests": ["Stimulus and Output messages comparison","Emergency Call Identifier header","Emergency Call Identifier URN","Emergency Call Identifier String ID","Emergency Call Identifier FQDN"]
    },
    "RQ_BCF_046": {
        "requirement_text": "The form of an Incident Tracking Identifier is a URN formed by the prefix “urn:emergency:uid:incidentid:”, a unique string containing alpha and/or numeric characters, the “:” character, and the Element Identifier of the entity that first declared the incident. For example, “urn:emergency:uid:incidentid:a56e556d871:bcf.state.pa.us” is a properly formatted Incident Tracking Identifier. The string MUST be unique for each Incident the element handles over time. The length of the unique string portion of the Incident Tracking Identifier MUST be a string of 10 to 32 characters.",
        "document_section": "2.1.7",
        "description": "The Incident Tracking Identifier is a URN with a unique string and the element's identifier, 10-32 characters long.",
        "test_id": "BCF_001",
        "subtests": ["Stimulus and Output messages comparison","Incident Tracking Identifier URN","Incident Tracking Identifier String ID","Incident Tracking Identifier FQDN"]
    },
    "RQ_BCF_002": {
        "requirement_text": "NG9‑1‑1 elements that process 9‑1‑1 calls MUST accept calls that do not strictly follow the SIP standards. As long as the messages can be parsed, and the method discerned, at least the first SIP element (the BCF) MUST be able to accept the call and forward the call onward (see Section 4.1) Support for the following SIP Methods is summarized and specified in the following table: (See underlying table)",
        "document_section": "3.1.1",
        "description": "NG9-1-1 elements must accept calls not strictly following SIP standards if they can be parsed, with the BCF forwarding the call.",
        "test_id": "BCF_001",
        "subtests": []
    },
    "RQ_BCF_003": {
        "requirement_text": "BCFs[1] MUST police Resource-Priority of incoming SIP calls when the value comes from the “esnet” namespace. Any other namespace is ignored. BCFs MUST add a Resource-Priority header with an appropriate value from the “esnet” namespace if it is not present and should be included. BCFs MUST change or delete a value that is present on an incoming call that appears to be invalid or illegitimate.",
        "document_section": "3.1.7 & 4.1.2",
        "description": "BCFs must enforce Resource-Priority on incoming SIP calls from the \"esnet\" namespace and add or modify it if necessary.",
        "test_id": "BCF_001",
        "subtests": ["Stimulus and Output messages comparison","Resource Priority header"]
    },
    "RQ_BCF_004": {
        "requirement_text": "All SIP proxy servers in the ESInet/NGCS MUST implement Resource-Priority and process calls in priority order when a queue of calls is waiting for service at the proxy server and, when needed, preempt lower priority calls",
        "document_section": "3.1.7",
        "description": "SIP proxy servers in the ESInet/NGCS must prioritize calls based on Resource-Priority, preempting lower-priority calls when needed.",
        "test_id": "SIP_002",
        "subtests": []
    },
    "RQ_BCF_005": {
        "requirement_text": "BCFs MUST add a Resource-Priority header with an appropriate value from the “esnet” namespace if it is not present and should be included.",
        "document_section": "3.1.7",
        "description": "BCFs must add a Resource-Priority header if missing and should include it if required.",
        "test_id": "BCF_001",
        "subtests": ["Stimulus and Output messages comparison","Resource Priority header"]
    },
    "RQ_BCF_006": {
        "requirement_text": "BCFs MUST change or delete a value that is present on an incoming call that appears to be invalid or illegitimate.",
        "document_section": "3.1.7",
        "description": "BCFs must modify or delete invalid or illegitimate Resource-Priority values.",
        "test_id": "BCF_001",
        "subtests": ["Verify 'urn:service:sos' in request URI", "Verify 'urn:service:sos' is in 'TO' header field"]
    },
    "RQ_BCF_007": {
        "requirement_text": "Those calls that appear to be emergency calls (such as those To: 911 but without a Request-URI of “urn:service:sos”) MUST be marked with a provisioned Resource-Priority, which defaults to “esnet.1”.",
        "document_section": "3.1.7",
        "description": "Calls that appear to be emergency calls without a \"urn:service:sos\" URI must be marked with a default “esnet.1” Resource-Priority.",
        "test_id": "BCF_002",
        "subtests": ["Stimulus and Output messages comparison","Resource Priority header"]
    },
    "RQ_BCF_008": {
        "requirement_text": "Elements on an ESInet SHALL assume a SIP call entering the ESInet is an emergency call unless it can determine it is something else, such as a call to an administrative number. Even if the call does not have the emergency service URN in the Request-URI, the call SHOULD be assumed to be an emergency call and the Request-URI SHALL be rewritten to urn:service:sos by the BCF or originating ESRP.",
        "document_section": "3.1.7",
        "description": "Elements on an ESInet must assume SIP calls are emergency calls unless otherwise determined, with the URI rewritten to \"urn:service:sos.\"",
        "test_id": "BCF_001",
        "subtests": ["Stimulus and Output messages comparison","Verify 'urn:service:sos' in request URI","Verify 'urn:service:sos' is in 'TO' header field"]
    },
    "RQ_BCF_009": {
        "requirement_text": "The functional elements described in this document MUST support the discrepancy report (DR) function.",
        "document_section": "3.7",
        "description": "Functional elements must support the discrepancy report (DR) function.",
        "test_id": "BCF_002",
        "subtests": []
    },
    "RQ_BCF_047": {
        "requirement_text": "request (If the discrepancy concerns a dialog, the initial INVITE that initiated the dialog )",
        "document_section": "3.7.6",
        "description": "Discrepancies involving dialogs should report the initial INVITE that started the dialog.",
        "test_id": "ALL_001",
        "subtests": []
    },
    "RQ_BCF_013": {
        "requirement_text": "problem (One of the following tokens:\n • InitialTrafficBlocked\n • MidTrafficBlocked\n • BadSDP\n • BadSIP\n • MediaLoss\n • TrafficNotBlockedBadActor\n • TrafficNotBlocked\n • QoS\n • BadCDR\n • TTY\n • Firewall\n • OtherBCF)",
        "document_section": "3.7.6",
        "description": "The \"problem\" parameter includes various issues like traffic blocking, bad SDP, and media loss.",
        "test_id": "ALL_001",
        "subtests": []
    },
    "RQ_BCF_014": {
        "requirement_text": "sosSource (The emergency-source parameter of the dialog request (i.e., the initial INVITE))",
        "document_section": "3.7.6",
        "description": "The \"sosSource\" parameter represents the emergency-source of the dialog request.",
        "test_id": "ALL_001",
        "subtests": []
    },
    "RQ_BCF_015": {
        "requirement_text": "EventTimestamp (Timestamp of event being reported)",
        "document_section": "3.7.6",
        "description": "The \"EventTimestamp\" parameter logs the timestamp of the event being reported.",
        "test_id": "ALL_001",
        "subtests": []
    },
    "RQ_BCF_916": {
        "requirement_text": "packetHeader (For InitialTrafficBlocked, MidTrafficBlocked, TrafficNotBlockedBadActor, TrafficNotBlocked, or Firewall, contains the packet’s header, encoded using base64)",
        "document_section": "3.7.6",
        "description": "The \"packetHeader\" contains the packet's header encoded in base64 for certain issues.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_917": {
        "requirement_text": "The Resolution parameter in a BCF DiscrepancyResolution report contains one of the following tokens:",
        "document_section": "3.7.6",
        "description": "The \"Resolution\" parameter in the DiscrepancyResolution report can be \"DiscrepancyCorrected.\"",
        "test_id": "BCF_002",
        "subtests": []
    },
    "RQ_BCF_018": {
        "requirement_text": "DiscrepancyCorrected",
        "document_section": "3.7.6",
        "description": "The \"Resolution\" parameter in the DiscrepancyResolution report can be \"DiscrepancyCorrected.\"",
        "test_id": "BCF_002",
        "subtests": []
    },
    "RQ_BCF_019": {
        "requirement_text": "PerPolicy",
        "document_section": "3.7.6",
        "description": "The \"Resolution\" can also be \"PerPolicy\" when applicable.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_020": {
        "requirement_text": "NoDiscrepancy",
        "document_section": "3.7.6",
        "description": "\"NoDiscrepancy\" indicates there is no discrepancy detected.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_921": {
        "requirement_text": "OtherResponse",
        "document_section": "3.7.6",
        "description": "\"OtherResponse\" refers to responses not covered by predefined categories.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_022": {
        "requirement_text": "The BCF MUST support the following security related techniques: Prevention, Detection, Reaction.",
        "document_section": "4.1.1",
        "description": "The BCF must support prevention, detection, and reaction for security.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_023": {
        "requirement_text": "Firewalls deployed on the ESInet SHALL meet the following specifications:",
        "document_section": "4.1.1",
        "description": "Firewalls on the ESInet must meet specified security requirements.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_024": {
        "requirement_text": "Provide both application and network layer protection and scanning;",
        "document_section": "4.1.1",
        "description": "Firewalls must provide both application and network layer protection and scanning.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_025": {
        "requirement_text": "Denial of Service (DoS) detection and protection;",
        "document_section": "4.1.1",
        "description": "Firewalls must include Denial of Service (DoS) detection and protection.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_026": {
        "requirement_text": "Provide a mechanism such that malware definitions and patterns can be easily and quickly updated by a national 9 1 1 Computer Emergency Response Team (CERT) or other managing authority;",
        "document_section": "4.1.1",
        "description": "Firewalls must allow quick updates of malware definitions by national 9-1-1 CERT or a managing authority.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_027": {
        "requirement_text": "Capability to receive and update 9 1 1 Malicious Content (NMC) filtering automatically for use by federated firewalls in protecting multiple disparate ESInets.",
        "document_section": "4.1.1",
        "description": "Firewalls must support automatic updates of 9-1-1 Malicious Content (NMC) filtering for federated ESInets.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_028": {
        "requirement_text": "The SBC component of the BCF SHALL support SIP/SDP protocol normalization and/or repair, including adjustments of encodings to a core network profile.",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must support SIP/SDP protocol normalization and repair, adjusting encodings to a core network profile.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_029": {
        "requirement_text": "The SBC component of the BCF SHALL perform NAT traversal for authorized calls/sessions using the SIP protocol. The SBC component MUST be able to recognize that a NAT or NAPT has been performed on Layer 3 but not above and correct the signaling messages for SIP.",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must perform NAT traversal for SIP calls/sessions, correcting signaling messages if a NAT or NAPT is detected.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_030": {
        "requirement_text": "The SBC component of the BCF SHALL enable interworking between networks utilizing IPv4 and networks using IPv6 through the use of dual stacks, selectable for each SBC interface. All valid IPv4 addresses and parameters SHALL be translated to/from the equivalent IPv6 values.",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must support interworking between IPv4 and IPv6 networks using dual-stack interfaces.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_016": {
        "requirement_text": "The SBC component of the BCF SHALL support SIP over the following protocols: TCP, UDP, TLS-over-TCP, and SCTP. Protocols supported MUST be selectable for each SBC interface to external systems.",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must support SIP over TCP, UDP, TLS-over-TCP, and SCTP, selectable for each SBC interface.",
        "test_id": "BCF_003",
        "subtests": []
    },
    "RQ_BCF_017": {
        "requirement_text": "The SBC component of the BCF MUST use TLS with AES-256 or better towards the ESInet.",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must use TLS with AES-256 or better towards the ESInet.",
        "test_id": "BCF_003",
        "subtests": []
    },
    "RQ_BCF_033": {
        "requirement_text": "The SBC component of the BCF SHALL support terminating the IP signaling received from a foreign carrier onto the ESInet address space. The SBC component of the BCF SHALL support B2BUA functions to enable VPN bridging if needed.",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must support terminating IP signaling from foreign carriers to the ESInet, including B2BUA functions for VPN bridging.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_034": {
        "requirement_text": "The SBC component of the BCF SHALL be capable of populating the layer 2 and layer 3 headers/fields, based on call/session type (e.g., 9 1 1 calls) in order to facilitate priority routing of the packets.",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must populate layer 2 and 3 headers based on call/session type for priority routing.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_035": {
        "requirement_text": "The SBC component of the BCF SHALL be capable of producing CDRs based on call/session control information (e.g., SIP/SDP).",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must be capable of producing CDRs based on call/session control information (e.g., SIP/SDP).",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_021": {
        "requirement_text": "All media connections exiting the SBC towards the ESInet MUST be protected against eavesdropping, alteration, and replay using AES-256 or better.",
        "document_section": "4.1.1",
        "description": "All media connections exiting the SBC towards the ESInet must be protected against eavesdropping, alteration, and replay with AES-256 or better.",
        "test_id": "BCF_003",
        "subtests": []
    },
    "RQ_BCF_037": {
        "requirement_text": "An SBC component of the BCF which always anchors media achieves this by accepting any media, with SRTP or not, and MUST protect the media towards the ESInet.",
        "document_section": "4.1.1",
        "description": "The SBC component of the BCF that anchors media must protect all media towards the ESInet, with or without SRTP.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_038": {
        "requirement_text": "An SBC that does not routinely anchor media MUST anchor media for calls entering without sufficient protection (AES-256 or better) and MUST protect the media towards the ESInet.",
        "document_section": "4.1.1",
        "description": "SBCs that don’t routinely anchor media must protect media entering without sufficient encryption (AES-256 or better).",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_039": {
        "requirement_text": "the SBC component of the BCF SHALL perform the following functions:",
        "document_section": "4.1.1",
        "description": "The SBC in the BCF must perform the functions specified in the document.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_040": {
        "requirement_text": "Opening and closing of a pinhole (firewall)",
        "document_section": "4.1.1",
        "description": "Opening and closing a pinhole involves managing firewall rules to allow or block specific traffic.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_041": {
        "requirement_text": "Resource and admission control",
        "document_section": "4.1.1",
        "description": "Resource and admission control ensures the system properly allocates resources and manages call traffic.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_042": {
        "requirement_text": "IP payload processing",
        "document_section": "4.1.1",
        "description": "IP payload processing involves handling the data in network packets for communication.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_043": {
        "requirement_text": "Performance measurement",
        "document_section": "4.1.1",
        "description": "Performance measurement evaluates the effectiveness and efficiency of the system’s operations.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_044": {
        "requirement_text": "The BCF SHALL support an automated interface that allows a downstream element to mark a particular source of a call as a “bad actor” (usually due to receipt of a call that appears to be part of a deliberate attack on the system) and send a message to the BCF notifying it of this marking. Reference the \"BadActors\" interface.",
        "document_section": "4.1.2",
        "description": "The BCF must support an automated interface to mark a source of a call as a \"bad actor\" and notify the system.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_945": {
        "requirement_text": "To facilitate this notification, the BCF SHALL insert a Call-Info header field with a purpose parameter of “emergency-source” in the outgoing INVITE message associated with every call.",
        "document_section": "4.1.2",
        "description": "The BCF must insert a Call-Info header with an \"emergency-source\" parameter in every outgoing INVITE message.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_946": {
        "requirement_text": "calls MUST be marked by the SBC component in a way that allows the recipient to identify the BCF that processed the call. The source-ID is formatted as follows: <unique source-id>@<domain name of BCF> (e.g., “a7123gc42@sbc22.example.net”).",
        "document_section": "4.1.2",
        "description": "Calls must be marked with a source-ID to identify the BCF that processed the call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_947": {
        "requirement_text": "The notification MUST be propagated to all such SBCs. The mechanism for doing so is not specified.",
        "document_section": "4.1.2",
        "description": "Notifications of bad actors must be propagated to all relevant SBCs, though the mechanism is unspecified.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_048": {
        "requirement_text": "Source-Ids MUST be unguessable.",
        "document_section": "4.1.2",
        "description": "Source-Ids must be unguessable to prevent malicious attempts to predict them.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_049": {
        "requirement_text": "If the BCF does not recognize the source-id, it MUST ignore the request.",
        "document_section": "4.1.2",
        "description": "If the BCF doesn’t recognize the source-id, it must ignore the request.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_050": {
        "requirement_text": "BCFs that anchor media MUST implement the Session Recording Client interface defined by SIPREC (RFC 7866) [116].",
        "document_section": "4.1.2",
        "description": "BCFs that anchor media must implement the Session Recording Client (SRC) interface as defined by SIPREC.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_051": {
        "requirement_text": "if the BCF evaluates suspicion, it SHALL insert a Call-Info header field with a purpose parameter of “emergency-CallSuspicion”, with an integer value of 0-100 indicating the call suspicion score where 0 is least suspicious (i.e. no suspicion) and 100 is most suspicious.",
        "document_section": "4.1.2",
        "description": "If the BCF suspects a call, it must insert an \"emergency-CallSuspicion\" parameter indicating the suspicion level in the INVITE message.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_052": {
        "requirement_text": "All Bridge elements (Section 5.7), Gateway elements (Section 7), BCF elements that anchor media, and PSAP Call Handling elements, MUST implement the SRC interface.",
        "document_section": "4.12.2",
        "description": "Bridge, Gateway, BCF elements that anchor media, and PSAP elements must implement the SRC interface.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_053": {
        "requirement_text": "Elements that implement the SRC interface MUST be capable of supporting redundant implementations of the SRS (RFC 7866) [116] and MUST insert the Call Identifier and Incident Tracking Identifier (Call-Info header fields) defined in this document into the INVITE sent to the Logging Service.",
        "document_section": "4.12.2",
        "description": "Elements implementing the SRC interface must support redundant SRS implementations and include Call Identifier and Incident Tracking Identifier in the INVITE to the Logging Service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_054": {
        "requirement_text": "The Logging Service and its SRC interface MUST log the SIPREC Metadata LogEvent (see the LogEvent section for details).",
        "document_section": "4.12.2",
        "description": "The Logging Service and SRC interface must log the SIPREC Metadata LogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_055": {
        "requirement_text": "When an SRC sends SIPREC Metadata, it MUST generate a SiprecMetadata LogEvent to the Logging Service.",
        "document_section": "4.12.2",
        "description": "When sending SIPREC Metadata, the SRC must generate a SiprecMetadata LogEvent to the Logging Service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_056": {
        "requirement_text": "The SRC MUST include the CallId and IncidentId for the emergency call being recorded in the SIPREC INVITE it generates and when generating an associated SiprecMetadata LogEvent.",
        "document_section": "4.12.2",
        "description": "The SRC must include CallId and IncidentId in the SIPREC INVITE and associated SiprecMetadata LogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_057": {
        "requirement_text": "Each emergency call (that is, each Communication Session), MUST result in a separate Recording Session.",
        "document_section": "4.12.2",
        "description": "Each emergency call must result in a separate Recording Session.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_058": {
        "requirement_text": "All SRCs and SRSes MUST implement RTCP on the recording session.",
        "document_section": "4.12.2",
        "description": "All SRCs and SRSes must implement RTCP for the recording session.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_059": {
        "requirement_text": "The SRC MUST send wall clock time in sender reports",
        "document_section": "4.12.2",
        "description": "The SRC must send wall clock time in sender reports.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_060": {
        "requirement_text": "SRCs MUST support recording of media to at least two SRSes.",
        "document_section": "4.12.2",
        "description": "SRCs must support recording media to at least two SRSes.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_061": {
        "requirement_text": "The call MUST go on even if there is no recorder.",
        "document_section": "4.12.2",
        "description": "The call must continue even if there is no recorder available.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_062": {
        "requirement_text": "\"For the purposes of this requirement there was no specific text to reference, but the group agreed that BCFs should always be stateful, with that understanding the group progressed through table 10.21 \"LogEvent\" registry and selected those events that would apply to a stateful BCF.\"",
        "document_section": "4.12.3.7 & 10.21",
        "description": "BCFs should always be stateful, ensuring proper handling of call events based on a stateful design.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_063": {
        "requirement_text": "CallStartLogEvent: Logged by an FE that is call stateful, when it begins processing a call.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The CallStartLogEvent is logged by an element when it begins processing a call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_064": {
        "requirement_text": "CallEndLogEvent: Logged by an element that is call stateful, when its processing of a call ends.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The CallEndLogEvent is logged by an element when it finishes processing a call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_065": {
        "requirement_text": "RecCallStartLogEvent: RecCallStartEvent is identical to CallStartEvent, but is logged by the Logging Service (SRS) and the client (SRC) to denote the beginning of a SIPREC recording session.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "RecCallStartLogEvent is logged by the Logging Service and SRC when a SIPREC recording session starts.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_066": {
        "requirement_text": "RecCallEndLogEvent: RecCallEndEvent is identical to CallEndEvent, but is logged by the Logging Service (SRS) and the client (SRC) to denote the end of a SIPREC recording session.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "RecCallEndLogEvent is logged by the Logging Service and SRC when a SIPREC recording session ends.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_067": {
        "requirement_text": "RouteLogEvent: When a call is transferred, the transfer is logged by the transferor (the entity that had the call prior to transferring it).",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The RouteLogEvent is logged when a call is transferred, by the entity transferring the call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_068": {
        "requirement_text": "MediaStartLogEvent: This event is logged by any media anchor (call recipient for an emergency call, caller for a callback, bridge, or BCF if the BCF anchors media) when at the start of media reception or transmission as appropriate.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The MediaStartLogEvent is logged when media reception or transmission begins, by the media anchor.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_069": {
        "requirement_text": "MediaEndLogEvent: This event is logged by any media anchor (call recipient for an emergency call, caller for a callback, bridge, or BCF if the BCF anchors media) for the communication session media.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The MediaEndLogEvent is logged when media ends in a communication session, by the media anchor.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_070": {
        "requirement_text": "RecMediaStartLogEvent: Both the SRC and SRS log RecMediaStartLogEvent/RecMediaEndLogEvent.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "RecMediaStartLogEvent is logged by both the SRC and SRS when media starts in a SIPREC session.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_071": {
        "requirement_text": "RecMediaEndLogEvent: Both the SRC and SRS log RecMediaStartLogEvent/RecMediaEndLogEvent.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "RecMediaEndLogEvent is logged by both the SRC and SRS when media ends in a SIPREC session.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_072": {
        "requirement_text": "RecordingFailedLogEvent: The Session Recording Client in a SIPREC media recording session is responsible for logging this event.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The RecordingFailedLogEvent is logged when a session recording fails.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_073": {
        "requirement_text": "MessageLogEvent: A SIP Message is logged with a MessageLogEvent",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The MessageLogEvent is used to log any SIP message sent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_074": {
        "requirement_text": "CallSignalingMessageLogEvent: An element MUST log outgoing messages it originates.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The CallSignalingMessageLogEvent logs any outgoing messages an element originates.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_075": {
        "requirement_text": "NonRtpMediaMessageLogEvent: An element MUST log outgoing messages it originates.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The NonRtpMediaMessageLogEvent logs any non-RTP outgoing messages an element originates.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_076": {
        "requirement_text": "MalformedMessageLogEvent: An element that receives a malformed SIP message logs it with the MalformedMessageLogEvent.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The MalformedMessageLogEvent logs any malformed SIP messages an element receives.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_077": {
        "requirement_text": "DiscrepancyReportLogEvent: Any element that sends or receives a Discrepancy Report, or that sends or receives an update (Status, Resolution, etc.) for one, logs what it sent or received with the DiscrepancyReportLogEvent.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The DiscrepancyReportLogEvent logs any discrepancy reports or updates sent or received by an element.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_078": {
        "requirement_text": "ElementStateeChangeLogEvent: When an element sends a notification of state change as described in the Element State section of this document, it MUST log the ElementStateChangeLogEvent.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The ElementStateChangeLogEvent is logged when an element notifies a state change.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_079": {
        "requirement_text": "ServiceStateChangeLogEvent: When a Service sends a notification of state change as described in the Service State section of this document, which includes Security Posture, it MUST log the ServiceStateChangeLogEvent.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The ServiceStateChangeLogEvent logs when a service notifies a state change, including security posture.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_080": {
        "requirement_text": "CallStateChangeLogEvent: CallStateChangeLogEvent MUST be logged by all elements that change the state of the call, which would include a bridge and all entities within the ESInet that request bridge actions when an emergency call is on a bridge.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The CallStateChangeLogEvent is logged when an element changes the state of a call, including bridges.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_081": {
        "requirement_text": "KeepAliveFailureLogEvent: The OPTIONS request is the “keep alive” mechanism specified in this document (Section 3.1.2.3).",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The KeepAliveFailureLogEvent logs failures of the keep-alive mechanism using OPTIONS requests.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_082": {
        "requirement_text": "VersionsLogEvent: Records the response to a web service Versions request (See Section 2.8).",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The VersionsLogEvent records the response to a web service Versions request.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_083": {
        "requirement_text": "SubscribeLogEvent: When a subscription request is processed for any defined Event Package, the transaction is logged with SubscribeLogEvent.",
        "document_section": "4.12.3.7 & 10.21",
        "description": "The SubscribeLogEvent logs the transaction when a subscription request is processed.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_084": {
        "requirement_text": "In addition, an ingress BCF SHALL police the presence of a “verstat” parameter within the P-Asserted-Identity header or From header of a SIP method associated with an incoming call. An ingress BCF SHALL remove the “verstat” parameter from a P-Asserted-Identity header or From header if present in a SIP method associated with an incoming call.",
        "document_section": "Section TBD",
        "description": "The ingress BCF must remove any “verstat” parameter from incoming SIP headers.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_085": {
        "requirement_text": "All elements in the ESInet MUST accept RSA-2048 with a certificate rooted in the PCA.",
        "document_section": "5.5",
        "description": "All elements in the ESInet must accept RSA-2048 certificates rooted in the PCA.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_086": {
        "requirement_text": "Authorization and Data Rights Management",
        "document_section": "5.6",
        "description": "Authorization and Data Rights Management governs the protection of access and data.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_087": {
        "requirement_text": "All protocol operations MUST be integrity-protected with TLS, using SHA‑256 [62] or stronger. SHA‑256 MUST be supported by all implementations.",
        "document_section": "5.7",
        "description": "All protocol operations must be integrity-protected using TLS with at least SHA-256.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_088": {
        "requirement_text": "All protocol operations MUST be privacy protected via TLS, preferably using Advanced Encryption Standard (AES) [63] with a minimum key length of 256 bits (AES‑256). Shorter key length MUST NOT be used.",
        "document_section": "5.8",
        "description": "All protocol operations must be privacy-protected using TLS with AES-256 encryption.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_089": {
        "requirement_text": "Stored data which contains confidential information MUST be stored encrypted, using AES‑256 or an equivalently strong algorithm.",
        "document_section": "5.8",
        "description": "Confidential data must be stored encrypted using AES-256 or equivalent encryption algorithms.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_090": {
        "requirement_text": "JSON Web Signature",
        "document_section": "5.1",
        "description": "The JSON Web Signature is used to securely sign data exchanges.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_091": {
        "requirement_text": "Data and the Emergency Incident Data Object",
        "document_section": "7",
        "description": "Data and the Emergency Incident Data Object refer to structured data about emergency calls.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_092": {
        "requirement_text": "All SIP elements MUST support TLS (See Section 2.8.1), TCP, and UDP transport. SIP signaling within the ESInet SHOULD be carried with TLS. If TLS transport fails or is not available, SIP elements SHOULD attempt to use TCP. If TLS and TCP transports both fail or are unavailable, SIP elements SHOULD fall back to UDP transport.",
        "document_section": "3.1.13",
        "description": "All SIP elements must support TLS, TCP, and UDP transport, with preference for TLS.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_093": {
        "requirement_text": "Media streams for voice, video, and text MUST be carried on RTP over UDP (User Datagram Protocol). All endpoints in an ESInet MUST implement media security with Secure Real Time Protocol (SRTP) using Datagram Transport Layer Security (DTLS) as specified in RFC 5763 [166] and RFC 5764 [167].",
        "document_section": "3.1.9",
        "description": "Media streams must be carried on RTP over UDP, with SRTP and DTLS used for security.",
        "test_id": "",
        "subtests": []
    },
    "RQ_BCF_094": {
        "requirement_text": "All endpoints in an ESInet MUST implement media security with Secure Real Time Protocol (SRTP) using Datagram Transport Layer Security (DTLS) as specified in RFC 5763 [166] and RFC 5764 [167].",
        "document_section": "3.1.9",
        "description": "All ESInet endpoints must implement SRTP with DTLS for media security.",
        "test_id": "",
        "subtests": []
    }
}
