REQUIREMENTS_SCHEMA = {
    "RQ_ECRF-LVF_005": {
        "requirement_text": "An ECRF or LVF provided by a 9-1-1 Authority and accessible from outside the ESInet MUST permit querying by an IP client/endpoint, an IP routing proxy, a Legacy Network Gateway, and any other entity outside the ESInet.",
        "document_section": "4.3",
        "description": "An ECRF or LVF provided by a 9-1-1 Authority and accessible outside the ESInet must allow querying by IP clients, proxies, and Legacy Network Gateways.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_006": {
        "requirement_text": "An ECRF or LVF accessible inside an ESInet MUST permit querying from any entity inside the ESInet.",
        "document_section": "4.3",
        "description": "An ECRF or LVF inside the ESInet must permit queries from any entity within the ESInet.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_007": {
        "requirement_text": "The ECRF MUST be used within the ESInet to route calls to the correct PSAP, and by the PSAP to route calls to the correct responders.",
        "document_section": "4.3",
        "description": "The ECRF must route calls to the correct PSAP and help PSAPs route calls to the appropriate responders within the ESInet.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_016": {
        "requirement_text": "The ECRF/LVF MUST implement an NTP client interface for time of day information.",
        "document_section": "4.3.2.4",
        "description": "The ECRF/LVF must include an NTP client interface to provide time of day information.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_017": {
        "requirement_text": "The ECRF/LVF MUST be capable of generating LogEvents per Section 4.12.",
        "document_section": "4.3.2.5",
        "description": "The ECRF/LVF must be capable of generating LogEvents as specified in Section 4.12.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_018": {
        "requirement_text": "The ECRF/LVF MUST be capable of logging every incoming routing/validation request along with every recursive request and all response messages.",
        "document_section": "4.3.2.5",
        "description": "The ECRF/LVF must log every routing/validation request, including recursive requests and responses.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_019": {
        "requirement_text": "In addition, the ECRF/LVF MUST log all provisioning and synchronization messages and actions. Specific LogEvent records for these are provided in Section 4.12.3.",
        "document_section": "4.3.2.5",
        "description": "The ECRF/LVF must log all provisioning and synchronization messages and actions as specified in Section 4.12.3.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_020": {
        "requirement_text": "Each ECRF and each LVF MUST implement the server-side of the ElementState event notification package. The ECRF/LVF MUST promptly report changes in its state to its subscribed elements. Any change in state that affects its ability to route (ECRF) or validate (LVF) MUST be reported.",
        "document_section": "4.3.2.6",
        "description": "Each ECRF and LVF must implement the server-side of ElementState notifications, promptly reporting state changes affecting routing or validation.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_021": {
        "requirement_text": "The set of ECRF and LVF FEs within an ESInet MUST implement the server side of the ServiceState event notification package for the ECRF and the LVF service.",
        "document_section": "4.3.2.7",
        "description": "ECRF and LVF FEs within the ESInet must implement the server side of the ServiceState event notification package for both services.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_025": {
        "requirement_text": "Unless the ECRF/LVF is provisioned to return different responses to different credentials of the querier, all queries with the same URN and location SHALL return the same response.",
        "document_section": "4.3.3.2",
        "description": "Unless provisioned differently, all queries with the same URN and location must return the same response from the ECRF/LVF.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_026": {
        "requirement_text": "The ECRF response SHALL be the service boundary with the greatest area of overlap. The ECRF will return multiple <mapping> elements in a response if the query has multiple matches (e.g., a query within an ESInet for “emergency:service:responder:police” with a location within the jurisdiction of campus, city, county, and state police agencies)",
        "document_section": "4.3.3.3",
        "description": "The ECRF response must return the service boundary with the greatest area overlap if there are multiple matches, such as overlapping jurisdictions.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_028": {
        "requirement_text": "When provisioning data for an ECRF and LVF through the SI, a 9-1-1 Authority (or 9-1-1 Authority designee) MUST only include GIS data for their geographic area of responsibility and MUST ensure the data includes coverage for the entire extent of that area.",
        "document_section": "4.3.4",
        "description": "The 9-1-1 Authority must only include GIS data within its geographic responsibility area when provisioning data for an ECRF/LVF.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_029": {
        "requirement_text": "The ECRF/LVF MUST have a provisionable threshold parameter that indicates the maximum gap/overlap that is ignored by it. This threshold is expressed in square meters. Gaps or overlaps that are smaller than this parameter MUST be handled by the ECRF/LVF using an algorithm of its choice. For example, it may split the gap/overlap roughly in half and consider the halves as belonging to one of the constituent sources.",
        "document_section": "4.3.4",
        "description": "The ECRF/LVF must have a threshold parameter for ignoring gaps/overlaps, and handle smaller gaps/overlaps using an algorithm of its choice.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_030": {
        "requirement_text": "The ECRF/LVF MUST report gaps and overlaps larger than the provisioned threshold. To do so, it makes use of the GapOverlap event.",
        "document_section": "4.3.4",
        "description": "The ECRF/LVF must report gaps and overlaps larger than the provisioned threshold using the GapOverlap event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_031": {
        "requirement_text": "All 9-1-1 Authorities which provide source GIS data to an ECRF/LVF MUST subscribe to its GapOverlap event.",
        "document_section": "4.3.4",
        "description": "All 9-1-1 Authorities providing GIS data to an ECRF/LVF must subscribe to the GapOverlap event.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_032": {
        "requirement_text": "The response of the agencies MUST be to provide updates to the data that address the gap/overlap.",
        "document_section": "4.3.4",
        "description": "Agencies must update their data to address identified gaps or overlaps.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_033": {
        "requirement_text": "During the period when the gap/overlap exists, notifications have been issued, and queries arrive (which could be at call time) with a location in the gap/overlap, the ECRF/LVF MUST resolve the query using an algorithm of its choice. For example, it may split the gap/overlap roughly in half and consider the halves as belonging to one of the constituent sources.",
        "document_section": "4.3.4",
        "description": "When a gap/overlap exists and a query arrives, the ECRF/LVF must resolve the query using an algorithm, such as splitting the gap/overlap.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_034": {
        "requirement_text": "A service may have areas within the service area of the ECRF for which there is no responder. For example, the mountain rescue service is not available in flat terrain. Also, there are still some areas where 9-1-1 service is not available. In such cases, a service boundary MUST exist in the ECRF with the Service URI field set to urn:emergency:servicenotimplemented. The ECRF MUST return the <serviceNotImplemented> error if asked to provide a route for a location within that areas.",
        "document_section": "4.3.4",
        "description": "A service area may lack a responder in some regions, requiring a service boundary with the \"urn:emergency:servicenotimplemented\" URI and the return of a <serviceNotImplemented> error.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_042": {
        "requirement_text": "An ECRF/LVF, wherever deployed, whether within an Origination or Access network, MUST be able to reach out to other ECRF/LVFs in case of missing data, or in the case in which the requested location is outside its local jurisdiction. If the ECRF/LVF doesn’t know the answer, based on configuration, it will either recurse (refer) a request for validation to one or more other ECRF/LVFs, or it will iterate the request to some other ECRF/LVF, providing the other ECRF/LVF’s URL in the original ECRF/LVF response.",
        "document_section": "4.3.8",
        "description": "The ECRF/LVF must query other ECRF/LVFs if needed for missing data or locations outside its jurisdiction.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_043": {
        "requirement_text": "Localized ECRF/LVF elements MAY have limited data, sufficient to provide routing/location validation within its defined boundaries, but MUST rely on other ECRF/LVFs for routing/validation of a location outside its local area.",
        "document_section": "4.3.8",
        "description": "Localized ECRF/LVFs may have limited data, relying on other ECRF/LVFs for locations outside their boundaries.",
        "test_id": "ECRF_LVF_005",
        "subtests": []
    },
    "RQ_ECRF-LVF_044": {
        "requirement_text": "However, it should be noted that the ECRF is a real-time element in the path of an emergency call. The LVF is used primarily while provisioning a LIS. If the ECRF and LVF are combined, the implementation MUST assure ECRF queries are processed promptly, and LVF traffic does not interfere with proper operation of the ECRF function.",
        "document_section": "4.3.9",
        "description": "The ECRF must process emergency call queries promptly, and the LVF should not interfere with the ECRF's operation.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_047": {
        "requirement_text": "The “service” element identifies the service requested by the client. Valid service names MUST be “urn:service:sos” or one of its sub-services for ECRF and LVF queries used by originating networks or devices for emergency calls.",
        "document_section": "3.4.3",
        "description": "The \"service\" element in ECRF/LVF queries must specify \"urn:service:sos\" or a sub-service for emergency calls.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_049": {
        "requirement_text": "Entities inside the ESInet MUST specify recursion by setting the recursive attribute in the <findService> request to ‘true’ and all ECRFs and LVFs MUST implement and perform recursion when requested to help mitigate the effect of an attack on the Internal Forest Guide (see Section 4.13.6).",
        "document_section": "3.4.3",
        "description": "Entities inside the ESInet must specify recursion by setting the recursive attribute to \"true,\" and ECRFs/LVFs must implement recursion when requested.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF-LVF_050": {
        "requirement_text": "All ECRF and LVF implementations MUST support both recursive and iterative modes.",
        "document_section": "3.4.4",
        "description": "All ECRF and LVF implementations must support both recursive and iterative modes for handling queries.",
        "test_id": "ECRF_LVF_005",
        "subtests": []
    },
    "RQ_ECRF-LVF_054": {
        "requirement_text": "All ECRFs and LVFs MUST implement listServices and listServicesByLocation. The response to this request may depend on the (TLS) credentials of the querier.",
        "document_section": "3.4.7",
        "description": "All ECRFs and LVFs must implement listServices and listServicesByLocation, with the response potentially depending on the querier’s credentials.",
        "test_id": "ECRF_LVF_004",
        "subtests": []
    }
}