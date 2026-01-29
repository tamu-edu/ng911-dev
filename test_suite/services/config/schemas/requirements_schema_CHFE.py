REQUIREMENTS_SCHEMA = {
    "RQ_CHFE_269": {
        "requirement_text": "NG9?1?1 elements that process 9?1?1 calls MUST accept calls that do not strictly follow the SIP standards. As long as the messages can be parsed, and the method discerned, at least the first SIP element (the BCF) MUST be able to accept the call and forward the call onward (see Section 4.1)  Support for the following SIP Methods is summarized and specified in the following table: (See underlying table)",
        "document_section": "3.1.1",
        "description": "NG9?1?1 elements that process 9?1?1 calls MUST accept calls that do not strictly follow the SIP standards.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_389": {
        "requirement_text": "All DRs MUST contain common data elements (a prolog) that include: [see list]",
        "document_section": "3.7",
        "description": "All DRs MUST contain common data elements (a prolog) that include: [see list]",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_003": {
        "requirement_text": "Callback and other non-emergency outbound call INVITE messages MUST comply with the SIP call interface as defined in Section 3.1, and constructed using the guidance provided in section 4.20 (OCIF), with the following clarifications.",
        "document_section": "4.6.1",
        "description": "Callback and other non-emergency outbound call INVITE messages MUST comply with the SIP call interface as defined in Section 3.",
        "test_id": "CHFE_004",
        "subtests": []
    },
    "RQ_CHFE_007": {
        "requirement_text": "If the PSAP receives an Answer containing both RTT and MSRP, it MUST be prepared to deal with both simultaneously.",
        "document_section": "4.6.2",
        "description": "If the PSAP receives an Answer containing both RTT and MSRP, it MUST be prepared to deal with both simultaneously.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_010": {
        "requirement_text": "The PSAP MUST implement a LoST client interface as defined in Section 3.4.",
        "document_section": "4.6.3",
        "description": "The PSAP MUST implement a LoST client interface as defined in Section 3.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_014": {
        "requirement_text": "PSAPs MUST be able to accept calls from, and utilize the features of, outside bridges.",
        "document_section": "4.6.5",
        "description": "PSAPs MUST be able to accept calls from, and utilize the features of, outside bridges.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_044": {
        "requirement_text": "The REFER MUST contain a suitable URN, usually the urn used to query the ECRF to determine the correct responder, or an appropriate urn from the urn:emergency:service:responder tree if a specific responder was selected, a 'serviceurn' parameter of the Refer-To .",
        "document_section": "4.7.1",
        "description": "The REFER MUST contain a suitable URN, usually the urn used to query the ECRF to determine the correct responder, or an appropriate urn from the urn:emergency:service:responder tree if a specific responder was selected, a 'serviceurn' parameter of the Refer-To.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_045": {
        "requirement_text": "The Refer-To header field contains the URI of the target (which may be returned from a LoST query) and MUST contain the URN (in the urn:service:sos or urn:emergency:service:sos trees) as a URI parameter of 'serviceurn'.",
        "document_section": "4.7.1",
        "description": "The Refer-To header field contains the URI of the target (which may be returned from a LoST query) and MUST contain the URN (in the urn:service:sos or urn:emergency:service:sos trees) as a URI parameter of 'serviceurn'.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_047": {
        "requirement_text": "Note that the Refer-To header field MUST be a sip URI.",
        "document_section": "4.7.1",
        "description": "Note that the Refer-To header field MUST be a sip URI.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_049": {
        "requirement_text": "For the Ad Hoc case, the transfer-to PSAP MUST release the bridge when the transfer-from PSAP terminates its leg of the call in order to release bridge resources",
        "document_section": "4.7.1",
        "description": "For the Ad Hoc case, the transfer-to PSAP MUST release the bridge when the transfer-from PSAP termin...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_054": {
        "requirement_text": "For a blind transfer in ESInets using the ad hoc method, the transferring PSAP SHALL NOT seize the bridge prior to initiating a blind transfer.",
        "document_section": "4.7.2",
        "description": "For a blind transfer in ESInets using the ad hoc method, the transferring PSAP SHALL NOT seize the bridge prior to initiating a blind transfer.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_055": {
        "requirement_text": "The transfer-from PSAP MUST send a REFER where the Request Line contains the caller information.",
        "document_section": "4.7.2",
        "description": "The transfer-from PSAP MUST send a REFER where the Request Line contains the caller information.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_056": {
        "requirement_text": "The Refer-To header field MUST specify the transfer-to PSAP (or any other entity): for consistency with Bridging and Attended transfer, the transfer-from PSAP SHOULD include the EIDO URI in an escaped parameter in the Refer-To header field.",
        "document_section": "4.7.2",
        "description": "The Refer-To header field MUST specify the transfer-to PSAP (or any other entity): for consistency with Bridging and Attended transfer, the transfer-from PSAP SHOULD include the EIDO URI in an escaped parameter in the Refer-To header field.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_058": {
        "requirement_text": "At this point the transferring PSAP MUST send a BYE to end its participation in the call.",
        "document_section": "4.7.2",
        "description": "At this point the transferring PSAP MUST send a BYE to end its participation in the call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_059": {
        "requirement_text": "If the transferring PSAP receives an error code in the notification, e.g. 503 Service Unavailable, it MUST assume that the transfer did not occur, and MUST NOT terminate the call.",
        "document_section": "4.7.2",
        "description": "If the transferring PSAP receives an error code in the notification, e.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_060": {
        "requirement_text": "If for any reason a consultative transfer must be terminated early, the following procedures MUST be used.",
        "document_section": "4.7.3",
        "description": "If for any reason a consultative transfer must be terminated early, the following procedures MUST be used.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_061": {
        "requirement_text": "A REFER request implicitly establishes a subscription to the refer event as defined in RFC 3515 [19], but not regarding the conference as a whole. Once the REFER is successfully acknowledged with a 200 OK, the recipient of the REFER will send notifications of the status of the adding the target participant. It MAY send a notification containing a 100 Trying to indicate the transfer is pending. It MAY also send additional provisional messages, e.g. 183 Session Progress. It MUST send a 200 OK indicating that the party was successfully added. At this point the transferring PSAP MUST send a BYE to end its participation in the call. If the transferring PSAP receives an error code in the notification, e.g. 503 Service Unavailable, it MUST assume that the transfer did not occur and MUST not terminate the call.",
        "document_section": "4.7.3",
        "description": "A REFER request implicitly establishes a subscription to the refer event as defined in RFC 3515 [19], but not regarding the conference as a whole.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_062": {
        "requirement_text": "Caller location information along with any Additional Data MUST be populated in an Emergency Incident Data Object (EIDO) structure (see Section 7 for further discussion of Additional Data structures).",
        "document_section": "4.7.4",
        "description": "Caller location information along with any Additional Data MUST be populated in an Emergency Incident Data Object (EIDO) structure (see Section 7 for further discussion of Additional Data structures).",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_063": {
        "requirement_text": "The bridge MUST subsequently include this Call-Info header field in the INVITE it sends to the transfer target.",
        "document_section": "4.7.4",
        "description": "The bridge MUST subsequently include this Call-Info header field in the INVITE it sends to the transfer target.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_064": {
        "requirement_text": "The EIDO MUST be passed by reference when the Call-Info header field contains a URL that, when dereferenced, yields the EIDO.",
        "document_section": "4.7.4",
        "description": "The EIDO MUST be passed by reference when the Call-Info header field contains a URL that, when dereferenced, yields the EIDO.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_070": {
        "requirement_text": "PSAPs MUST implement both transfer models.",
        "document_section": "4.7.5",
        "description": "PSAPs MUST implement both transfer models.",
        "test_id": "CHFE_006",
        "subtests": []
    },
    "RQ_CHFE_388": {
        "requirement_text": "Negotiation of multi-party awareness SHALL be performed by mixers and endpoints at session initiation and modification.",
        "document_section": "4.8.1",
        "description": "Negotiation of multi-party awareness SHALL be performed by mixers and endpoints at session initiation and modification.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_082": {
        "requirement_text": "The receiving endpoint with presentation functions, which has completed the negotiation for multi-party RTT awareness, SHALL use the source information to present text from the different sources separated in readable groups placed in an approximate relative time order.",
        "document_section": "4.8.1",
        "description": "The receiving endpoint with presentation functions, which has completed the negotiation for multi-party RTT awareness, SHALL use the source information to present text from the different sources separated in readable groups placed in an approximate relative time order.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_250": {
        "requirement_text": "A REFER request implicitly establishes a subscription to the refer event as defined in RFC 3515 [19], but not regarding the conference as a whole. Once the REFER is successfully acknowledged with a 200 OK, the recipient of the REFER will send notifications of the status of the adding the target participant. It MAY send a notification containing a 100 Trying to indicate the transfer is pending. It MAY also send additional provisional messages, e.g. 183 Session Progress. It MUST send a 200 OK indicating that the party was successfully added. At this point the transferring PSAP MUST send a BYE to end its participation in the call. If the transferring PSAP receives an error code in the notification, e.g. 503 Service Unavailable, it MUST assume that the transfer did not occur and MUST not terminate the call.",
        "document_section": "4.7.3",
        "description": "A REFER request implicitly establishes a subscription to the refer event as defined in RFC 3515 [19], but not regarding the conference as a whole.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_270": {
        "requirement_text": "All SIP proxy servers in the ESInet/NGCS MUST implement Resource-Priority and process calls in priority order when a queue of calls is waiting for service at the proxy server and, when needed, preempt lower priority calls",
        "document_section": "3.1.7",
        "description": "All SIP proxy servers in the ESInet/NGCS MUST implement Resource-Priority and process calls in prior...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_271": {
        "requirement_text": "All endpoints and media intermediaries within an ESInet/NGCS MUST support CPIM.",
        "document_section": "4.7.6",
        "description": "All endpoints and media intermediaries within an ESInet/NGCS MUST support CPIM.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_272": {
        "requirement_text": "Negotiation of multi-party awareness SHALL be performed by mixers and endpoints at session initiation and modification.",
        "document_section": "4.8.1",
        "description": "Negotiation of multi-party awareness SHALL be performed by mixers and endpoints at session initiation and modification.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_301": {
        "requirement_text": "All SIP proxy servers in the ESInet/NGCS MUST implement Resource-Priority and process calls in priority order when a queue of calls is waiting for service at the proxy server and, when needed, preempt lower priority calls",
        "document_section": "3.1.7",
        "description": "All SIP proxy servers in the ESInet/NGCS MUST implement Resource-Priority and process calls in prior...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_302": {
        "requirement_text": "The ECRF MUST be used within the ESInet to route calls to the correct PSAP, and by the PSAP to route calls to the correct responders.",
        "document_section": "4.3",
        "description": "The ECRF MUST be used within the ESInet to route calls to the correct PSAP, and by the PSAP to route calls to the correct responders.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_341": {
        "requirement_text": "RecCallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecCallStartLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_342": {
        "requirement_text": "RecCallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecCallEndLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_357": {
        "requirement_text": "When a call is transferred, the transfer is logged by the transferor (the entity that had the call prior to transferring it). The transfer target URI is logged in a target member. Elements that log CallTransferLogEvent MUST also log the actual SIP targetCallIdSIP member that contains the SIP CallId of the new session with the transfer target, when known. Note that the PSAP may not know this CallId, but the bridge would.",
        "document_section": "4.12.3.7",
        "description": "When a call is transferred, the transfer is logged by the transferor (the entity that had the call prior to transferring it).",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_362": {
        "requirement_text": "LostResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LostResponseLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_377": {
        "requirement_text": "LostQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LostQueryLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_001": {
        "requirement_text": "The PSAP MUST deploy the SIP call interface as defined in Section 3.1 including the multimedia capability, and the non-interactive call (emergency event) capability.",
        "document_section": "4.6.1",
        "description": "The PSAP MUST deploy the SIP call interface as defined in Section 3.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_006": {
        "requirement_text": "All i3 PSAPs MUST support all media, voice, video, and text.",
        "document_section": "4.6.2",
        "description": "All i3 PSAPs MUST support all media, voice, video, and text.",
        "test_id": "CHFE_002",
        "subtests": []
    },
    "RQ_CHFE_008": {
        "requirement_text": "SDP offers and answers generated by the PSAP MUST include appropriate language tags.",
        "document_section": "4.6.2",
        "description": "SDP offers and answers generated by the PSAP MUST include appropriate language tags.",
        "test_id": "CHFE_003",
        "subtests": []
    },
    "RQ_CHFE_009": {
        "requirement_text": "Answers to offers that included language tags MUST include language tags.",
        "document_section": "4.6.2",
        "description": "Answers to offers that included language tags MUST include language tags.",
        "test_id": "CHFE_003",
        "subtests": []
    },
    "RQ_CHFE_011": {
        "requirement_text": "The PSAP MUST implement both SIP Presence Event Package and HELD dereferencing interfaces to any LIS function as described in Section 4.10.",
        "document_section": "4.6.4",
        "description": "The PSAP MUST implement both SIP Presence Event Package and HELD dereferencing interfaces to any LIS function as described in Section 4.",
        "test_id": "CHFE_001",
        "subtests": []
    },
    "RQ_CHFE_013": {
        "requirement_text": "The PSAP MUST use TCP with TLS for the LIS dereferencing interface, with fallback to TCP (without TLS) on failure to establish a TLS connection when TLS is used.",
        "document_section": "4.6.4",
        "description": "The PSAP MUST use TCP with TLS for the LIS dereferencing interface, with fallback to TCP (without TLS) on failure to establish a TLS connection when TLS is used.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_017": {
        "requirement_text": "The PSAP MUST deploy a ServiceState notifier as described in Section 2.4.2.",
        "document_section": "4.6.7",
        "description": "The PSAP MUST deploy a ServiceState notifier as described in Section 2.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_021": {
        "requirement_text": "The PSAP MUST implement a Logging Service client, as defined in Section 4.12, including the client side of the media recording mechanism (Section 4.12.2).",
        "document_section": "4.6.12",
        "description": "The PSAP MUST implement a Logging Service client, as defined in Section 4.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_033": {
        "requirement_text": "PSAPs MUST support the test call interface as described in Section 9...",
        "document_section": "4.6.17",
        "description": "PSAPs MUST support the test call interface as described in Section 9.",
        "test_id": "CHFE_005",
        "subtests": []
    },
    "RQ_CHFE_034": {
        "requirement_text": "PSAPs MUST support test of all media - voice, video, and text.",
        "document_section": "4.6.17",
        "description": "PSAPs MUST support test of all media - voice, video, and text.",
        "test_id": "CHFE_005",
        "subtests": []
    },
    "RQ_CHFE_281": {
        "requirement_text": "The REFER MUST contain a suitable URN, usually the urn used to query the ECRF to determine the correct responder, or an appropriate urn from the urn:emergency:service:responder tree if a specific responder was selected, a 'serviceurn' parameter of the Refer-To.",
        "document_section": "4.7.1",
        "description": "The REFER MUST contain a suitable URN, usually the urn used to query the ECRF to determine the correct responder, or an appropriate urn from the urn:emergency:service:responder tree if a specific responder was selected, a 'serviceurn' parameter of the Refer-To.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_283": {
        "requirement_text": "...the Refer-To header field MUST be a sip URI.",
        "document_section": "4.7.1",
        "description": "...the Refer-To header field MUST be a sip URI.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_287": {
        "requirement_text": "The Refer-To header field MUST specify the transfer-to PSAP (or any other entity): for consistency with Bridging and Attended transfer",
        "document_section": "4.7.2",
        "description": "The Refer-To header field MUST specify the transfer-to PSAP (or any other entity): for consistency w...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_296": {
        "requirement_text": "When the bridge is used to transfer the call, the location of the caller and any Additional Data included (or retrieved in conjunction) with the call MUST be transferred to the transfer target.",
        "document_section": "4.7.1",
        "description": "When the bridge is used to transfer the call, the location of the caller and any Additional Data included (or retrieved in conjunction) with the call MUST be transferred to the transfer target.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_304": {
        "requirement_text": "MediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MediaStartLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_309": {
        "requirement_text": "DiscrepancyReportLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "DiscrepancyReportLogEvent members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_310": {
        "requirement_text": "DiscrepancyReportLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "DiscrepancyReportLogEvent members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_312": {
        "requirement_text": "CallSignalingMessageLogEvent: An element MUST always log messages it receives (with \"direction\" set to \"incoming\").",
        "document_section": "4.12.3.7",
        "description": "CallSignalingMessageLogEvent: An element MUST always log messages it receives (with \"direction\" set to \"incoming\").",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_313": {
        "requirement_text": "CallSignalingMessageLogEvent: An element MUST log outgoing messages it originates.",
        "document_section": "4.12.3.7",
        "description": "CallSignalingMessageLogEvent: An element MUST log outgoing messages it originates.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_314": {
        "requirement_text": "CallSignalingMessageLogEvent members.",
        "document_section": "4.12.3.7",
        "description": "CallSignalingMessageLogEvent members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_315": {
        "requirement_text": "MalformedMessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MalformedMessageLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_316": {
        "requirement_text": "Clients to the Logging Service MUST support logging to at least two Logging Services",
        "document_section": "4.12.1",
        "description": "Clients to the Logging Service MUST support logging to at least two Logging Services",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_318": {
        "requirement_text": "Each element that is call stateful logs the beginning and end of its processing of a call, including non-interactive calls, with Start Call and End Call events. Elements that log CallStartLogEvent/CallEndLogEvent MUST also log the actual SIP message with CallSignalingMessageLogEvent for SIP parts of a call and GatewayCallLogEvent for TDM parts of a call. For CallStartLogEvent and CallEndLogEvent, the Timestamp MUST be the time the INVITE, MESSAGE, BYE or equivalents to these messages, or the final status code was received or sent by the element logging the event.",
        "document_section": "4.12.3.7",
        "description": "Each element that is call stateful logs the beginning and end of its processing of a call, including non-interactive calls, with Start Call and End Call events.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_319": {
        "requirement_text": "CallStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallStartLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_320": {
        "requirement_text": "CallEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallEndLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_327": {
        "requirement_text": "Clients to the Logging Service MUST support logging to at least two Logging Services for redundancy purposes",
        "document_section": "4.12.1",
        "description": "Clients to the Logging Service MUST support logging to at least two Logging Services for redundancy...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_334": {
        "requirement_text": "Clients to the Logging Service MUST support logging to at least two Logging Services for redundancy purposes",
        "document_section": "4.12.1",
        "description": "Clients to the Logging Service MUST support logging to at least two Logging Services for redundancy...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_336": {
        "requirement_text": "FEs that use a Logging Service MUST NOT depend on a Logging Service accepting an extension to provide services conformant to this document.",
        "document_section": "4.12.3.1",
        "description": "FEs that use a Logging Service MUST NOT depend on a Logging Service accepting an extension to provide services conformant to this document.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_339": {
        "requirement_text": "QueueStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "QueueStateChangeLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_345": {
        "requirement_text": "All forms of media described in this document MUST be logged (see the Media section for details)",
        "document_section": "4.12",
        "description": "All forms of media described in this document MUST be logged (see the Media section for details)",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_346": {
        "requirement_text": "Elements that implement the SRC interface MUST be capable of supporting redundant implementations of the SRS (RFC 7866) [116] and MUST insert the Call Identifier and Incident Tracking Identifier (Call-Info header fields) defined in this document into the INVITE sent to the Logging Service.",
        "document_section": "4.12.2",
        "description": "Elements that implement the SRC interface MUST be capable of supporting redundant implementations of the SRS (RFC 7866) [116] and MUST insert the Call Identifier and Incident Tracking Identifier (Call-Info header fields) defined in this document into the INVITE sent to the Logging Service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_347": {
        "requirement_text": "When an SRC sends SIPREC Metadata, it MUST generate a SiprecMetadata LogEvent to the Logging Service.",
        "document_section": "4.12.2",
        "description": "When an SRC sends SIPREC Metadata, it MUST generate a SiprecMetadata LogEvent to the Logging Service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_348": {
        "requirement_text": "The SRC MUST include the CallId and IncidentId for the emergency call being recorded in the SIPREC INVITE it generates and when generating an associated SiprecMetadata LogEvent.",
        "document_section": "4.12.2",
        "description": "The SRC MUST include the CallId and IncidentId for the emergency call being recorded in the SIPREC INVITE it generates and when generating an associated SiprecMetadata LogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_349": {
        "requirement_text": "Elements that implement the SRC interface MUST be capable of supporting redundant implementations of the SRS (RFC 7866) [116]",
        "document_section": "4.12.2",
        "description": "Elements that implement the SRC interface MUST be capable of supporting redundant implementations of...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_350": {
        "requirement_text": "SRCs MUST support recording of media to at least two SRSes.",
        "document_section": "4.12.2",
        "description": "SRCs MUST support recording of media to at least two SRSes.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_351": {
        "requirement_text": "All SRCs and SRSes MUST implement RTCP on the recording session.",
        "document_section": "4.12.2",
        "description": "All SRCs and SRSes MUST implement RTCP on the recording session.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_352": {
        "requirement_text": "The SRC MUST send wall clock time in sender reports.",
        "document_section": "4.12.2",
        "description": "The SRC MUST send wall clock time in sender reports.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_353": {
        "requirement_text": "All Bridge elements (Section 5.7), Gateway elements (Section 7), BCF elements that anchor media, and PSAP Call Handling elements, MUST implement the SRC interface.",
        "document_section": "4.12.2",
        "description": "All Bridge elements (Section 5.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_354": {
        "requirement_text": "The call MUST still be recorded while the third party is being added as well as when all three parties are on the call.",
        "document_section": "4.12.2.2",
        "description": "The call MUST still be recorded while the third party is being added as well as when all three parties are on the call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_355": {
        "requirement_text": "The call MUST still be recorded by the SRC.",
        "document_section": "4.12.2.5",
        "description": "The call MUST still be recorded by the SRC.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_356": {
        "requirement_text": "The Logging Recorder MUST be able to provide a clean shut down by sending a BYE as specified in Section 3.1.1.3, for example when one SRS in a redundant pair is going out of service. The SRC MUST respond with a 200 OK.",
        "document_section": "4.12.2.6",
        "description": "The Logging Recorder MUST be able to provide a clean shut down by sending a BYE as specified in Section 3.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_359": {
        "requirement_text": "CallStateChangeLogEvent MUST be logged by all elements that change the state of the call, which would include a bridge and all entities within the ESInet that request bridge actions when an emergency call is on a bridge.",
        "document_section": "4.12.3.7",
        "description": "CallStateChangeLogEvent MUST be logged by all elements that change the state of the call, which would include a bridge and all entities within the ESInet that request bridge actions when an emergency call is on a bridge.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_360": {
        "requirement_text": "CallStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallStateChangeLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_365": {
        "requirement_text": "AdditionalDataResponseLogEvent: Any Additional Data that is retrieved by a client MUST be logged using the AdditionalDataResponseLogEvent.",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataResponseLogEvent: Any Additional Data that is retrieved by a client MUST be logged using the AdditionalDataResponseLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_371": {
        "requirement_text": "EidoLogEvent members",
        "document_section": "4.12.3.7",
        "description": "EidoLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_372": {
        "requirement_text": "AdditionalDataQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataQueryLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_373": {
        "requirement_text": "A queue manager MUST log a change in the state of the queue with the QueueStateChangeLogEvent.",
        "document_section": "4.12.3.7",
        "description": "A queue manager MUST log a change in the state of the queue with the QueueStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_374": {
        "requirement_text": "AdditionalDataQueryLogEvent: A \"queryId\" member is used to relate the request to the response. The id is generated locally, MUST be globally unique",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataQueryLogEvent: A \"queryId\" member is used to relate the request to the response.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_376": {
        "requirement_text": "AdditionalDataResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataResponseLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_002": {
        "requirement_text": "PSAPs MUST recognize calls to their administrative numbers received from the ESInet (and distinguishable from normal 9?1?1 calls by the presence of the number in a sip or tel URI in the To header field and the absence of the sos service URN in a Request-URI line, and identified in the target PSAP's SALR, if available).",
        "document_section": "4.6.1",
        "description": "PSAPs MUST recognize calls to their administrative numbers received from the ESInet (and distinguishable from normal 9?1?1 calls by the presence of the number in a sip or tel URI in the To header field and the absence of the sos service URN in a Request-URI line, and identified in the target PSAP's SALR, if available).",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_004": {
        "requirement_text": "The To header field value of the callback INVITE message MUST be set to a value that will allow reaching the home network of the target.",
        "document_section": "4.6.1",
        "description": "The To header field value of the callback INVITE message MUST be set to a value that will allow reaching the home network of the target.",
        "test_id": "CHFE_004",
        "subtests": []
    },
    "RQ_CHFE_005": {
        "requirement_text": "If the To header field value is a sip URI, the domain SHALL be the one of the home network of the target.",
        "document_section": "4.6.1",
        "description": "If the To header field value is a sip URI, the domain SHALL be the one of the home network of the target.",
        "test_id": "CHFE_004",
        "subtests": []
    },
    "RQ_CHFE_012": {
        "requirement_text": "The PSAP MUST be able to be provisioned with credentials for every LIS in its service area.",
        "document_section": "4.6.4",
        "description": "The PSAP MUST be able to be provisioned with credentials for every LIS in its service area.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_015": {
        "requirement_text": "The PSAP MUST deploy an ElementState Notifier.",
        "document_section": "4.6.6",
        "description": "The PSAP MUST deploy an ElementState Notifier.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_016": {
        "requirement_text": "Any element inside a PSAP that provides a call queue MUST deploy an ElementState notifier as described in Section 2.4.1.",
        "document_section": "4.6.6",
        "description": "Any element inside a PSAP that provides a call queue MUST deploy an ElementState notifier as described in Section 2.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_018": {
        "requirement_text": "The PSAP MUST implement the subscriber side of the AbandonedCall Event as described in Section 4.2.2.9.",
        "document_section": "4.6.8",
        "description": "The PSAP MUST implement the subscriber side of the AbandonedCall Event as described in Section 4.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_019": {
        "requirement_text": "The PSAP MUST implement a DequeueRegistration client, as described in Section 4.2.1.4, for every queue on which it expects to receive calls.",
        "document_section": "4.6.9",
        "description": "The PSAP MUST implement a DequeueRegistration client, as described in Section 4.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_020": {
        "requirement_text": "The PSAP MUST implement a QueueState notifier as described in Section 4.2.1.3 for all queues it manages.",
        "document_section": "4.6.10",
        "description": "The PSAP MUST implement a QueueState notifier as described in Section 4.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_022": {
        "requirement_text": "A PSAP MUST be able to use a Logging Service hosted in the ESInet.",
        "document_section": "4.6.12",
        "description": "A PSAP MUST be able to use a Logging Service hosted in the ESInet.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_023": {
        "requirement_text": "The PSAP MAY deploy a Logging Service (as described in Section 4.12) inside the PSAP, in which case it MUST provide the Logging Service retrieval functions.",
        "document_section": "4.6.12",
        "description": "The PSAP MAY deploy a Logging Service (as described in Section 4.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_024": {
        "requirement_text": "The PSAP MUST provide a Security Posture notifier as described in Section 2.4.2.",
        "document_section": "4.6.13",
        "description": "The PSAP MUST provide a Security Posture notifier as described in Section 2.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_027": {
        "requirement_text": "If the PSAP uses a Policy Store outside the PSAP to control functions inside the PSAP, it MUST deploy the client-side of the policy retrieval functions.",
        "document_section": "4.6.14",
        "description": "If the PSAP uses a Policy Store outside the PSAP to control functions inside the PSAP, it MUST deploy the client-side of the policy retrieval functions.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_030": {
        "requirement_text": "The PSAP MUST deploy a dereference (HTTPS GET) interface for additional data as described in Section 7, as well as the IS ADR identity query mechanism.",
        "document_section": "4.6.15",
        "description": "The PSAP MUST deploy a dereference (HTTPS GET) interface for additional data as described in Section 7, as well as the IS ADR identity query mechanism.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_031": {
        "requirement_text": "The PSAP MUST also be able to dereference an EIDO URI for a call transferred to it.",
        "document_section": "4.6.15",
        "description": "The PSAP MUST also be able to dereference an EIDO URI for a call transferred to it.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_032": {
        "requirement_text": "The PSAP MUST implement an NTP client interface for time of day information.",
        "document_section": "4.6.16",
        "description": "The PSAP MUST implement an NTP client interface for time of day information.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_387": {
        "requirement_text": "The PSAP MUST merge the IncidentTrackingID assigned by the ESRP with the actual IncidentTrackingID.",
        "document_section": "4.6.19",
        "description": "The PSAP MUST merge the IncidentTrackingID assigned by the ESRP with the actual IncidentTrackingID.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_051": {
        "requirement_text": "None. [Call flows depicted in the diagram are expected to work according to RFC 4579.]",
        "document_section": "4.7.1.1",
        "description": "None. [Call flows depicted in the diagram are expected to work according to RFC 4579.]",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_052": {
        "requirement_text": "None. [Call flows depicted in the diagram are expected to work according to RFC 4579.]",
        "document_section": "4.7.1.2",
        "description": "None. [Call flows depicted in the diagram are expected to work according to RFC 4579.]",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_053": {
        "requirement_text": "None. [Call flows depicted in the diagram are expected to work according to RFC 4579.]",
        "document_section": "4.7.1.3",
        "description": "None. [Call flows depicted in the diagram are expected to work according to RFC 4579.]",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_065": {
        "requirement_text": "The GET request MUST contain an 'Accept:' header field which specifies the MIME type assigned to EIDO (application/emergency.eido+json) and MUST include as a parameter a comma-delimited list of the major version(s) of the schema the client supports (for example 'Accept: application/emergency.eido+json;version=\"1,2,3\"').",
        "document_section": "4.7.4",
        "description": "The GET request MUST contain an 'Accept:' header field which specifies the MIME type assigned to EIDO (application/emergency.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_067": {
        "requirement_text": "The client MUST expect to receive an object derived from any minor version of the specified EIDO schema, including a higher minor version than it currently supports.",
        "document_section": "4.7.4",
        "description": "The client MUST expect to receive an object derived from any minor version of the specified EIDO schema, including a higher minor version than it currently supports.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_068": {
        "requirement_text": "The client MUST ignore any fields it does not understand.",
        "document_section": "4.7.4",
        "description": "The client MUST ignore any fields it does not understand.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_072": {
        "requirement_text": "All ESInet/NGCS CPIM-enabled endpoints MUST implement the nickname negotiation feature of RFC 7701 [123] and offer a nickname.",
        "document_section": "4.7.6",
        "description": "All ESInet/NGCS CPIM-enabled endpoints MUST implement the nickname negotiation feature of RFC 7701 [123] and offer a nickname.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_073": {
        "requirement_text": "All endpoints and media intermediaries within an ESInet/NGCS MUST support CPIM.",
        "document_section": "4.7.6",
        "description": "All endpoints and media intermediaries within an ESInet/NGCS MUST support CPIM.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_075": {
        "requirement_text": "All NG9 1 1 implementations MUST supply identity information in this manner to the bridge.",
        "document_section": "4.8",
        "description": "All NG9 1 1 implementations MUST supply identity information in this manner to the bridge.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_086": {
        "requirement_text": "No specific text",
        "document_section": "4.9.3.1",
        "description": "No specific text",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_087": {
        "requirement_text": "No specific text",
        "document_section": "4.9.3.2",
        "description": "No specific text",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_088": {
        "requirement_text": "No specific text",
        "document_section": "4.9.4.1",
        "description": "No specific text",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_089": {
        "requirement_text": "No specific text",
        "document_section": "4.9.4.2",
        "description": "No specific text",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_093": {
        "requirement_text": "SIP INVITE messages for callbacks destined to be routed through an OCIF MUST contain: 1.  A Request-URI line containing the callback URI; 2.  A To header field populated with the callback URI. Usually the value is the content of the P-A-I (preferred, if present) or From header field of the original emergency call;",
        "document_section": "4.20",
        "description": "SIP INVITE messages for callbacks destined to be routed through an OCIF MUST contain: 1.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_094": {
        "requirement_text": "The callback URI MUST contain a dialable telephone number either expressed as a national 10-digit NANP number or as an international number following ITU-T Recommendation E.164 and, if expressed as a sip URI, the domain part SHALL represent the home network of the target.",
        "document_section": "4.20",
        "description": "The callback URI MUST contain a dialable telephone number either expressed as a national 10-digit NANP number or as an international number following ITU-T Recommendation E.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_095": {
        "requirement_text": "If the original emergency call was from a non-service initialized handset, the callback number of the form \"911 plus the last 7 digits of the ESN or IMEI expressed as a decimal\" is not dialable and therefore MUST NOT be used for callback.",
        "document_section": "4.20",
        "description": "If the original emergency call was from a non-service initialized handset, the callback number of the form \"911 plus the last 7 digits of the ESN or IMEI expressed as a decimal\" is not dialable and therefore MUST NOT be used for callback.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_097": {
        "requirement_text": "SIP INVITE messages for other outgoing calls that transit the ESInet through an OCIF MUST contain: 1. A Request-URI line containing the target URI; 2. A To header field populated with the target URI, as determined by the initiating PSAP; Note: The target URI MUST contain a dialable telephone number either expressed as a national 10-digit NANP number or as an international number following ITU-T Recommendation E.164, or a sip URI that is routable within the ESInet, where the domain part represents the home network of the target. 3. A From header field containing sip:TN@<psapdomain>;user=phone, which SHOULD be the same as in the P-A-I header field; Note: The OCIF MUST support receipt of outgoing calls from i3-PSAPs marked for presentation restriction of caller ID, expressed by the presence of a Privacy header field (RFC 3323 [207], expanded by RFC 3325 [16] and RFC 7044 [35]) and the From header field value populated with \"Anonymous\" sip:anonymous@anonymous.invalid;  4. A Route header field populated with a routing URI that should contain the \"lr\" parameter to avoid Request-URI rewriting (the INVITE from the PSAP MUST contain the outgoing ESRP. The INVITE from the ESRP to the OCIF SHALL contain the OCIF URI. If the INVITE from the OCIF is to an interconnected network, it MAY contain the well-known URI associated with that network); 5. A Resource-Priority header field populated with an appropriate value based on section 3.1.7 (e.g., \"esnet.0\" or \"esnet.2\") as determined by the originating PSAP; 6. A P-Asserted-Identity header field containing sip:TN@<psapdomain>;user=phone, where the TN is associated with the PSAP originating the call and can be asserted by an STI-AS function; 7. A second P-Asserted-Identity header field containing the identity of the agent originating the call expressed as sip:\"agent name\"<agentID@agencyID>; Note:  the Display Name part is OPTIONAL 8. An SDP offer containing all media supported at the PSAP;",
        "document_section": "4.20",
        "description": "SIP INVITE messages for other outgoing calls that transit the ESInet through an OCIF MUST contain: 1.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_251": {
        "requirement_text": "The GET request MUST contain an 'Accept:' header field which specifies the MIME type assigned to EIDO (application/emergency.eido+json) and MUST include as a parameter a comma-delimited list of the major version(s) of the schema the client supports (for example 'Accept: application/emergency.eido+json;version=\"1,2,3\"').",
        "document_section": "4.7.4",
        "description": "The GET request MUST contain an 'Accept:' header field which specifies the MIME type assigned to EIDO (application/emergency.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_253": {
        "requirement_text": "A reference to this structure SHALL be passed with a transferred call",
        "document_section": "7.2",
        "description": "A reference to this structure SHALL be passed with a transferred call",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_254": {
        "requirement_text": "the structure MUST be retrieved using the EIDO Conveyance mechanisms defined in NENA/APCO STA 024.1 201x [185]",
        "document_section": "7.2",
        "description": "the structure MUST be retrieved using the EIDO Conveyance mechanisms defined in NENA/APCO STA 024.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_255": {
        "requirement_text": "SIP MUST also be the protocol used to call a 9-1-1 caller back",
        "document_section": "3.1",
        "description": "SIP MUST also be the protocol used to call a 9-1-1 caller back",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_259": {
        "requirement_text": "i3 PSAPs MUST support NG-AACN calls per RFC 8148 [168], including at least the VEDS dataset and the ability to send a telematics dataset acknowledgment.",
        "document_section": "3.1.19",
        "description": "i3 PSAPs MUST support NG-AACN calls per RFC 8148 [168], including at least the VEDS dataset and the ability to send a telematics dataset acknowledgment.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_273": {
        "requirement_text": "request (If the discrepancy concerns a dialog, the initial INVITE that initiated the dialog )",
        "document_section": "3.7.6",
        "description": "request (If the discrepancy concerns a dialog, the initial INVITE that initiated the dialog )",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_274": {
        "requirement_text": "problem (One of the following tokens: InitialTrafficBlocked; MidTrafficBlocked; BadSDP; BadSIP; MediaLoss; TrafficNotBlockedBadActor; TrafficNotBlocked; QoS; BadCDR; TTY; Firewall; OtherBCF)",
        "document_section": "3.7.6",
        "description": "problem (One of the following tokens: InitialTrafficBlocked; MidTrafficBlocked; BadSDP; BadSIP...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_275": {
        "requirement_text": "sosSource (The emergency-source parameter of the dialog request (i.e., the initial INVITE))",
        "document_section": "3.7.6",
        "description": "sosSource (The emergency-source parameter of the dialog request (i.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_276": {
        "requirement_text": "EventTimestamp (Timestamp of event being reported)",
        "document_section": "3.7.6",
        "description": "EventTimestamp (Timestamp of event being reported)",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_277": {
        "requirement_text": "packetHeader (For InitialTrafficBlocked, MidTrafficBlocked, TrafficNotBlockedBadActor, TrafficNotBlocked, or Firewall, contains the packet's header, encoded using base64)",
        "document_section": "3.7.6",
        "description": "packetHeader (For InitialTrafficBlocked, MidTrafficBlocked, TrafficNotBlockedBadActor, TrafficNotBlo...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_278": {
        "requirement_text": "packetHeader (For InitialTrafficBlocked, MidTrafficBlocked, TrafficNotBlockedBadActor, TrafficNotBlocked, or Firewall, contains the packet's header, encoded using base64)",
        "document_section": "3.7.6",
        "description": "packetHeader (For InitialTrafficBlocked, MidTrafficBlocked, TrafficNotBlockedBadActor, TrafficNotBlo...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_279": {
        "requirement_text": "All endpoints and media intermediaries within an ESInet/NGCS MUST support CPIM.",
        "document_section": "4.7.6",
        "description": "All endpoints and media intermediaries within an ESInet/NGCS MUST support CPIM.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_280": {
        "requirement_text": "All NG9-1-1 implementations MUST supply identity information in this manner to the bridge.",
        "document_section": "4.8",
        "description": "All NG9-1-1 implementations MUST supply identity information in this manner to the bridge.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_282": {
        "requirement_text": "The Refer-To header field contains the URI of the target (which may be returned from a LoST query) and MUST contain the URN (in the urn:service:sos or urn:emergency:service:sos trees) as a URI parameter of 'serviceurn'.",
        "document_section": "4.7.1",
        "description": "The Refer-To header field contains the URI of the target (which may be returned from a LoST query) and MUST contain the URN (in the urn:service:sos or urn:emergency:service:sos trees) as a URI parameter of 'serviceurn'.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_284": {
        "requirement_text": "For the Ad Hoc case, the transfer-to PSAP MUST release the bridge when the transfer-from PSAP terminates its leg of the call in order to release bridge resources.",
        "document_section": "4.7.1",
        "description": "For the Ad Hoc case, the transfer-to PSAP MUST release the bridge when the transfer-from PSAP terminates its leg of the call in order to release bridge resources.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_285": {
        "requirement_text": "For a blind transfer in ESInets using the ad hoc method, the transferring PSAP SHALL NOT seize the bridge prior to initiating a blind transfer.",
        "document_section": "4.7.2",
        "description": "For a blind transfer in ESInets using the ad hoc method, the transferring PSAP SHALL NOT seize the bridge prior to initiating a blind transfer.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_286": {
        "requirement_text": "The transfer-from PSAP MUST send a REFER where the Request Line contains the caller information.",
        "document_section": "4.7.2",
        "description": "The transfer-from PSAP MUST send a REFER where the Request Line contains the caller information.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_288": {
        "requirement_text": "To dereference the URI and obtain the EIDO, the recipient initiates an HTTPS: GET on the URI and the EIDO [111] is returned. The GET request MUST contain an 'Accept:' header field which specifies the MIME type assigned to EIDO (application/emergency.eido+json) and MUST include as a parameter a comma-delimited list of the major version(s) of the schema the client supports (for example 'Accept: application/emergency.eido+json;version=\"1,2,3\"').",
        "document_section": "4.7.4",
        "description": "To dereference the URI and obtain the EIDO, the recipient initiates an HTTPS: GET on the URI and the EIDO [111] is returned.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_289": {
        "requirement_text": "The client MUST expect to receive an object derived from any minor version of the specified EIDO schema, including a higher minor version than it currently supports.",
        "document_section": "4.7.4",
        "description": "The client MUST expect to receive an object derived from any minor version of the specified EIDO schema, including a higher minor version than it currently supports.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_290": {
        "requirement_text": "The client MUST ignore any fields it does not understand.",
        "document_section": "4.7.4",
        "description": "The client MUST ignore any fields it does not understand.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_291": {
        "requirement_text": "All ESInet/NGCS CPIM-enabled endpoints MUST implement the nickname negotiation feature of RFC 7701 [123] and offer a nickname.",
        "document_section": "4.7.6",
        "description": "All ESInet/NGCS CPIM-enabled endpoints MUST implement the nickname negotiation feature of RFC 7701 [123] and offer a nickname.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_292": {
        "requirement_text": "The receiving endpoint with presentation functions, which has completed the negotiation for multi-party RTT awareness, SHALL use the source information to present text from the different sources separated in readable groups placed in an approximate relative time order.",
        "document_section": "4.8.1",
        "description": "The receiving endpoint with presentation functions, which has completed the negotiation for multi-party RTT awareness, SHALL use the source information to present text from the different sources separated in readable groups placed in an approximate relative time order.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_293": {
        "requirement_text": "SIP/MSRP session setup with CPIM is specified within the SDP of an INVITE message in the initial conference setup. All endpoints and media intermediaries within an ESInet/NGCS MUST support CPIM.",
        "document_section": "4.7.6",
        "description": "SIP/MSRP session setup with CPIM is specified within the SDP of an INVITE message in the initial conference setup.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_294": {
        "requirement_text": "...Caller location information along with any Additional Data MUST be populated in an Emergency Incident Data Object (EIDO) structure",
        "document_section": "4.7.4",
        "description": "...Caller location information along with any Additional Data MUST be populated in an Emergency Inci...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_295": {
        "requirement_text": "Negotiation of multi-party awareness SHALL be performed by mixers and endpoints at session initiation and modification.",
        "document_section": "4.8.1",
        "description": "Negotiation of multi-party awareness SHALL be performed by mixers and endpoints at session initiation and modification.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_297": {
        "requirement_text": "SIP entities implementing REFER MUST implement RFC 4508 [38] and the Replaces Header Field, RFC 3891 [27].",
        "document_section": "3.1.1.2",
        "description": "SIP entities implementing REFER MUST implement RFC 4508 [38] and the Replaces Header Field, RFC 3891 [27].",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_298": {
        "requirement_text": "The ECRF MUST be used within the ESInet to route calls to the correct PSAP, and by the PSAP to route calls to the correct responders.",
        "document_section": "4.3",
        "description": "The ECRF MUST be used within the ESInet to route calls to the correct PSAP, and by the PSAP to route calls to the correct responders.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_299": {
        "requirement_text": "All elements that implement LoST MUST implement the Call and Incident ID extension.",
        "document_section": "3.4.10.4",
        "description": "All elements that implement LoST MUST implement the Call and Incident ID extension.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_300": {
        "requirement_text": "When there is more than one dequeuer, each dequeuer MUST register with this service.",
        "document_section": "4.2.1.4",
        "description": "When there is more than one dequeuer, each dequeuer MUST register with this service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_303": {
        "requirement_text": "There are multiple references to the Geolocation header field in this document. These references MUST be interpreted to include the possibility of multiple location information.",
        "document_section": "3.2",
        "description": "There are multiple references to the Geolocation header field in this document.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_305": {
        "requirement_text": "NonRtpMediaMessageLogEvent: An element MUST always log messages it receives (with \"direction\" set to \"incoming\").",
        "document_section": "4.12.3.7",
        "description": "NonRtpMediaMessageLogEvent: An element MUST always log messages it receives (with \"direction\" set to \"incoming\").",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_306": {
        "requirement_text": "NonRtpMediaMessageLogEvent: An element MUST log outgoing messages it originates.",
        "document_section": "4.12.3.7",
        "description": "NonRtpMediaMessageLogEvent: An element MUST log outgoing messages it originates.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_307": {
        "requirement_text": "NonRtpMediaMessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "NonRtpMediaMessageLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_308": {
        "requirement_text": "MediaEndLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MediaEndLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_311": {
        "requirement_text": "ElementStateChangeLogEvent: When an element sends a notification of state change as described in the Element State section of this document, it MUST log the ElementStateChangeLogEvent.",
        "document_section": "4.12.3.7",
        "description": "ElementStateChangeLogEvent: When an element sends a notification of state change as described in the Element State section of this document, it MUST log the ElementStateChangeLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_317": {
        "requirement_text": "All agencies and NG9 1 1 functional elements MUST have access to a conformant Logging Service and log all relevant events in that service.",
        "document_section": "4.12.4",
        "description": "All agencies and NG9 1 1 functional elements MUST have access to a conformant Logging Service and log all relevant events in that service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_321": {
        "requirement_text": "RecMediaStartLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecMediaStartLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_322": {
        "requirement_text": "RecordingFailedLogEvent members",
        "document_section": "4.12.3.7",
        "description": "RecordingFailedLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_323": {
        "requirement_text": "ElementStateChangeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "ElementStateChangeLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_324": {
        "requirement_text": "(common LogEvent prologue (base object/header) table)",
        "document_section": "4.12.3.1",
        "description": "(common LogEvent prologue (base object/header) table)",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_325": {
        "requirement_text": "KeepAliveFailureLogEvent: Malformed, invalid, or responses not received from the other element MUST be logged in a \"responseStatus\" member that contains text and a status code from the Status Codes Registry (Section 10.29). There is a TimeOut status in that registry that is used for a timeout failure of OPTIONS.",
        "document_section": "4.12.3.7",
        "description": "KeepAliveFailureLogEvent: Malformed, invalid, or responses not received from the other element MUST be logged in a \"responseStatus\" member that contains text and a status code from the Status Codes Registry (Section 10.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_326": {
        "requirement_text": "KeepAliveFailureLogEvent members",
        "document_section": "4.12.3.7",
        "description": "KeepAliveFailureLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_328": {
        "requirement_text": "All protocol operations MUST be integrity-protected with TLS, using SHA-256 [62] or stronger. SHA-256 MUST be supported by all implementations.",
        "document_section": "5.7",
        "description": "All protocol operations MUST be integrity-protected with TLS, using SHA-256 [62] or stronger.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_329": {
        "requirement_text": "All protocol operations MUST be integrity-protected with TLS, using SHA-256 [62] or stronger. SHA-256 MUST be supported by all implementations.",
        "document_section": "5.7",
        "description": "All protocol operations MUST be integrity-protected with TLS, using SHA-256 [62] or stronger.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_330": {
        "requirement_text": "All protocol operations MUST be privacy protected via TLS, preferably using Advanced Encryption Standard (AES) [63] with a minimum key length of 256 bits (AES-256). Shorter key length MUST NOT be used. Systems currently using Data Encryption Standard (DES) or triple-DES MUST be upgraded to at least AES-256. Alternate encryption algorithms are acceptable as long as they are at least as strong as AES.",
        "document_section": "5.8",
        "description": "All protocol operations MUST be privacy protected via TLS, preferably using Advanced Encryption Standard (AES) [63] with a minimum key length of 256 bits (AES-256).",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_331": {
        "requirement_text": "KeepAliveFailureLogEvent: Malformed, invalid, or responses not received from the other element MUST be logged in a \"responseStatus\" member that contains text and a status code from the Status Codes Registry (Section 10.29). There is a TimeOut status in that registry that is used for a timeout failure of OPTIONS.",
        "document_section": "4.12.3.7",
        "description": "KeepAliveFailureLogEvent: Malformed, invalid, or responses not received from the other element MUST be logged in a \"responseStatus\" member that contains text and a status code from the Status Codes Registry (Section 10.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_332": {
        "requirement_text": "KeepAliveFailureLogEvent members",
        "document_section": "4.12.3.7",
        "description": "KeepAliveFailureLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_333": {
        "requirement_text": "All protocol operations MUST be integrity-protected with TLS, using SHA-256 [62] or stronger. SHA-256 MUST be supported by all implementations.",
        "document_section": "5.7",
        "description": "All protocol operations MUST be integrity-protected with TLS, using SHA-256 [62] or stronger.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_335": {
        "requirement_text": "All protocol operations MUST be privacy protected via TLS, preferably using Advanced Encryption Standard (AES) [63] with a minimum key length of 256 bits (AES-256). Shorter key length MUST NOT be used. Systems currently using Data Encryption Standard (DES) or triple-DES MUST be upgraded to at least AES-256. Alternate encryption algorithms are acceptable as long as they are at least as strong as AES.",
        "document_section": "5.8",
        "description": "All protocol operations MUST be privacy protected via TLS, preferably using Advanced Encryption Standard (AES) [63] with a minimum key length of 256 bits (AES-256).",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_337": {
        "requirement_text": "Logging Services MUST be capable of verifying the signature of a signed LogEvent during the processing of the LogEvent request (i.e., before returning the response). The currently in force policy of the agency operating the Logging Service determines if the Logging Service does so. If the signature verification fails, it MUST return a \"Signature Verification Failed\" status code as a warning and SHOULD generate (subject to throttling) a Signature/Certificate Discrepancy Report (Section 3.7.22) to the logging entity. This is a warning, not an error; the LogEvent MUST be recorded, and the client MUST NOT retry the request.",
        "document_section": "4.12.3.1",
        "description": "Logging Services MUST be capable of verifying the signature of a signed LogEvent during the processing of the LogEvent request (i.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_338": {
        "requirement_text": "(LogEvents POST parameters)",
        "document_section": "4.12.3.1.2",
        "description": "(LogEvents POST parameters)",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_340": {
        "requirement_text": "Logging Services MUST be capable of verifying the signature of a signed LogEvent during the processing of the LogEvent request (i.e., before returning the response). The currently in force policy of the agency operating the Logging Service determines if the Logging Service does so. If the signature verification fails, it MUST return a \"Signature Verification Failed\" status code as a warning and SHOULD generate (subject to throttling) a Signature/Certificate Discrepancy Report (Section 3.7.22) to the logging entity. This is a warning, not an error; the LogEvent MUST be recorded, and the client MUST NOT retry the request.",
        "document_section": "4.12.3.1",
        "description": "Logging Services MUST be capable of verifying the signature of a signed LogEvent during the processing of the LogEvent request (i.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_343": {
        "requirement_text": "MessageLogEvent states: Elements that log Message MUST also log the actual SIP message with CallSignalingMessageLogEvent.",
        "document_section": "",
        "description": "MessageLogEvent states: Elements that log Message MUST also log the actual SIP message with CallSignalingMessageLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_344": {
        "requirement_text": "MessageLogEvent members",
        "document_section": "4.12.3.7",
        "description": "MessageLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_358": {
        "requirement_text": "CallTransferLogEvent members",
        "document_section": "4.12.3.7",
        "description": "CallTransferLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_361": {
        "requirement_text": "LostQueryLogEvent:  A \"queryId\" member is used to relate the request to the response. The id is generated locally, MUST be globally unique",
        "document_section": "4.12.3.7",
        "description": "LostQueryLogEvent:  A \"queryId\" member is used to relate the request to the response.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_363": {
        "requirement_text": "LostResponseLogEvent:  A \"responseId\" member is used to relate the request to the response, and MUST match the id used in the LostQueryLogEvent.",
        "document_section": "4.12.3.7",
        "description": "LostResponseLogEvent:  A \"responseId\" member is used to relate the request to the response, and MUST match the id used in the LostQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_364": {
        "requirement_text": "SubscribeLogEvent: The id is generated locally, MUST be globally unique",
        "document_section": "4.12.3.7",
        "description": "SubscribeLogEvent: The id is generated locally, MUST be globally unique",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_366": {
        "requirement_text": "LocationQueryLogEvent: A \"queryId\" member is used to relate the request or subscription to the response or notifications. The id is generated locally, MUST be globally unique,",
        "document_section": "4.12.3.7",
        "description": "LocationQueryLogEvent: A \"queryId\" member is used to relate the request or subscription to the response or notifications.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_367": {
        "requirement_text": "LocationQueryLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LocationQueryLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_368": {
        "requirement_text": "LocationResponseLogEvent: All clients and servers, if the server is located inside an ESInet, or is an LNG or LSRG operated by, or on behalf of, a 9-1-1 Authority, MUST log responses.",
        "document_section": "4.12.3.7",
        "description": "LocationResponseLogEvent: All clients and servers, if the server is located inside an ESInet, or is an LNG or LSRG operated by, or on behalf of, a 9-1-1 Authority, MUST log responses.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_369": {
        "requirement_text": "LocationResponseLogEvent: A \"responseId\" member is used to relate the request or subscription to the response or notifications and MUST match the id used in the LocationQueryLogEvent.",
        "document_section": "4.12.3.7",
        "description": "LocationResponseLogEvent: A \"responseId\" member is used to relate the request or subscription to the response or notifications and MUST match the id used in the LocationQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_370": {
        "requirement_text": "LocationResponseLogEvent members",
        "document_section": "4.12.3.7",
        "description": "LocationResponseLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_375": {
        "requirement_text": "AdditionalDataResponseLogEvent: A \"responseId\" member is used to relate the request to the response and MUST match the id used in the AdditionalDataQueryLogEvent.",
        "document_section": "4.12.3.7",
        "description": "AdditionalDataResponseLogEvent: A \"responseId\" member is used to relate the request to the response and MUST match the id used in the AdditionalDataQueryLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_378": {
        "requirement_text": "AdditionalAgencyLogEvent members",
        "document_section": "4.12.3.7",
        "description": "AdditionalAgencyLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_379": {
        "requirement_text": "When an agency becomes aware that another agency may be involved, in any way, with a call, it MUST log an AdditionalAgencyLogEvent.",
        "document_section": "4.12.3.7",
        "description": "When an agency becomes aware that another agency may be involved, in any way, with a call, it MUST log an AdditionalAgencyLogEvent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_380": {
        "requirement_text": "IncidentMergeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentMergeLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_381": {
        "requirement_text": "IncidentUnMergeLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentUnMergeLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_382": {
        "requirement_text": "IncidentSplitLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentSplitLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_383": {
        "requirement_text": "IncidentLinkLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentLinkLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_384": {
        "requirement_text": "IncidentUnLinkLogEvent members",
        "document_section": "4.12.3.7",
        "description": "IncidentUnLinkLogEvent members",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_385": {
        "requirement_text": "IncidentClearLogEvent",
        "document_section": "4.12.3.7",
        "description": "IncidentClearLogEvent",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_386": {
        "requirement_text": "IncidentReopenLogEvent",
        "document_section": "4.12.3.7",
        "description": "IncidentReopenLogEvent",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_390": {
        "requirement_text": "Implementations MUST support (be capable of generating and using) algorithm \"EdDSA\" and MUST NOT use other algorithms except that implementations of the Logging Service and clients of the Logging Service MUST support (be capable of generating and using) unsigned (algorithm \"none\")",
        "document_section": "2.8.2",
        "description": "Implementations MUST support (be capable of generating and using) algorithm \"EdDSA\" and MUST NOT use...",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_391": {
        "requirement_text": "Clients MUST appropriately handle all status codes listed for each supported entry point, and MUST react appropriately to other status codes received, based on the first digit as per RFC 7231 [223] Section 6.",
        "document_section": "2.8.3",
        "description": "Clients MUST appropriately handle all status codes listed for each supported entry point, and MUST react appropriately to other status codes received, based on the first digit as per RFC 7231 [223] Section 6.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_392": {
        "requirement_text": "Implementations MUST ignore elements of data structures they do not understand",
        "document_section": "2.9",
        "description": "Implementations MUST ignore elements of data structures they do not understand",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_393": {
        "requirement_text": "Clients MUST retry transactions on redundant elements that that could not be completed on the initial element.",
        "document_section": "2.9",
        "description": "Clients MUST retry transactions on redundant elements that that could not be completed on the initial element.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_394": {
        "requirement_text": "Every implementation MUST be capable of using a DNS based implementation of redundant elements where more than one address may be returned for the URI provided.",
        "document_section": "2.9",
        "description": "Every implementation MUST be capable of using a DNS based implementation of redundant elements where more than one address may be returned for the URI provided.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_395": {
        "requirement_text": "Implementations MUST be capable of preferring the first returned address, and using the second, third and optionally additional addresses returned as representing redundant elements for the service.",
        "document_section": "2.9",
        "description": "Implementations MUST be capable of preferring the first returned address, and using the second, third and optionally additional addresses returned as representing redundant elements for the service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_396": {
        "requirement_text": "Other mechanisms to achieve redundancy MAY be provided, but the DNS based mechanism MUST be supported by all services and clients of those services.",
        "document_section": "3.1.12",
        "description": "Other mechanisms to achieve redundancy MAY be provided, but the DNS based mechanism MUST be supported by all services and clients of those services.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_397": {
        "requirement_text": "All SIP elements in an ESInet/NGCS MUST support multipart MIME as defined in RFC 2046 [90]",
        "document_section": "3.1.12",
        "description": "All SIP elements in an ESInet/NGCS MUST support multipart MIME as defined in RFC 2046 [90]",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_398": {
        "requirement_text": "All SIP elements in the NGCS MUST allow all mime types/body parts to pass to the PSAP",
        "document_section": "3.1.13",
        "description": "All SIP elements in the NGCS MUST allow all mime types/body parts to pass to the PSAP",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_399": {
        "requirement_text": "all SIP elements within the NGCS MUST support connection reuse, RFC 5923 [217].",
        "document_section": "3.1.14",
        "description": "all SIP elements within the NGCS MUST support connection reuse, RFC 5923 [217].",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_400": {
        "requirement_text": "All SIP elements MUST support routing of SIP messages per RFC 3261 [10] and RFC 3263 [13].",
        "document_section": "3.1.14",
        "description": "All SIP elements MUST support routing of SIP messages per RFC 3261 [10] and RFC 3263 [13].",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_401": {
        "requirement_text": "DNS SRV records (RFC 2782) [75] MUST be consulted to determine the hostname of the SIP server for that domain.",
        "document_section": "3.1.17",
        "description": "DNS SRV records (RFC 2782) [75] MUST be consulted to determine the hostname of the SIP server for that domain.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_402": {
        "requirement_text": "all SIP elements MUST implement the overload control mechanisms described in RFC 7339 [56].",
        "document_section": "3.1.18",
        "description": "all SIP elements MUST implement the overload control mechanisms described in RFC 7339 [56].",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_403": {
        "requirement_text": "All elements in an ESInet that implement SIP interfaces MUST comply with RFC 5626 [42] (Outbound) to maintain connections from User Agents.",
        "document_section": "3.1.18",
        "description": "All elements in an ESInet that implement SIP interfaces MUST comply with RFC 5626 [42] (Outbound) to maintain connections from User Agents.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_404": {
        "requirement_text": "PSAPs, IMRs, bridges and other elements that terminate calls from entities outside an ESInet that may be behind NATs MUST implement \"Interactive Connectivity Establishment (ICE)\", RFC 8445 [44] which includes support for \"Session Traversal Utilities for NAT (STUN), RFC 5389 [83].",
        "document_section": "3.1.2.4",
        "description": "PSAPs, IMRs, bridges and other elements that terminate calls from entities outside an ESInet that may be behind NATs MUST implement \"Interactive Connectivity Establishment (ICE)\", RFC 8445 [44] which includes support for \"Session Traversal Utilities for NAT (STUN), RFC 5389 [83].",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_405": {
        "requirement_text": "All endpoints in an ESInet/NGCS MUST use ACK.",
        "document_section": "3.1.2.5",
        "description": "All endpoints in an ESInet/NGCS MUST use ACK.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_406": {
        "requirement_text": "The PRACK method MUST be used within systems that need reliable provisional responses (non 100)",
        "document_section": "3.1.2.6",
        "description": "The PRACK method MUST be used within systems that need reliable provisional responses (non 100)",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_407": {
        "requirement_text": "ESInet elements MUST allow MESSAGE requests in the context of a dialog initiated by some other SIP request.",
        "document_section": "3.1.3.2",
        "description": "ESInet elements MUST allow MESSAGE requests in the context of a dialog initiated by some other SIP request.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_408": {
        "requirement_text": "subscribers MUST refresh subscriptions on a periodic basis using a new SUBSCRIBE message on the same dialog.",
        "document_section": "3.1.3.2",
        "description": "subscribers MUST refresh subscriptions on a periodic basis using a new SUBSCRIBE message on the same dialog.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_409": {
        "requirement_text": "Entities implementing a notifier MUST implement RFC 3857 [26].",
        "document_section": "3.1.7",
        "description": "Entities implementing a notifier MUST implement RFC 3857 [26].",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_410": {
        "requirement_text": "All SIP user agents that place calls within the ESInet/NGCS MUST be able to set Resource-Priority.",
        "document_section": "3.2",
        "description": "All SIP user agents that place calls within the ESInet/NGCS MUST be able to set Resource-Priority.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_411": {
        "requirement_text": "Each element MUST do its own de-reference operation, supplying its credentials to the LIS.",
        "document_section": "3.2",
        "description": "Each element MUST do its own de-reference operation, supplying its credentials to the LIS.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_412": {
        "requirement_text": "NGCS that receive a location reference and forward location in SIP signaling to another element MUST pass the reference, and not any value that they determine by de- referencing (although the value should be logged).",
        "document_section": "3.2",
        "description": "NGCS that receive a location reference and forward location in SIP signaling to another element MUST pass the reference, and not any value that they determine by de- referencing (although the value should be logged).",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_413": {
        "requirement_text": "If additional location is acquired16, a new PIDF-LO with a different <provided-by> element MUST be created and passed in addition to the original location.",
        "document_section": "3.7",
        "description": "If additional location is acquired16, a new PIDF-LO with a different <provided-by> element MUST be created and passed in addition to the original location.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_414": {
        "requirement_text": "The functional elements described in this document MUST support the discrepancy report (DR) function.",
        "document_section": "3.7",
        "description": "The functional elements described in this document MUST support the discrepancy report (DR) function.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_415": {
        "requirement_text": "Each database, service, and agency MUST provide a Discrepancy Reporting web service.",
        "document_section": "5.10",
        "description": "Each database, service, and agency MUST provide a Discrepancy Reporting web service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_416": {
        "requirement_text": "If a Web Service request receives an \"Unacceptable Algorithm\" error, the client MUST make a new request on the Versions entry point and retry the request with a JWS that uses a signing algorithm acceptable to the Web Service.",
        "document_section": "5.10",
        "description": "If a Web Service request receives an \"Unacceptable Algorithm\" error, the client MUST make a new request on the Versions entry point and retry the request with a JWS that uses a signing algorithm acceptable to the Web Service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_417": {
        "requirement_text": "When this document indicates that a set of Web Service interface parameters is a JWS (e.g., for LogEvents), the set of parameters is conveyed in the web service request as a string consisting of a JWS. The JWS is formed by applying the JWS algorithm to the set of parameters per the JWS standard [171].; The JWS Protected Header MUST contain exactly one \"alg\" field. The \"alg\" field MUST have a value acceptable to the Web Service.; An unsigned (unprotected) JWS is indicated by an \"alg\" field set to the value \"none\".; For signed LogEvents, and all other uses of JWS requiring signatures (e.g., policy documents), the JWS Protected Header MUST have its \"alg\" field set to a value acceptable to the Web Service that MUST NOT be \"none\" and MUST specify the signing entity's X.509 certificate and all intermediate certificates up to one signed by the trusted root58. The certificate is provided either by reference or by value. A certificate provided by value is contained in an \"x5c\" field. A certificate is provided by reference using the \"x5u\" and \"x5t#256\" fields. When the \"x5u\" field is present, it MUST contain a URL that is stable (resolvable) for a minimum of 10 years. The JWS Protected Header MAY contain other fields. Including a certificate (with chain) in each LogEvent increases the size of the event (in some cases by a multiple of the event size) but avoids the additional network requests necessary to retrieve the certificate chain using the \"x5u\" field. When the \"x5u\" field is used, the \"x5t#256\" field MUST also be used, to allow an entity to more easily detect when a certificate chain needs to be retrieved.",
        "document_section": "5.10",
        "description": "When this document indicates that a set of Web Service interface parameters is a JWS (e.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_418": {
        "requirement_text": "a JWS MUST use the Flat JSON serialization format (not JWS Compact Serialization and not General JWS JSON Serialization Syntax), and only the Edwards-curve Digital Signature Algorithm (ECDSA) with Curve448 (algorithm \"EdDSA\") [227] [228] signature method is used.",
        "document_section": "5.10",
        "description": "a JWS MUST use the Flat JSON serialization format (not JWS Compact Serialization and not General JWS JSON Serialization Syntax), and only the Edwards-curve Digital Signature Algorithm (ECDSA) with Curve448 (algorithm \"EdDSA\") [227] [228] signature method is used.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_028": {
        "requirement_text": "PSAPs MUST provide a RoutePolicy in the upstream PRF for the queue(s) to which its calls are sent.",
        "document_section": "4.6.14",
        "description": "PSAPs MUST provide a RoutePolicy in the upstream PRF for the queue(s) to which its calls are sent.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_029": {
        "requirement_text": "PSAPs MUST also provide an Enqueuer policy to specify which entities are allowed to send it calls.",
        "document_section": "4.6.14",
        "description": "PSAPs MUST also provide an Enqueuer policy to specify which entities are allowed to send it calls.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_039": {
        "requirement_text": "If the calling device does not support the Replaces header field, then a B2BUA in the path MUST be present which does support the Replaces header field in an ESInet supporting ad hoc bridging.",
        "document_section": "4.7.1",
        "description": "If the calling device does not support the Replaces header field, then a B2BUA in the path MUST be present which does support the Replaces header field in an ESInet supporting ad hoc bridging.",
        "test_id": "",
        "subtests": []
    },
    "RQ_CHFE_050": {
        "requirement_text": "The caller, or some element in the path, MUST implement the Replaces header field (see Section 3.1.1.2).",
        "document_section": "4.7.1",
        "description": "The caller, or some element in the path, MUST implement the Replaces header field (see Section 3.",
        "test_id": "",
        "subtests": []
    }
}