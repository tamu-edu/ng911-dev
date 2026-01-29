REQUIREMENTS_SCHEMA = {
    "RQ_ECRF_001": {
        "requirement_text": "The NENA NG9-1-1 solution MUST properly route incoming IP packet-based emergency calls to the appropriate or designated PSAP, as well as support the dispatch of responders to the right location",
        "document_section": "4.3",
        "description": "The NENA NG9-1-1 solution must route incoming emergency calls to the correct PSAP and support responder dispatch to the right location.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_002": {
        "requirement_text": "The location information used, when provided in civic form, MUST be proved sufficient for routing and dispatch prior to the call being placed.",
        "document_section": "4.3",
        "description": "Civic location information provided before the call must be sufficient for proper routing and dispatch.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_008": {
        "requirement_text": "Authentication MUST apply to all entities that initiate queries to the ECRF within the ESInet.",
        "document_section": "4.3.2.1",
        "description": "Authentication is required for all entities that query the ECRF within the ESInet.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_009": {
        "requirement_text": "TLS is used by all ECRFs and LVFs within the ESInet, and credentials issued to the querying entity that are traceable to the PCA MUST be accepted.",
        "document_section": "4.3.2.1",
        "description": "All ECRFs and LVFs within the ESInet must use TLS and accept credentials traceable to the PCA.",
        "test_id": "ECRF_LVF_001",
        "subtests": []
    },
    "RQ_ECRF_010": {
        "requirement_text": "Devices and carriers outside the ESInet may not have credentials, TLS is not required, and the ECRF/LVF should assume a common public identity for such queries.",
        "document_section": "4.3.2.1",
        "description": "Devices and carriers outside the ESInet do not require credentials or TLS, assuming a common public identity for queries.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_011": {
        "requirement_text": "If the proffered location is not specified as a point (i.e., the location in the query is a shape) and the shape intersects more than one service boundary with a given service URN, the ECRF response SHALL be the URI of the service boundary with the greatest area of overlap (with a tie-breaking policy for the case of equal area of overlap).",
        "document_section": "4.3.2.1",
        "description": "If a location is a shape and intersects multiple service boundaries, the ECRF response should return the URI of the service boundary with the greatest area overlap.",
        "test_id": "ECRF_LVF_003",
        "subtests": []
    },
    "RQ_ECRF_012": {
        "requirement_text": "If more than one service boundary for the same service URN at a given location exists in the ECRF, multiple <mapping> elements will be returned. The querier (e.g., a PSAP), MUST have local policy to determine how to handle the call.",
        "document_section": "4.3.2.1",
        "description": "When multiple service boundaries exist for a service URN, the ECRF will return multiple mapping elements, with the querier determining how to handle the call.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_013": {
        "requirement_text": "In some cases, the ECRF can use the identity of the querier, or a distinguished Service URN to return the URI of the correct agency. This condition only occurs for queries to an ECRF from within an ESInet. External queries will only return one (PSAP) URI.",
        "document_section": "4.3.2.1",
        "description": "For queries within the ESInet, the ECRF can use the querier's identity to return the correct agency URI, while external queries return only one PSAP URI.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_022": {
        "requirement_text": "The ECRF MUST be able to provide routing information based on location information represented by a civic address. To do so, it is expected that the ECRF will represent the geographic service boundary in a manner that allows the association of a given address with the service boundary within which it is located.",
        "document_section": "4.3.3.1",
        "description": "The ECRF must provide routing information based on civic address and geographic service boundaries.",
        "test_id": "ECRF_LVF_002",
        "subtests": []
    },
    "RQ_ECRF_023": {
        "requirement_text": "..if the provisioning data changes, the ECRF MUST respond immediately to the change, which may invalidate (for at least some time) the precalculated tabular data.",
        "document_section": "4.3.3.1",
        "description": "The ECRF must immediately respond to any changes in provisioning data, which may invalidate previously calculated data.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_024": {
        "requirement_text": "ECRFs MUST accept location information conforming to U.S. addressing standards defined/ in CLDXF [77] and its eventual Canadian equivalents.",
        "document_section": "4.3.3.1",
        "description": "ECRFs must accept location information in U.S. addressing standards defined in CLDXF and its Canadian equivalents.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_027": {
        "requirement_text": "When dereferenced by a client using PCA-traceable credentials, URIs returned for the Additional Data service MUST resolve to Additional Data blocks registered in the IANA Emergency Call Additional Data registry [179].",
        "document_section": "4.3.3.4",
        "description": "When dereferenced with PCA-traceable credentials, URIs returned for Additional Data services must resolve to blocks registered in the IANA Emergency Call Additional Data registry.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_035": {
        "requirement_text": "Any ECRF that is authoritative for a top level URN MUST also be authoritative for all lower level URNs for the same coverage regions.",
        "document_section": "4.3.6",
        "description": "An ECRF authoritative for a top-level URN must also be authoritative for all lower-level URNs within the same coverage region.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_036": {
        "requirement_text": "Since it is not possible that all entities that need to access an ECRF will have one in their local domain, an ECRF for each 9-1-1 Authority MUST be accessible from the Internet",
        "document_section": "4.3.8",
        "description": "Each 9-1-1 Authority must have an ECRF accessible from the Internet due to the lack of local access for all entities.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_037": {
        "requirement_text": "Provisioning of data within appropriate ECRF/LVF systems for use in overload and backup routing scenarios MUST also be supported.",
        "document_section": "4.3.8",
        "description": "ECRF/LVF systems must support data provisioning for overload and backup routing scenarios.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_039": {
        "requirement_text": "Similar considerations apply for an ECRF, but the entities that route are often different from the entities that validate, so differences in deployments may occur. All devices and services that route MUST have access to an ECRF. External ECRFs MUST be accessible to all devices and services, including those on the Internet.",
        "document_section": "4.3.8",
        "description": "All routing entities must have access to an ECRF, with external ECRFs accessible to devices and services, including those on the Internet.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_040": {
        "requirement_text": "Within the ESInet, ECRFs MUST be accessible from all ESRPs and all agencies that may receive or transfer calls or EIDOs related to calls.",
        "document_section": "4.3.8",
        "description": "ECRFs must be accessible from all ESRPs and agencies involved in receiving or transferring emergency calls or EIDOs within the ESInet.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_045": {
        "requirement_text": "There SHALL NOT be any single point of failure for any critical service or function hosted on the ESInet. Certain services designated as non-critical may be exempt from this requirement. These MUST NOT include the BCF, internal ECRF, ESRP, Logging Service, and security services.",
        "document_section": "2.7",
        "description": "There must be no single point of failure for critical services in the ESInet, including the BCF, internal ECRF, ESRP, Logging Service, and security services.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_046": {
        "requirement_text": "The LoST interface allows a geo-location to be expressed as a point or one of a number of defined “shapes” such as circle, ellipse, arc-band, or polygon. ECRFs MUST be able to handle all of these shapes.",
        "document_section": "3.4.3",
        "description": "The LoST interface allows geo-locations to be expressed as various shapes, and ECRFs must handle all these shapes.",
        "test_id": "ECRF_LVF_002",
        "subtests": []
    },
    "RQ_ECRF_048": {
        "requirement_text": "ECRF implementations MUST support “urn:emergency:service”.",
        "document_section": "3.4.3",
        "description": "ECRF implementations must support the “urn:emergency:service” service.",
        "test_id": "",
        "subtests": []
    },
    "RQ_ECRF_051": {
        "requirement_text": "An ECRF outside the ESInet is REQUIRED to support the “urn:service:sos” service. Service substitution, as described in RFC 5222 [48], SHALL be used to substitute “urn:service:sos” for all subservices such as “urn:service:sos.police”, which would cause the call to be routed the same as a call to “urn:service:sos”.",
        "document_section": "3.4.4",
        "description": "An ECRF outside the ESInet must support the \"urn:service:sos\" service and use service substitution to route calls correctly.",
        "test_id": "ECRF_LVF_004",
        "subtests": []
    },
    "RQ_ECRF_052": {
        "requirement_text": "ECRFs inside the ESInet MUST support both “urn:service:sos” and “urn:emergency:service:sos”.",
        "document_section": "3.4.4",
        "description": "ECRFs inside the ESInet must support both \"urn:service:sos\" and \"urn:emergency:service:sos\".",
        "test_id": "ECRF_LVF_004",
        "subtests": []
    },
    "RQ_ECRF_053": {
        "requirement_text": "The <serviceNumber> element in the <mapping> response contains the emergency services number appropriate for the location provided in the query. This allows a foreign end device to recognize a dialed emergency number. The service number returned by an ECRF or LVF for an emergency call MUST be “911”.",
        "document_section": "3.4.4",
        "description": "The serviceNumber element in the <mapping> response should return the emergency number \"911\" for all emergency calls.",
        "test_id": "ECRF_LVF_002",
        "subtests": []
    }
}