REQUIREMENTS_SCHEMA = {
    "RQ_LIS_001": {
        "requirement_text": "If the LIS supplies location by reference, it MUST also provide dereferencing service for that location URI.",
        "document_section": "4.1",
        "description": "If the LIS provides location by reference, it must also provide a dereferencing service for that location URI.",
        "test_id": "LIS_001",
        "subtests": []
    },
    "RQ_LIS_002": {
        "requirement_text": "If the LIS supplies location by reference, it MUST support HELD (RFC 5985) [7], HELD Dereferencing (RFC 6753) [55], and/or SIP Presence Event Package (RFC 3856) [25].",
        "document_section": "4.1",
        "description": "If the LIS provides location by reference, it must support HELD (RFC 5985), HELD Dereferencing (RFC 6753), and/or SIP Presence Event Package (RFC 3856).",
        "test_id": "LIS_001",
        "subtests": []
    },
    "RQ_LIS_003": {
        "requirement_text": "LISs supporting SIP MUST support location filters (RFC 6447) [72] and event rate control (RFC 6446) [80].",
        "document_section": "4.1",
        "description": "LISs supporting SIP must support location filters (RFC 6447) and event rate control (RFC 6446).",
        "test_id": "LIS_003\n LIS_004",
        "subtests": []
    },
    "RQ_LIS_004": {
        "requirement_text": "A LIS MUST validate locations prior to entering them into the LIS using the LVF (see Section 4.3).",
        "document_section": "4.1",
        "description": "A LIS must validate locations before entering them using the LVF (Section 4.3).",
        "test_id": "",
        "subtests": []
    },
    "RQ_LIS_005": {
        "requirement_text": "A LIS MUST accept credentials traceable to the PCA for authenticating queries for a location dereference. Since calls may be diverted to any available PSAP, the LIS cannot rely on any other credential source to authorize location dereferencing.",
        "document_section": "4.1",
        "description": "A LIS must accept credentials traceable to the PCA for authenticating location dereference queries.",
        "test_id": "LIS_005",
        "subtests": []
    },
    "RQ_LIS_006": {
        "requirement_text": "..any LIS that provides a dereferencing service for a location URI MUST provide an expiration time associated with that URI set at a minimum of 30 minutes, with a maximum of 24 hours.",
        "document_section": "4.1",
        "description": "Any LIS providing location dereferencing must provide an expiration time for the location URI, at least 30 minutes and no more than 24 hours.",
        "test_id": "LIS_002",
        "subtests": []
    },
    "RQ_LIS_007": {
        "requirement_text": "The NG9-1-1 system supports location included by value in the body of a SIP message, with a pointer to it (i.e., a cid URL) in the Geolocation header field (RFC 6442) [8] of the SIP message. It also supports location by reference, when a location URI is populated in the Geolocation header field. All NGCS that receive location as a PIDF-LO must be prepared to receive location by reference and to use location by reference the NGCS MUST implement SIP and HTTP Enabled Location Delivery (HELD) (RFC 5985) [7] de-referencing protocols. A Location Information Server (LIS)14 MUST implement one or both of these protocols.",
        "document_section": "3.2",
        "description": "NG9-1-1 supports both location by value and reference, with a pointer to the location URI in the Geolocation header; LIS must support HELD dereferencing protocols.",
        "test_id": "LIS_001",
        "subtests": []
    },
    "RQ_LIS_008": {
        "requirement_text": "In order for a LIS to be NG9-1-1 compliant, it MUST accept credentials traceable to the PSAP Credentialing Agency (PCA) when establishing the TLS connection as sufficient to deliver “dispatch” quality location.",
        "document_section": "3.2",
        "description": "To be NG9-1-1 compliant, a LIS must accept credentials traceable to the PSAP Credentialing Agency (PCA) for TLS connection establishment.",
        "test_id": "LIS_005",
        "subtests": []
    }
}