REQUIREMENTS_SCHEMA = {
        "RQ_BRIDGE_001": {
            "requirement_text": "Bridges MUST be multimedia capable (voice, video, text).",
            "document_section": "4.7",
            "description": "Bridges must support multimedia communication, including voice, video, and text.",
            "test_id": "BRIDGE_001",
            "subtests": []
        },
        "RQ_BRIDGE_002": {
            "requirement_text": "If the calling device does not support the Replaces header field, then a B2BUA in the path MUST be present which does support the Replaces header field in an ESInet supporting ad hoc bridging.",
            "document_section": "4.7.1",
            "description": "A B2BUA supporting the Replaces header is required if the calling device doesn’t.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_003": {
            "requirement_text": "If the B2BUA receives an INVITE from a caller that does not include a Supported header field containing the “replaces” option-tag, it MUST include a Supported header field containing the “replaces” option-tag in the INVITE forwarded to the ESInet and provide the functionality described in this section.",
            "document_section": "4.7.1",
            "description": "B2BUA must add the “replaces” option-tag to the INVITE if it’s missing from the caller’s INVITE.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_004": {
            "requirement_text": "All Bridges in the ESInet/NGCS MUST implement the Session Recording Client interface defined by SIPREC (RFC 7866).",
            "document_section": "4.7.1",
            "description": "All bridges in ESInet/NGCS must implement the SIPREC Session Recording Client interface.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_005": {
            "requirement_text": "When the bridge is used to transfer the call, the location of the caller and any Additional Data included (or retrieved in conjunction) with the call MUST be transferred to the transfer target.",
            "document_section": "4.7.1",
            "description": "Caller’s location and additional data must be transferred with the call when using the bridge.",
            "test_id": "BRIDGE_999",
            "subtests": []
        },
        "RQ_BRIDGE_006": {
            "requirement_text": "The emergency-Call Identifier and the emergency-Incident Tracking Identifier MUST be copied from the REFER to the outgoing INVITE.",
            "document_section": "4.7.1",
            "description": "Emergency-Call and Incident Tracking Identifiers must be copied from the REFER to the INVITE.",
            "test_id": "BRIDGE_999",
            "subtests": []
        },
        "RQ_BRIDGE_007": {
            "requirement_text": "The REFER MUST contain a suitable URN, usually the urn used to query the ECRF to determine the correct responder, or an appropriate urn from the urn:emergency:service:responder tree if a specific responder was selected, a ‘serviceurn’ parameter of the Refer-To.",
            "document_section": "4.7.1",
            "description": "The REFER must contain a URN to identify the correct responder or service.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_008": {
            "requirement_text": "The Refer-To header field contains the URI of the target (which may be returned from a LoST query) and MUST contain the URN (in the urn:service:sos or urn:emergency:service:sos trees) as a URI parameter of ‘serviceurn’.",
            "document_section": "4.7.1",
            "description": "The Refer-To header must include a service URN as a URI parameter.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_009": {
            "requirement_text": "When the INVITE is created by the bridge to the secondary PSAP, the INVITE MUST contain the service URN in the Request-URI, with a Route header field containing the URI (which should include the “lr” parameter to avoid Request-URI rewriting) found in the Refer-To header field...",
            "document_section": "4.7.1",
            "description": "INVITE to the secondary PSAP must include service URN and Route header as per Refer-To.",
            "test_id": "BRIDGE_999",
            "subtests": []
        },
        "RQ_BRIDGE_010": {
            "requirement_text": "...and MUST contain a Referred-By header field with the URI of the primary PSAP per RFC 3892. S/MIME protection of the referrer is OPTIONAL.",
            "document_section": "4.7.1",
            "description": "INVITE must include the Referred-By header with the primary PSAP URI, S/MIME protection is optional.",
            "test_id": "BRIDGE_999",
            "subtests": []
        },
        "RQ_BRIDGE_011": {
            "requirement_text": "...the Refer-To header field MUST be a sip URI. Tel URIs do not support purpose parameters.",
            "document_section": "4.7.1",
            "description": "The Refer-To header must use a sip URI, Tel URIs don’t support purpose parameters.",
            "test_id": "BRIDGE_999",
            "subtests": []
        },
        "RQ_BRIDGE_012": {
            "requirement_text": "The bridge is a service: each element of the bridge MUST implement the server-side of ElementState and the set of bridge elements MUST implement the server-side of ServiceState.",
            "document_section": "4.7.1",
            "description": "Each bridge element must implement server-side ElementState and ServiceState.",
            "test_id": "BRIDGE_002",
            "subtests": []
        },
        "RQ_BRIDGE_013": {
            "requirement_text": "For the Ad Hoc case, the transfer-to PSAP MUST release the bridge when the transfer-from PSAP terminates its leg of the call in order to release bridge resources.",
            "document_section": "4.7.1",
            "description": "The transfer-to PSAP must release the bridge when the transfer-from PSAP ends its call leg.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_014": {
            "requirement_text": "The caller, or some element in the path, MUST implement the Replaces header field (see Section 3.1.1.2).",
            "document_section": "4.7.1",
            "description": "The caller or a path element must implement the Replaces header field.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_015": {
            "requirement_text": "For a blind transfer in ESInets using the ad hoc method, the transferring PSAP SHALL NOT seize the bridge prior to initiating a blind transfer.",
            "document_section": "4.7.2",
            "description": "In ad hoc transfers, the transferring PSAP must not seize the bridge before initiating a blind transfer.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_016": {
            "requirement_text": "The transfer-from PSAP MUST send a REFER where the Request Line contains the caller information.",
            "document_section": "4.7.2",
            "description": "The transfer-from PSAP must include caller information in the REFER's Request Line.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_017": {
            "requirement_text": "The Refer-To header field MUST specify the transfer-to PSAP (or any other entity): for consistency with Bridging and Attended transfer…",
            "document_section": "4.7.2",
            "description": "The Refer-To header must specify the transfer-to PSAP for consistency with transfer protocols.",
            "test_id": "BRIDGE_999",
            "subtests": []
        },
        "RQ_BRIDGE_018": {
            "requirement_text": "Once the REFER is successfully acknowledged with a 200 OK, the recipient of the REFER will send notifications of the status of the adding the target participant. It MAY send a notification containing a 100 Trying to indicate the transfer is pending. It MAY also send additional provisional messages, e.g. 183 Session Progress. It MUST send a 200 OK indicating that the party was successfully added.",
            "document_section": "4.7.2",
            "description": "After successful REFER, the recipient must send status notifications, including a 200 OK.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_021": {
            "requirement_text": "...Caller location information along with any Additional Data MUST be populated in an Emergency Incident Data Object (EIDO) structure (see Section 7 for further discussion of Additional Data structures). When an emergency call is transferred, the transferring PSAP will request that the bridge insert a reference to the EIDO via an embedded Call-Info header field with a URI that points to the EIDO data structure in the REFER method sent to the bridge, and a purpose parameter of “emergency-eido”. See the example of the associated header fields in 4.7.1 above. The bridge MUST subsequently include this Call-Info header field in the INVITE it sends to the transfer target.",
            "document_section": "4.7.4",
            "description": "Caller’s location and additional data must be included in an Emergency Incident Data Object (EIDO) during transfers.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_023": {
            "requirement_text": "The EIDO MUST be passed by reference when the Call-Info header field contains a URL that, when dereferenced, yields the EIDO.",
            "document_section": "4.7.4",
            "description": "The EIDO must be referenced in the Call-Info header to ensure it’s passed along during the transfer.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_024": {
            "requirement_text": "To dereference the URI and obtain the EIDO, the recipient initiates an HTTPS: GET on the URI and the EIDO [111] is returned. The GET request MUST contain an ‘Accept:’ header field which specifies the MIME type assigned to EIDO (application/emergency.eido+json) and MUST include as a parameter a comma-delimited list of the major version(s) of the schema the client supports (for example ‘Accept: application/emergency.eido+json;version=\"1,2,3\"’).",
            "document_section": "4.7.4",
            "description": "Dereferencing the EIDO URI involves initiating an HTTPS GET request with an Accept header specifying the correct MIME type.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_025": {
            "requirement_text": "If the server can fulfil the request, the response MUST include one and only one EIDO instance in the body of the reply.",
            "document_section": "4.7.4",
            "description": "A successful GET request must return exactly one EIDO instance in the response body.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_026": {
            "requirement_text": "The client MUST expect to receive an object derived from any minor version of the specified EIDO schema, including a higher minor version than it currently supports.",
            "document_section": "4.7.4",
            "description": "The client must handle any minor version of the EIDO schema, including higher versions than currently supported.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_027": {
            "requirement_text": "The client MUST ignore any fields it does not understand.",
            "document_section": "4.7.4",
            "description": "Clients must ignore fields in the EIDO they do not understand.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_028": {
            "requirement_text": "If the server does not support any of the major versions found in the ‘Accept:’ header field of the GET request, it MUST return a 406 Not Acceptable response.",
            "document_section": "4.7.4",
            "description": "A 406 Not Acceptable response must be returned if the server doesn’t support requested major EIDO versions.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_029": {
            "requirement_text": "Because some user devices do not currently support CPIM, the NG9-1-1 conference bridge MUST emulate what a CPIM-enabled device would do to appropriately interwork (e.g., label) text from other participants.",
            "document_section": "4.7.6",
            "description": "The conference bridge must emulate CPIM behavior when devices do not support it for text interworking.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_030": {
            "requirement_text": "All ESInet/NGCS CPIM-enabled endpoints MUST implement the nickname negotiation feature of RFC 7701 [123] and offer a nickname.",
            "document_section": "4.7.6",
            "description": "CPIM-enabled ESInet/NGCS endpoints must implement and offer nickname negotiation.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_031": {
            "requirement_text": "SIP/MSRP session setup with CPIM is specified within the SDP of an INVITE message in the initial conference setup. All endpoints and media intermediaries within an ESInet/NGCS MUST support CPIM.",
            "document_section": "4.7.6",
            "description": "CPIM session setup is specified in the SDP of the INVITE, and all endpoints must support it.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_032": {
            "requirement_text": "The RTCP SDES report SHOULD contain identification of the source represented by the CSRC identifier. This identification MUST contain the CNAME field and MAY contain the NAME field and other defined fields of the SDES report.",
            "document_section": "4.8",
            "description": "The RTCP SDES report should contain CNAME identification and may include additional fields like NAME.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_033": {
            "requirement_text": "All NG9-1-1 implementations MUST supply identity information in this manner to the bridge.",
            "document_section": "4.8",
            "description": "All NG9-1-1 implementations must provide identity information to the bridge.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_034": {
            "requirement_text": "The bridge MUST convey SDES information received from the sources of the session members.",
            "document_section": "4.8",
            "description": "The bridge must forward SDES information received from session sources.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_035": {
            "requirement_text": "When such information is not available, the focus UA MUST compose CSRC, CNAME, and NAME information from available information from the SIP session (From and P-A-I) with the participant.",
            "document_section": "4.8",
            "description": "When SDES information is unavailable, the focus UA must generate CSRC, CNAME, and NAME from session info.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_036": {
            "requirement_text": "Transport of real-time text is originally specified in RFC 4103 [85]. Multi-party handling for real-time text is described in RFC 9071 [219], which updates RFC 4103. The Mixer function of the Bridge MUST implement these mechanisms for both multi-party aware and multi-party unaware end devices.",
            "document_section": "4.8.1",
            "description": "The bridge must handle real-time text transport as per RFC 4103, supporting multi-party aware and unaware devices.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_037": {
            "requirement_text": "Negotiation of multi-party awareness SHALL be performed by mixers and endpoints at session initiation and modification.",
            "document_section": "4.8.1",
            "description": "Multi-party awareness negotiation is performed by mixers and endpoints during session initiation and modification.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_038": {
            "requirement_text": "If both parties declare multi-party capability awareness, the mixer SHALL apply the mixing procedures for multi-party awareness as defined in RFC 9071 [219].",
            "document_section": "4.8.1",
            "description": "If both parties support multi-party awareness, the mixer applies appropriate mixing procedures.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_039": {
            "requirement_text": "In all other cases, the mixer SHALL apply the limited functionality mixing procedures for multi-party unaware participants as defined in RFC 9071 [219].",
            "document_section": "4.8.1",
            "description": "The mixer applies limited functionality for participants who are unaware of multi-party RTT.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_040": {
            "requirement_text": "The receiving endpoint with presentation functions, which has completed the negotiation for multi-party RTT awareness, SHALL use the source information to present text from the different sources separated in readable groups placed in an approximate relative time order.",
            "document_section": "4.8.1",
            "description": "Endpoints with multi-party RTT awareness must present text from different sources in readable time-ordered groups.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_041": {
            "requirement_text": "For the case when the multi-party awareness negotiation was unsuccessful, the mixer SHALL compose a simulated limited multi-party RTT view suitable for presentation.",
            "document_section": "4.8.1",
            "description": "If multi-party RTT awareness negotiation fails, the mixer simulates a limited multi-party RTT view.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_042": {
            "requirement_text": "Mixers SHALL be capable of handling both multi-party aware and multi-party unaware endpoints in the same multi-party session.",
            "document_section": "4.8.1",
            "description": "Mixers must support both multi-party aware and unaware endpoints within the same session.",
            "test_id": "",
            "subtests": []
        },
        "RQ_BRIDGE_043": {
            "requirement_text": "The downstream bridge MUST release the upstream bridge resources when no active call legs in the Upstream ESInet remain.",
            "document_section": "4.9.3",
            "description": "The downstream bridge must release upstream bridge resources when no active call legs remain.",
            "test_id": "",
            "subtests": []
        }
}