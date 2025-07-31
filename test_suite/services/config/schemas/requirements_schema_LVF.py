REQUIREMENTS_SCHEMA = {
    "RQ_LVF_003": {
        "requirement_text": "LVFs MUST support draft-ecrit-lost-planned-changes [178] allowing a LIS to be notified of planned changes in GIS data and for it to pre-validate a location against this new GIS data before it becomes live.",
        "document_section": "4.3",
        "description": "LVFs must support draft-ecrit-lost-planned-changes to notify a LIS of planned GIS data changes and allow pre-validation of locations before the changes go live.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LVF_004": {
        "requirement_text": "As specified in Section 3.4.2, the LVF MUST support the validation of location around planned changes as defined by draft-ecrit-lost-planned-changes [178].",
        "document_section": "4.3",
        "description": "LVFs must validate locations based on planned GIS changes, as defined by draft-ecrit-lost-planned-changes.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LVF_014": {
        "requirement_text": "All LoST server implementations, deployed as an LVF, MUST support the inclusion of location validation information in the “findServiceResponse” message.",
        "document_section": "4.3.2.2",
        "description": "All LoST servers deployed as LVFs must include location validation information in the \"findServiceResponse\" message.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LVF_015": {
        "requirement_text": "As specified in Section 3.4.2, the LVF MUST support the validation of location around planned changes as defined by draft-ecrit-lost-planned-changes [178].",
        "document_section": "4.3.2.2",
        "description": "LVFs must validate locations based on planned GIS changes, as outlined in draft-ecrit-lost-planned-changes.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LVF_038": {
        "requirement_text": "Given that NG9-1-1 elements will also need to validate civic locations that either come with an emergency call, or are conveyed over the voice path, it is also a requirement that LVF elements MUST be reachable from within any ESInet. Since it is not possible that all entities that need to access an LVF will have one in their local domain, an LVF MUST be accessible from the Internet",
        "document_section": "4.3.8",
        "description": "LVF elements must be reachable from any ESInet and accessible from the Internet to validate civic locations associated with emergency calls.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LVF_041": {
        "requirement_text": "The LVF is a logical function that MAY share the physical platform of an ECRF, and MUST share the same data for a given jurisdiction as the ECRF.",
        "document_section": "4.3.8",
        "description": "The LVF may share the physical platform with the ECRF but must use the same jurisdiction data as the ECRF.",
        "test_id": "",
        "subtests": []
    },
    "RQ_LVF_055": {
        "requirement_text": "An LVF SHOULD NOT return a degradedMatch warning if there is no potential for improvement (e.g., a road centerline match in a region where address points are not able to be provisioned).",
        "document_section": "3.4.10.2",
        "description": "LVFs should not return a degradedMatch warning if there is no potential for improvement, such as when road centerline matches cannot be enhanced with address points.",
        "test_id": "",
        "subtests": []
    }
}