REQUIREMENTS_SCHEMA = {
    "RQ_ESRP_001": {
        "requirement_text": "If calls transferred to a PSAP are to be policy-routed, then the URI in the ECRF SHALL point to a queue.",
        "document_section": "4.2.1.1",
        "description": "Calls routed to a PSAP must follow policy routing by directing the URI in the ECRF to a queue.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_002": {
        "requirement_text": "A unique Queue Identifier identifies a queue. A queue is normally managed by an ESRP or PSAP. A call sent to the queue URI MUST route to the entity that manages it.",
        "document_section": "4.2.1.2",
        "description": "A queue is identified by a unique Queue Identifier, which ensures the call is routed to the appropriate managing entity (ESRP or PSAP).",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_003": {
        "requirement_text": "Each queue MUST have a unique URI that routes to the ESRP.",
        "document_section": "4.2.1.2",
        "description": "Each queue must have a unique URI that directs calls to the ESRP managing it.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_004": {
        "requirement_text": "Each ESRP element SHALL maintain a QueueState notifier and track the number of calls in queue for the queues that it manages.",
        "document_section": "4.2.1.2",
        "description": "The ESRP must track the number of calls in its managed queues using a QueueState notifier.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_005": {
        "requirement_text": "Changing the ServiceState MUST change the state of all Queues implemented by the Service to an appropriate QueueState (for example if ServiceState is set to Unstaffed, underlying QueueState values become Disabled).",
        "document_section": "4.2.1.2",
        "description": "Changes to ServiceState must be reflected in the states of all associated queues, adjusting their QueueState accordingly.",
        "test_id": "ESRP_001",
        "subtests": []
    },
    "RQ_ESRP_006": {
        "requirement_text": "The registry includes the value “unreachable”, which MUST NOT be returned in a NOTIFY.",
        "document_section": "4.2.1.3",
        "description": "The \"unreachable\" value in the registry must never be returned in a NOTIFY message.",
        "test_id": "ESRP_001",
        "subtests": []
    },
    "RQ_ESRP_007": {
        "requirement_text": "QueueState is NOT REQUIRED to be implemented on simple routing proxy or when queue length is 1 and only one dequeuer is permitted. QueueState MUST reflect the state of the (ESRP or PSAP) service state.",
        "document_section": "4.2.1.3",
        "description": "QueueState is not required for simple routing proxies or queues with a single dequeuer, but it must reflect the ESRP or PSAP's service state.",
        "test_id": "ESRP_001",
        "subtests": []
    },
    "RQ_ESRP_008": {
        "requirement_text": "If the ESRP is down, all of its queues MUST show a state matching the reason the service is not available.",
        "document_section": "4.2.1.3",
        "description": "If the ESRP is down, the queues it manages must reflect the reason for the service's unavailability.",
        "test_id": "ESRP_001",
        "subtests": []
    },
    "RQ_ESRP_009": {
        "requirement_text": "Forking between elements MUST NOT be used.",
        "document_section": "4.2.1.3",
        "description": "Forking between elements is prohibited in the routing process.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_010": {
        "requirement_text": "The subscriber can control the rate of notifications using the filter rate control (RFC 6446) [80]. The default throttle rate is one notification per second. The default force rate is one notification per minute. The Notifier MUST be capable of generating NOTIFYs at the maximum busy second call rate to the maximum number of downstream dequeueing entities, plus at least 10 other subscribers.",
        "document_section": "4.2.1.3",
        "description": "Subscribers can control the rate of notifications using filter rate control, with default settings of one per second and one per minute, but the Notifier must handle a maximum busy second call rate.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_011": {
        "requirement_text": "An ESRP that dequeues a call, sends it to a downstream entity, and receives a 486 Busy Here in return, MUST continue evaluating the existing rule set per Section 3.3.3.2.1.",
        "document_section": "4.2.1.3",
        "description": "If an ESRP receives a 486 Busy response after dequeuing a call, it must continue evaluating the rule set.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_013": {
        "requirement_text": "Often, an ESRP or PSAP will manage a queue for which it is the only dequeuer; explicit DequeueRegistration for a single dequeuer is NOT REQUIRED. When there is more than one dequeuer, each dequeuer MUST register with this service.",
        "document_section": "4.2.1.4",
        "description": "When an ESRP or PSAP manages a queue with a single dequeuer, explicit DequeueRegistration is not needed; multiple dequeuers require registration.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_014": {
        "requirement_text": "When dequeueing calls, the ESRP MUST send calls to the highest DequeuePreference entity available to take the call when it reaches the head of the queue.",
        "document_section": "4.2.1.4",
        "description": "The ESRP must send calls to the highest preference entity available when dequeuing calls from the queue.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_015": {
        "requirement_text": "The rule that has the LostServiceUrnCondition MUST contain an action \"InvokePolicyAction\" which uses the NormalNexthopRoutePolicy for <policyType>, and results in executing the rule set associated with the policy identified by the Normal-NextHop URI.",
        "document_section": "4.2.1.5",
        "description": "A rule with a LostServiceUrnCondition must invoke a policy action that uses the NormalNexthopRoutePolicy to execute the rule set associated with the Normal-NextHop URI.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_016": {
        "requirement_text": "Forking between elements MUST NOT be used.",
        "document_section": "4.2.1.6",
        "description": "Forking between elements is prohibited in the call routing process.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_017": {
        "requirement_text": "Each ESRP MUST be capable of receiving location as a value or a reference and MUST be provisioned with credentials suitable to present to any LIS in its service area to be able to dereference a location reference using either SIP or HELD.",
        "document_section": "4.2.1.7",
        "description": "Each ESRP must be capable of receiving and dereferencing location data using SIP or HELD, with proper credentials for the LIS in its service area.",
        "test_id": "ESRP_002",
        "subtests": []
    },
    "RQ_ESRP_018": {
        "requirement_text": "Each ESRP MUST be capable of receiving location as a value or a reference and MUST be provisioned with credentials suitable to present to any LIS in its service area to be able to dereference a location reference using either SIP or HELD.",
        "document_section": "4.2.1.7",
        "description": "The ESRP must handle location references and ensure proper credentials to dereference them from any LIS.",
        "test_id": "ESRP_002",
        "subtests": []
    },
    "RQ_ESRP_019": {
        "requirement_text": "The ESRP MUST be able to handle emergency calls with problems in location.",
        "document_section": "4.2.1.7",
        "description": "The ESRP must be able to manage emergency calls even if location information is problematic.",
        "test_id": "ESRP_003",
        "subtests": []
    },
    "RQ_ESRP_021": {
        "requirement_text": "A PIDF-LO containing a Default Location MUST have its <method> element set to the value “Default”, and its <provided-by> element set to the identity of the NGCS provider that inserted it. The location elements MUST be populated to a level that yields an appropriate route URI in the LoST response from the ECRF.",
        "document_section": "4.2.1.7",
        "description": "A PIDF-LO with a default location must include the method \"Default\" and the identity of the NGCS provider in the provided-by element, ensuring the location elements generate an appropriate route URI from the ECRF's LoST response.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_022": {
        "requirement_text": "The ESRP SHALL perform the following procedures when handling a default location: The ESRP SHALL preserve the original Geolocation header field values and PIDF-LO documents in the original INVITE;",
        "document_section": "4.2.1.7",
        "description": "When handling a default location, the ESRP must preserve the original Geolocation header values and PIDF-LO documents from the original INVITE.",
        "test_id": "ESRP_003",
        "subtests": []
    },
    "RQ_ESRP_023": {
        "requirement_text": "The ESRP SHALL perform the following procedures when handling a default location: If there is no Geolocation header field, the ESRP SHALL add the default location PIDF-LO document in the body of the INVITE (to do so, the ESRP MUST behave as a B2BUA), and add a Geolocation header field populated with a “cid” URI pointing to it;",
        "document_section": "4.2.1.7",
        "description": "If no Geolocation header exists, the ESRP must add the default location PIDF-LO to the INVITE body, act as a B2BUA, and include a Geolocation header with a \"cid\" URI pointing to it.",
        "test_id": "ESRP_003",
        "subtests": []
    },
    "RQ_ESRP_024": {
        "requirement_text": "The ESRP SHALL perform the following procedures when handling a default location: If there is a Geolocation header field value in the original INVITE (but no associated body part), a new one is created and placed as the top-most entry of the Geolocation field sequence;",
        "document_section": "4.2.1.7",
        "description": "If the original INVITE has a Geolocation header but lacks a body, the ESRP must create a new Geolocation entry and place it at the top of the sequence.",
        "test_id": "ESRP_003",
        "subtests": []
    },
    "RQ_ESRP_025": {
        "requirement_text": "The ESRP SHALL perform the following procedures when handling a default location: If the original INVITE contained a garbled PIDF-LO, the ESRP SHALL add a new body part with the default location PIDF-LO (to do so, the ESRP MUST behave as a B2BUA) and add a new Geolocation header field with a “cid” URI pointing to it as top-most entry of the Geolocation field sequence, retaining the garbled one;",
        "document_section": "4.2.1.7",
        "description": "If the INVITE contains a garbled PIDF-LO, the ESRP must add the default location PIDF-LO, behave as a B2BUA, and include a new Geolocation header with a \"cid\" URI, while retaining the original garbled one.",
        "test_id": "ESRP_003",
        "subtests": []
    },
    "RQ_ESRP_026": {
        "requirement_text": "The ESRP SHALL perform the following procedures when handling a default location: If the original INVITE contained a garbled location reference in the Geolocation header field, or the location dereferencing timed out or yielded a garbled PIDF-LO document, the ESRP SHALL add a new body part with the default location PIDF-LO document (to do so, the ESRP MUST behave as a B2BUA) and add a new Geolocation header field with a “cid” URI pointing to it as top-most entry of the Geolocation field sequence, retaining the garbled one;",
        "document_section": "4.2.1.7",
        "description": "If the Geolocation header contains a garbled location reference or the dereferencing fails, the ESRP must add the default location PIDF-LO and a new Geolocation header with a \"cid\" URI, keeping the original invalid reference.",
        "test_id": "ESRP_003",
        "subtests": []
    },
    "RQ_ESRP_027": {
        "requirement_text": "The ESRP SHALL perform the following procedures when handling a default location: Once the INVITE has been groomed with a usable location for routing, albeit a default one, the ESRP MUST reprocess the Origination-Policy rule, including the LoSTServiceURN condition. Normal call processing ensued thereafter as described below.",
        "document_section": "4.2.1.7",
        "description": "After adding a default location, the ESRP must reprocess the Origination-Policy rule, including the LoSTServiceURN condition, before proceeding with normal call processing.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_028": {
        "requirement_text": "If all rules fail then the ESRP MUST invoke the Fatal Error ruleset (see section 4.2.1.6).",
        "document_section": "4.2.1.7",
        "description": "If all rules fail, the ESRP must invoke the Fatal Error ruleset.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_029": {
        "requirement_text": "If a default location is used to determine the route for the emergency call, the ESRP SHALL pass the location information received in incoming signaling forward in the outgoing SIP INVITE/MESSAGE.",
        "document_section": "4.2.1.7",
        "description": "The ESRP must forward the location information from incoming signaling in the outgoing SIP INVITE/MESSAGE if a default location is used for routing the emergency call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_030": {
        "requirement_text": "..is used to try these alternate IP addresses. Should no entity respond, the ESRP MUST reevaluate the ruleset with the rule which failed, interpreted as not satisfying its conditions.",
        "document_section": "4.2.1.7",
        "description": "If no entity responds to alternate IP addresses, the ESRP must reevaluate the ruleset with the failed rule as not satisfying its conditions.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_031": {
        "requirement_text": "Calls to an administrative number are recognized by the value in the To header. Administrative calls do not have location, so they MUST be routed using a provisioned table in the ESRP that associates the called number or sip URI to a URI of a queue in the ESRP.",
        "document_section": "4.2.1.7",
        "description": "Calls to administrative numbers, which do not have location data, must be routed using a provisioned table in the ESRP that associates the number or SIP URI to a queue URI.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_032": {
        "requirement_text": "An ESRP MUST process BYEs per RFC 3261.",
        "document_section": "4.2.1.8",
        "description": "The ESRP must process BYE messages according to RFC 3261.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_033": {
        "requirement_text": "An ESRP MUST process CANCELs per RFC 3261.",
        "document_section": "4.2.1.9",
        "description": "The ESRP must process CANCEL messages according to RFC 3261.",
        "test_id": "ESRP_004",
        "subtests": []
    },
    "RQ_ESRP_034": {
        "requirement_text": "An ESRP MUST process OPTIONS transactions per RFC 3261.",
        "document_section": "4.2.1.10",
        "description": "The ESRP must process OPTIONS transactions according to RFC 3261.",
        "test_id": "ESRP_004",
        "subtests": []
    },
    "RQ_ESRP_035": {
        "requirement_text": "If the downstream entity is not reachable, the ESRP MUST treat its queues as Inactive.",
        "document_section": "4.2.1.10",
        "description": "If the downstream entity is unreachable, the ESRP must mark its queues as inactive.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_036": {
        "requirement_text": "The upstream SIP call interface for the originating ESRP must only assume the minimal methods and header fields as defined in Section 3.1.1, but MUST handle any valid SIP transaction.",
        "document_section": "4.2.2.1",
        "description": "The originating ESRP must handle only the minimal methods and header fields specified in Section 3.1.1 but must be capable of handling any valid SIP transaction.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_037": {
        "requirement_text": "All other ESRPs MUST handle all methods and SIP header fields.",
        "document_section": "4.2.2.1",
        "description": "All other ESRPs must support all SIP methods and header fields.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_038": {
        "requirement_text": "The ESRP MUST respond to the URI returned by the ECRF and/or specified in a Route action for a rule for the upstream service the ESRP receives calls from.",
        "document_section": "4.2.2.1",
        "description": "The ESRP must respond to the URI returned by the ECRF or specified in a Route action for the upstream service receiving calls from the ESRP.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_039": {
        "requirement_text": "The upstream interface on the originating ESRP MUST support UDP, TCP, and TCP/TLS and MAY support SCTP transports.",
        "document_section": "4.2.2.1",
        "description": "The upstream interface of the originating ESRP must support UDP, TCP, and TCP/TLS, with SCTP support optional.",
        "test_id": "ESRP_005",
        "subtests": []
    },
    "RQ_ESRP_040": {
        "requirement_text": "The upstream interface on other ESRPs MUST implement TCP/TLS but MUST be capable of fallback to UDP. SCTP support is OPTIONAL.",
        "document_section": "4.2.2.1",
        "description": "The upstream interface on other ESRPs must implement TCP/TLS, with fallback support for UDP, and optional SCTP support.",
        "test_id": "ESRP_005",
        "subtests": []
    },
    "RQ_ESRP_041": {
        "requirement_text": "The downstream SIP call interface MUST implement all SIP methods to be able to propagate any method invoked on the upstream call interface.",
        "document_section": "4.2.2.2",
        "description": "The downstream SIP call interface must implement all SIP methods to propagate any method invoked on the upstream call interface.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_042": {
        "requirement_text": "The INVITE transaction exiting the ESRP MUST include a Via header field specifying the ESRP.",
        "document_section": "4.2.2.2",
        "description": "The INVITE transaction leaving the ESRP must include a Via header field specifying the ESRP.",
        "test_id": "ESRP_006",
        "subtests": []
    },
    "RQ_ESRP_043": {
        "requirement_text": "It MUST include a Route header field containing a URI (which should contain the \"lr\" parameter to avoid Request-URI rewriting) of the downstream queue that receives the call.",
        "document_section": "4.2.2.2",
        "description": "It must include a Route header field with a URI containing the \"lr\" parameter (to avoid Request-URI rewriting) of the downstream queue that will receive the call.",
        "test_id": "ESRP_006",
        "subtests": []
    },
    "RQ_ESRP_044": {
        "requirement_text": "The Request-URI remains “urn:service:sos” (although the ESRP may not depend on that; a call presented to an ESRP that is not recognized as an emergency call, for example, a call to an admin line, MUST be treated as an emergency call and its occurrence logged) and it replaces the top Route header field with the next hop URI (this is described in RFC 6881).",
        "document_section": "4.2.2.2",
        "description": "The Request-URI must remain \"urn:service:sos\" (though the ESRP may not depend on this; if the call is not recognized as emergency, such as a call to an admin line, it must be treated as an emergency call, and its occurrence must be logged). The top Route header field must be replaced with the next hop URI, as described in RFC 6881.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_045": {
        "requirement_text": "Thus, the first ESRP in the path MUST add a Call-Info header field, if one is not already present, with a purpose parameter of “emergency-IncidentId” and a new Incident Tracking Identifier per Section 2.1.7.",
        "document_section": "4.2.2.2",
        "description": "The first ESRP in the path must add a Call-Info header field, if absent, with a \"purpose\" parameter of \"emergency-IncidentId\" and a new Incident Tracking Identifier, as outlined in Section 2.1.7.",
        "test_id": "ESRP_006",
        "subtests": []
    },
    "RQ_ESRP_046": {
        "requirement_text": "The ESRP MUST also create a new Call identifier (Section 2.1.6) and add a Call-Info header field with a purpose parameter of “emergency-CallId” if one is not already present.",
        "document_section": "4.2.2.2",
        "description": "The ESRP must also create a new Call Identifier (Section 2.1.6) and add a Call-Info header field with a \"purpose\" parameter of \"emergency-CallId\" if one is not already present.",
        "test_id": "ESRP_006",
        "subtests": []
    },
    "RQ_ESRP_047": {
        "requirement_text": "The downstream interface MUST implement TCP/TLS towards downstream elements but MUST be capable of fallback to UDP. SCTP support is OPTIONAL.",
        "document_section": "4.2.2.2",
        "description": "The downstream interface must implement TCP/TLS towards downstream elements but should be capable of fallback to UDP. SCTP support is optional.",
        "test_id": "ESRP_005",
        "subtests": []
    },
    "RQ_ESRP_048": {
        "requirement_text": "An ESRP MAY NOT remove header fields received in the upstream call interface; all header fields in the upstream message MUST be copied to the downstream interface except as required in the relevant RFCs.",
        "document_section": "4.2.2.2",
        "description": "The ESRP must not remove header fields received on the upstream call interface; all upstream message header fields must be copied to the downstream interface, except as required by the relevant RFCs.",
        "test_id": "ESRP_006",
        "subtests": []
    },
    "RQ_ESRP_049": {
        "requirement_text": "The ESRP MUST implement a LoST interface towards a (provisioned) ECRF.",
        "document_section": "4.2.2.3",
        "description": "The ESRP must implement a LoST interface toward a (provisioned) ECRF.",
        "test_id": "ESRP_006",
        "subtests": []
    },
    "RQ_ESRP_050": {
        "requirement_text": "The ESRP MUST use a TCP/TLS transport and MUST be provisioned with the credentials for the ECRF.",
        "document_section": "4.2.2.3",
        "description": "The ESRP must use TCP/TLS transport and be provisioned with the necessary credentials for the ECRF.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_051": {
        "requirement_text": "The ESRP MUST use a TCP/TLS transport and MUST be provisioned with the credentials for the ECRF.",
        "document_section": "4.2.2.3",
        "description": "The ESRP must use TCP/TLS transport and be provisioned with the necessary credentials for the ECRF.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_052": {
        "requirement_text": "Any URN in the “urn.service.sos” (and its urn:service:test.sos equivalents) or “urn:emergency.service.sos” tree MUST be supported by all ESRPs. Loops can result if the service urns specified in the policy are not appropriately chosen.",
        "document_section": "4.2.2.3",
        "description": "Any URN in the \"urn.service.sos\" (and its \"urn:service:test.sos\" equivalents) or \"urn:emergency.service.sos\" tree must be supported by all ESRPs. Loops may occur if the service URNs specified in the policy are not appropriately chosen.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_053": {
        "requirement_text": "The ESRP MUST use the ECRF interface with the “urn:emergency:service:additionaldata” service URN when accessing Additional Data associated with a location in the evaluation of a rule set that contains an Additional Data condition, as described in Section 4.2.2.5 Additional Data Interfaces.",
        "document_section": "4.2.2.3",
        "description": "The ESRP must use the ECRF interface with the “urn:emergency:service:additionaldata” service URN when accessing Additional Data related to a location as part of rule set evaluation that includes an Additional Data condition, as described in Section 4.2.2.5 Additional Data Interfaces.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_054": {
        "requirement_text": "The ESRP MUST implement both SIP Presence Event Package and HELD dereferencing interfaces.",
        "document_section": "4.2.2.4",
        "description": "The ESRP must implement both SIP Presence Event Package and HELD dereferencing interfaces.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_055": {
        "requirement_text": "The ESRP MUST use TCP/TLS for the LIS Dereferencing interface, with fallback to TCP (without TLS) on failure to establish a TLS connection.",
        "document_section": "4.2.2.4",
        "description": "The ESRP must use TCP/TLS for the LIS Dereferencing interface, with fallback to TCP (without TLS) if establishing a TLS connection fails.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_056": {
        "requirement_text": "The ESRP MUST implement mechanisms for retrieving Additional Data (RFC 7852).",
        "document_section": "4.2.2.5",
        "description": "The ESRP must implement mechanisms for retrieving Additional Data, as outlined in RFC 7852.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_057": {
        "requirement_text": "The ESRP MUST be able to accommodate multiple additional data services and structures for the same call.",
        "document_section": "4.2.2.5",
        "description": "The ESRP must be able to accommodate multiple Additional Data services and structures for the same call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_058": {
        "requirement_text": "The ESRP MUST implement the client side of the ElementState and ServiceState event notification packages.",
        "document_section": "4.2.2.6",
        "description": "The ESRP must implement the client side of the ElementState and ServiceState event notification packages.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_059": {
        "requirement_text": "The ESRP MUST maintain Subscriptions for these packages on every downstream element/service it serves.",
        "document_section": "4.2.2.6",
        "description": "The ESRP must maintain Subscriptions for these packages on every downstream element/service it serves.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_060": {
        "requirement_text": "The ESRP MUST implement the server-side of the ElementState event notification package and accept Subscriptions for all upstream ESRPs from which it expects to receive calls.",
        "document_section": "4.2.2.6",
        "description": "The ESRP must implement the server-side of the ElementState event notification package and accept Subscriptions for all upstream ESRPs from which it expects to receive calls.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_061": {
        "requirement_text": "The ESRP MUST promptly report changes in its state to its subscribed elements.",
        "document_section": "4.2.2.6",
        "description": "The ESRP must promptly report state changes to its subscribed elements.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_062": {
        "requirement_text": "Any change in state that affects its ability to receive calls MUST be reported.",
        "document_section": "4.2.2.6",
        "description": "Any state change affecting the ability to receive calls must be reported.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_063": {
        "requirement_text": "The set of ESRPs within an NGCS MUST implement the server-side of the ServiceState event notification package.",
        "document_section": "4.2.2.6",
        "description": "All ESRPs in an NGCS must implement the ServiceState event notification package server-side.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_064": {
        "requirement_text": "The ESRP MUST maintain reliable time synchronization.",
        "document_section": "4.2.2.7",
        "description": "The ESRP must maintain reliable time synchronization.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_065": {
        "requirement_text": "The ESRP MUST implement a logging interface per Section 4.12.",
        "document_section": "4.2.2.8",
        "description": "The ESRP must implement a logging interface as outlined in Section 4.12.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_066": {
        "requirement_text": "The ESRP MUST be capable of logging every transaction and every message received and sent on its call interfaces, every query to the ECRF, and every state change it receives or sends.",
        "document_section": "4.2.2.8",
        "description": "The ESRP must log all transactions, messages, queries, and state changes.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_067": {
        "requirement_text": "It MUST be capable of logging the rule set it consulted, the rules found to be relevant to the route, and the route decision it made. Specific LogEvent records for these are provided in Section 4.12.3.",
        "document_section": "4.2.2.8",
        "description": "It must log the rule set used, relevant rules, and route decisions.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_068": {
        "requirement_text": "The ESRP uses the AbandonedCallEvent to notify a PSAP that a call was started, but then cancelled prior to the PSAP responding to the INVITE. The AbandonedCall Notify is sent to the PSAP that would have received the call, had it been completed. If rule set evaluation was not complete when the call was abandoned, rule evaluation with best-effort values for conditions in the rules is completed in order to determine where to send the Notify.",
        "document_section": "4.2.2.9",
        "description": "The ESRP uses the AbandonedCallEvent to notify a PSAP if a call is abandoned before response.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_069": {
        "requirement_text": "When the ESRP receives a CANCEL for a call prior to any non-100 response received from a PSAP, such that the ESRP is unsure whether the downstream entity ever got an INVITE, a new NOTIFY is generated to the PSAP that would have received the call as determined by interpreting the ruleset, adhering to the filter requests. If there are multiple ESRPs in the path, the ESRPs before the terminating ESRP may not get the INVITE or the CANCEL, but will receive a NOTIFY from the upstream ESRP. They MUST send a NOTIFY downstream following the above process.",
        "document_section": "4.2.2.9",
        "description": "If the ESRP receives a CANCEL without a non-100 response, it must generate a NOTIFY to the PSAP based on the ruleset.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_070": {
        "requirement_text": "Forking between elements MUST NOT be used.",
        "document_section": "4.2.2.9",
        "description": "Forking between elements must not be used.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_071": {
        "requirement_text": "The ESRP MUST invoke the STI-VS before applying the RoutePolicy ruleset for the queue the emergency calls arrives on.",
        "document_section": "4.2.2.10",
        "description": "The ESRP must invoke the STI-VS before applying the RoutePolicy ruleset for incoming calls.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_072": {
        "requirement_text": "The ESRP MUST have access to the appropriate RoutePolicy ruleset for every URI that the ECRF can return in response to a service query made by the ESRP (Normal-NextHop).",
        "document_section": "4.2.3",
        "description": "The ESRP must have access to the appropriate RoutePolicy ruleset for each URI returned by the ECRF.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_073": {
        "requirement_text": "The ESRP MUST be provisioned with the policy store it uses.",
        "document_section": "4.2.3",
        "description": "The ESRP must be provisioned with its policy store.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_074": {
        "requirement_text": "Use of an external Policy Store MUST be possible even if an implementation includes a Policy Store.",
        "document_section": "4.2.3",
        "description": "An external Policy Store must be usable even if the ESRP has an internal policy store.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ESRP_075": {
        "requirement_text": "Downstream entities maintaining queues that upstream ESRPs queue calls on MUST supply a rule set for the upstream ESRP.",
        "document_section": "4.2.5",
        "description": "Downstream entities with queues must supply a rule set for the upstream ESRP.",
        "test_id": "",
        "subtests": []
    }
}