REQUIREMENTS_SCHEMA = {
    "RQ_PS_001": {
        "requirement_text": "If the policy is needed for use after expiration, it MUST be retrieved again from the Policy Store",
        "document_section": "3.3",
        "description": "If a policy is needed after its expiration, it must be retrieved again from the Policy Store.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_002": {
        "requirement_text": "If the policy is needed for use after expiration, it MUST be retrieved again from the Policy Store",
        "document_section": "3.3",
        "description": "If a policy is needed after its expiration, it must be retrieved again from the Policy Store.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_003": {
        "requirement_text": "A policy retrieval request MAY return a referral to another Policy Store instead of the requested policy. The referred-to Policy Store might have the policy or might return another referral.",
        "document_section": "3.3",
        "description": "A policy retrieval request may refer to another Policy Store, which might return the policy or another referral.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_004": {
        "requirement_text": "Policies stored in the Policy Store MUST be signed by the owner of the Policy.",
        "document_section": "3.3",
        "description": "Policies stored in the Policy Store must be signed by the policy's owner.",
        "test_id": "PS_001",
        "subtests": []
    },
    "RQ_PS_005": {
        "requirement_text": "Policies stored in the Policy Store MUST be signed by the owner of the Policy.",
        "document_section": "3.3",
        "description": "Policies stored in the Policy Store must be signed by the policy's owner.",
        "test_id": "PS_001",
        "subtests": []
    },
    "RQ_PS_006": {
        "requirement_text": "A policy document MUST be a JSON Web Signature (JWS) object per Section 5.10",
        "document_section": "3.3",
        "description": "A policy document must be a JSON Web Signature (JWS) object, as described in Section 5.10.",
        "test_id": "PS_001",
        "subtests": []
    },
    "RQ_PS_007": {
        "requirement_text": "A policy document MUST be a JSON Web Signature (JWS) object per Section 5.10",
        "document_section": "3.3",
        "description": "A policy document must be a JSON Web Signature (JWS) object, as described in Section 5.10.",
        "test_id": "PS_001",
        "subtests": []
    },
    "RQ_PS_008": {
        "requirement_text": "For agencies within an ESInet, a credential traceable to the PCA MUST be used.",
        "document_section": "3.3",
        "description": "Agencies within an ESInet must use a credential traceable to the PCA.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_009": {
        "requirement_text": "For agencies within an ESInet, a credential traceable to the PCA MUST be used.",
        "document_section": "3.3",
        "description": "Agencies within an ESInet must use a credential traceable to the PCA.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_010": {
        "requirement_text": "(Policy Object contents table)",
        "document_section": "3.3.1",
        "description": "The Policy Object contents table outlines the policy's structure.",
        "test_id": "PS_002",
        "subtests": []
    },
    "RQ_PS_011": {
        "requirement_text": "(Policy Object contents table)",
        "document_section": "3.3.1 and\n 3.3.1.2.1",
        "description": "The Policy Object contents table outlines the policy's structure.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_012": {
        "requirement_text": "(Policy Object contents table)",
        "document_section": "3.3.1",
        "description": "The Policy Object contents table outlines the policy's structure.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_013": {
        "requirement_text": "(Versions entry point result parameters)",
        "document_section": "3.3.1.1",
        "description": "The Versions entry point parameters specify the results for the Policy Store.",
        "test_id": "PS_003",
        "subtests": []
    },
    "RQ_PS_014": {
        "requirement_text": "The Versions entry point of the Policy Store Web Service MUST include, in the “serviceInfo” parameter, the parameter “requiredAlgorithms” whose value is an array of JWS algorithms (as described in 5.10) acceptable to the policy store.",
        "document_section": "3.3.1.1",
        "description": "The Versions entry point of the Policy Store must include acceptable JWS algorithms in the \"serviceInfo\" parameter.",
        "test_id": "PS_003",
        "subtests": ["Verify if all 'versions' contain 'serviceInfo' with 'requiredAlgorithms' array of string values"]
    },
    "RQ_PS_015": {
        "requirement_text": "Clients of Web Services MUST make an HTTPS GET request using the URI of the service’s Versions entry point.",
        "document_section": "2.8.3",
        "description": "Clients of Web Services must make an HTTPS GET request using the URI of the service’s Versions entry point.",
        "test_id": "PS_009",
        "subtests": []
    },
    "RQ_PS_016": {
        "requirement_text": "(PolicyArray contents table)",
        "document_section": "3.3.1.2.1",
        "description": "The PolicyArray contents table outlines the structure of policies stored.",
        "test_id": "PS_004",
        "subtests": ["Validate response message for: {variation_name}"]
    },
    "RQ_PS_017": {
        "requirement_text": "(Retrieve Policies parameters)",
        "document_section": "3.3.1.2.1",
        "description": "The Retrieve Policies parameters specify how policies should be retrieved.",
        "test_id": "PS_004",
        "subtests": ["Validate 4xx error response for: {variation_name}"]
    },
    "RQ_PS_018": {
        "requirement_text": "(Retrieve Policies parameters)",
        "document_section": "3.3.1.2.1",
        "description": "The Retrieve Policies parameters specify how policies should be retrieved.",
        "test_id": "PS_004",
        "subtests": []
    },
    "RQ_PS_019": {
        "requirement_text": "(Update Policy parameters)",
        "document_section": "3.3.1.2.3",
        "description": "The Update Policy parameters define how policies are updated.",
        "test_id": "PS_005",
        "subtests": []
    },
    "RQ_PS_021": {
        "requirement_text": "(Delete Policy parameters)",
        "document_section": "3.3.1.2.4",
        "description": "The Delete Policy parameters define how policies are deleted.",
        "test_id": "PS_006",
        "subtests": []
    },
    "RQ_PS_023": {
        "requirement_text": "(Enumerate Policies parameters)",
        "document_section": "3.3.1.3.1",
        "description": "The Enumerate Policies parameters define how policies are listed.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_024": {
        "requirement_text": "(Enumerate Policies parameters)",
        "document_section": "3.3.1.3.1",
        "description": "The Enumerate Policies parameters define how policies are listed.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_025": {
        "requirement_text": "Following a POST, the Policy Store MUST confirm that the policyExpirationTime is in the future and the structure and contents of the document is well-formed and conformant; for Policy Routing Rules, MUST confirm that each rule has a unique id and verify the signature of the JWS.",
        "document_section": "3.3.1.2.2",
        "description": "After a POST request, the Policy Store must confirm the policy's expiration time is in the future and verify the document's structure and signature.",
        "test_id": "PS_002",
        "subtests": []
    },
    "RQ_PS_026": {
        "requirement_text": "Following a POST, the Policy Store MUST confirm that the policyExpirationTime is in the future and the structure and contents of the document is well-formed and conformant; for Policy Routing Rules, MUST confirm that each rule has a unique id and verify the signature of the JWS.",
        "document_section": "3.3.1.2.2",
        "description": "After a POST request, the Policy Store must confirm the policy's expiration time is in the future and verify the document's structure and signature.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_027": {
        "requirement_text": "Following a POST, the Policy Store MUST confirm that the policyExpirationTime is in the future and the structure and contents of the document is well-formed and conformant; for Policy Routing Rules, MUST confirm that each rule has a unique id and verify the signature of the JWS.",
        "document_section": "3.3.1.2.2",
        "description": "After a POST request, the Policy Store must confirm the policy's expiration time is in the future and verify the document's structure and signature.",
        "test_id": "PS_007",
        "subtests": []
    },
    "RQ_PS_028": {
        "requirement_text": "Following a POST, the Policy Store MUST confirm that the policyExpirationTime is in the future and the structure and contents of the document is well-formed and conformant; for Policy Routing Rules, MUST confirm that each rule has a unique id and verify the signature of the JWS.",
        "document_section": "3.3.1.2.2",
        "description": "After a POST request, the Policy Store must confirm the policy's expiration time is in the future and verify the document's structure and signature.",
        "test_id": "PS_001",
        "subtests": []
    },
    "RQ_PS_029": {
        "requirement_text": "When processing an Update request, the Policy Store MUST confirm that the policyExpirationTime is in the future and the structure and contents of the document is well-formed and conformant; for Policy Routing Rules, MUST confirm that each file has a unique ID and verify the signature of the JWS.",
        "document_section": "3.3.1.2.3",
        "description": "When processing an Update request, the Policy Store must confirm the policy's expiration time is in the future, verify the document's structure, and check for unique policy rule IDs.",
        "test_id": "PS_005",
        "subtests": ["Validate 4xx error response for invalid request"]
    },
    "RQ_PS_030": {
        "requirement_text": "When processing an Update request, the Policy Store MUST confirm that the policyExpirationTime is in the future and the structure and contents of the document is well-formed and conformant; for Policy Routing Rules, MUST confirm that each file has a unique ID and verify the signature of the JWS.",
        "document_section": "3.3.1.2.3",
        "description": "The Policy Store must ensure that the policy expiration time is valid, the document structure is correct, and the JWS signature is verified when processing an Update request.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_031": {
        "requirement_text": "When processing an Update request, the Policy Store MUST confirm that the policyExpirationTime is in the future and the structure and contents of the document is well-formed and conformant; for Policy Routing Rules, MUST confirm that each file [rule] has a unique ID and verify the signature of the JWS.",
        "document_section": "3.3.1.2.3",
        "description": "The Policy Store must confirm the policy's expiration time, validate the document structure, and verify the signature of the JWS during an Update request.",
        "test_id": "PS_007",
        "subtests": []
    },
    "RQ_PS_032": {
        "requirement_text": "When processing an Update request, the Policy Store MUST confirm that the policyExpirationTime is in the future and the structure and contents of the document is well-formed and conformant; for Policy Routing Rules, MUST confirm that each file [rule] has a unique ID and verify the signature of the JWS.",
        "document_section": "3.3.1.2.3",
        "description": "The Policy Store must validate the expiration time, structure, contents, and signature of the JWS for Update requests.",
        "test_id": "PS_005",
        "subtests": ["Validate 4xx error response for invalid request"]
    },
    "RQ_PS_033": {
        "requirement_text": "(PolicyEnumArray members)",
        "document_section": "3.3.1.2.6",
        "description": "The PolicyEnumArray defines the elements of the policy enumeration.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_034": {
        "requirement_text": "A Route Policy document MUST be a JWS [171] as per Section 5.10 and MUST have a payload conforming to Appendix E.10.",
        "document_section": "3.3.3",
        "description": "A Route Policy document must be a JWS and comply with Appendix E.10.",
        "test_id": "PS_007",
        "subtests": []
    },
    "RQ_PS_036": {
        "requirement_text": "A Route Policy document MUST be a JWS [171] as per Section 5.10 and MUST have a payload conforming to Appendix E.10.\n \n A condition object contains the following members:\n \n • 'conditionType': a string which MUST exist and be set to the specific condition type.\n • 'negation': an OPTIONAL Boolean that when set to ‘true’ inverts the condition sense. When “negation” exists and is set to ‘true’, it reverses the evaluation of the “Conditions” object; when set to ‘false’ or omitted it has no effect.\n • 'description': an OPTIONAL string containing a description of the condition.",
        "document_section": "3.3.3",
        "description": "A Route Policy document must be a JWS with conditions including a type, optional negation, and a description.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_037": {
        "requirement_text": "A Route Policy document MUST be a JWS [171] as per Section 5.10 and MUST have a payload conforming to Appendix E.10.\n \n A condition object contains the following members:\n \n • 'conditionType': a string which MUST exist and be set to the specific condition type.\n • 'negation': an OPTIONAL Boolean that when set to ‘true’ inverts the condition sense. When “negation” exists and is set to ‘true’, it reverses the evaluation of the “Conditions” object; when set to ‘false’ or omitted it has no effect.\n • 'description': an OPTIONAL string containing a description of the condition.",
        "document_section": "3.3.3",
        "description": "A Route Policy document must be a JWS with conditions including condition type, optional negation, and an optional description.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_038": {
        "requirement_text": "A routing element MUST verify the JWS signature before executing the rules.\n \n If the JWS signature verification fails, the policy MUST NOT be executed.",
        "document_section": "3.3.3",
        "description": "Routing elements must verify the JWS signature before executing rules; if verification fails, the policy is not executed.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_039": {
        "requirement_text": "The Policy Store is REQUIRED to store and retrieve Route Policy documents byte-for-byte unaltered",
        "document_section": "3.3.3",
        "description": "The Policy Store must store and retrieve Route Policy documents without alteration.",
        "test_id": "PS_008",
        "subtests": []
    },
    "RQ_PS_040": {
        "requirement_text": "If a rule set has no conditions that evaluate to ‘true’, the ESRP MUST treat this as a fatal error (see Section 4.2.1.6).",
        "document_section": "3.3.3.1",
        "description": "If a rule set has no conditions evaluating to ‘true,’ it must be treated as a fatal error by the ESRP.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_041": {
        "requirement_text": "(Time Period Condition members)",
        "document_section": "3.3.3.1.1",
        "description": "The Time Period Condition specifies valid time range members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_042": {
        "requirement_text": "(Time Period Condition members)",
        "document_section": "3.3.3.1.1",
        "description": "The Time Period Condition specifies valid time range members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_043": {
        "requirement_text": "An ESRP or other entity executing a policy MUST ignore an invalid value in a member (e.g., a timeStart or timeEnd with an hour greater than 24, or minutes or seconds greater than 60, or hour set to 24 with minutes or seconds greater than 0)",
        "document_section": "3.3.3.1.1",
        "description": "The ESRP must ignore invalid condition values, such as incorrect time or date formats.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_044": {
        "requirement_text": "An ESRP or other entity executing a policy MUST ignore an invalid value in a member (e.g., a timeStart or timeEnd with an hour greater than 24, or minutes or seconds greater than 60, or hour set to 24 with minutes or seconds greater than 0) but SHOULD generate a Discrepancy Report against the policy owner (Section 3.7.13) and MAY file a DR against the Policy Store (Section 3.7.4). A Policy Store MUST reject as an error an attempt to store or update a policy containing an invalid value.",
        "document_section": "3.3.3.1.1",
        "description": "The ESRP must ignore invalid values and generate a Discrepancy Report; invalid policies are rejected by the Policy Store.",
        "test_id": "PS_007",
        "subtests": []
    },
    "RQ_PS_045": {
        "requirement_text": "Any “weekdayList” values that do not correspond to expected values MUST be ignored",
        "document_section": "3.3.3.1.1.1",
        "description": "Any invalid “weekdayList” values must be ignored.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_046": {
        "requirement_text": "(SIP Header condition members)",
        "document_section": "3.3.3.1.2",
        "description": "The SIP Header condition specifies valid header criteria members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_047": {
        "requirement_text": "(SIP Header condition members)",
        "document_section": "3.3.3.1.2",
        "description": "The SIP Header condition specifies valid header criteria members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_048": {
        "requirement_text": "(Additional Data condition condition members)",
        "document_section": "3.3.3.1.3",
        "description": "The Additional Data condition specifies members for defining data requirements.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_049": {
        "requirement_text": "(Additional Data condition condition members)",
        "document_section": "3.3.3.1.3",
        "description": "The Additional Data condition specifies members for defining data requirements.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_050": {
        "requirement_text": "(MIME Body List condition condition member)",
        "document_section": "3.3.3.1.4",
        "description": "The MIME Body List condition defines members for validating MIME body content.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_051": {
        "requirement_text": "(MIME Body List condition condition members",
        "document_section": "3.3.3.1.4",
        "description": "The MIME Body List condition defines members for validating MIME body content.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_052": {
        "requirement_text": "(Location condition condition members)",
        "document_section": "3.3.3.1.5",
        "description": "The Location condition defines members for specifying valid location parameters.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_053": {
        "requirement_text": "(Location condition condition members)",
        "document_section": "3.3.3.1.5",
        "description": "The Location condition defines members for specifying valid location parameters.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_054": {
        "requirement_text": "(Call Suspicion condition condition members)",
        "document_section": "3.3.3.1.6",
        "description": "The Call Suspicion condition includes members for evaluating call suspicion.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_055": {
        "requirement_text": "(Call Suspicion condition condition members)",
        "document_section": "3.3.3.1.6",
        "description": "The Call Suspicion condition includes members for evaluating call suspicion.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_056": {
        "requirement_text": "(Security Posture condition members)",
        "document_section": "3.3.3.1.7",
        "description": "The Security Posture condition specifies members for evaluating security status.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_057": {
        "requirement_text": "(Security Posture condition members)",
        "document_section": "3.3.3.1.7",
        "description": "The Security Posture condition specifies members for evaluating security status.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_058": {
        "requirement_text": "(Queue State condition members)",
        "document_section": "3.3.3.1.8",
        "description": "The Queue State condition defines members for assessing queue status.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_059": {
        "requirement_text": "(Queue State condition members)",
        "document_section": "3.3.3.1.8",
        "description": "The Queue State condition defines members for assessing queue status.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_060": {
        "requirement_text": "(LoST Service URN condition members)",
        "document_section": "3.3.3.1.9",
        "description": "The LoST Service URN condition specifies members for validating LoST service URNs.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_061": {
        "requirement_text": "(LoST Service URN condition members)",
        "document_section": "3.3.3.1.9",
        "description": "The LoST Service URN condition specifies members for validating LoST service URNs.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_062": {
        "requirement_text": "(Service State condition members)",
        "document_section": "3.3.3.1.10",
        "description": "The Service State condition defines the members for evaluating service status.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_063": {
        "requirement_text": "(Service State condition members)",
        "document_section": "3.3.3.1.10",
        "description": "The Service State condition defines the members for evaluating service status.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_064": {
        "requirement_text": "(Call Source condition members)",
        "document_section": "3.3.3.1.11",
        "description": "The Call Source condition defines the members for identifying the call source.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_065": {
        "requirement_text": "(Call Source condition members)",
        "document_section": "3.3.3.1.11",
        "description": "The Call Source condition defines the members for identifying the call source.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_066": {
        "requirement_text": "(Body Part condition members)",
        "document_section": "3.3.3.1.12",
        "description": "The Body Part condition specifies members for validating body parts in messages.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_067": {
        "requirement_text": "(Body Part condition members)",
        "document_section": "3.3.3.1.12",
        "description": "The Body Part condition specifies members for validating body parts in messages.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_068": {
        "requirement_text": "(Request URI condition members)",
        "document_section": "3.3.3.1.13",
        "description": "The Request URI condition defines members for validating request URIs.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_069": {
        "requirement_text": "(Body Part condition members)",
        "document_section": "3.3.3.1.13",
        "description": "The Body Part condition specifies members for validating body parts in messages.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_070": {
        "requirement_text": "(Normal-NextHop condition members)",
        "document_section": "3.3.3.1.14",
        "description": "The Normal-NextHop condition defines members for evaluating the next hop in routing.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_071": {
        "requirement_text": "(Normal-NextHop condition members)",
        "document_section": "3.3.3.1.14",
        "description": "The Normal-NextHop condition defines members for evaluating the next hop in routing.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_072": {
        "requirement_text": "(Incoming Queue condition members)",
        "document_section": "3.3.3.1.15",
        "description": "The Incoming Queue condition defines members for assessing the incoming call queue.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_073": {
        "requirement_text": "(Incoming Queue condition members)",
        "document_section": "3.3.3.1.15",
        "description": "The Incoming Queue condition defines members for assessing the incoming call queue.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_074": {
        "requirement_text": "(SDP Offer condition members)",
        "document_section": "3.3.3.1.16",
        "description": "The SDP Offer condition specifies members for evaluating SDP offers.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_075": {
        "requirement_text": "(SDP Offer condition members)",
        "document_section": "3.3.3.1.16",
        "description": "The SDP Offer condition specifies members for evaluating SDP offers.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_076": {
        "requirement_text": "(CAP condition members)",
        "document_section": "3.3.3.1.17",
        "description": "The CAP condition defines members for evaluating CAP-related criteria.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_077": {
        "requirement_text": "(CAP condition members)",
        "document_section": "3.3.3.1.17",
        "description": "The CAP condition defines members for evaluating CAP-related criteria.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_078": {
        "requirement_text": "(Calling Number Verification Status condition members)",
        "document_section": "3.3.3.1.18",
        "description": "The Calling Number Verification Status condition defines members for verifying calling numbers.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_079": {
        "requirement_text": "(Calling Number Verification Status condition members)",
        "document_section": "3.3.3.1.18",
        "description": "The Calling Number Verification Status condition defines members for verifying calling numbers.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_080": {
        "requirement_text": "A Route Policy document MUST be a JWS [171] as per Section 5.10 and MUST have a payload conforming to Appendix E.10.\n \n An 'Actions' object contains the following members:\n \n • actionType: a string which MUST exist and be set to the specific action type.\n • “description”: an OPTIONAL string containing a description of the action.\n • Other action-specific members as described in the below subsections.",
        "document_section": "3.3.3.2",
        "description": "A Route Policy document must be a JWS and include an 'Actions' object with required action type and description members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_081": {
        "requirement_text": "A Route Policy document MUST be a JWS [171] as per Section 5.10 and MUST have a payload conforming to Appendix E.10.\n \n An 'Actions' object contains the following members:\n \n • actionType: a string which MUST exist and be set to the specific action type.\n • “description”: an OPTIONAL string containing a description of the action.\n • Other action-specific members as described in the below subsections.",
        "document_section": "3.3.3.2",
        "description": "A Route Policy document must be a JWS and include an 'Actions' object with action type, description, and action-specific members.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_082": {
        "requirement_text": "Rules MUST NOT contain more than one Route, Busy or Invoke Policy action, or a combination of Route, Busy or Invoke Policy actions.",
        "document_section": "3.3.3.2",
        "description": "Rules must not include more than one Route, Busy, or Invoke Policy action, or any combination of them.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_083": {
        "requirement_text": "Rules MUST NOT contain more than one Route, Busy or Invoke Policy action, or a combination of Route, Busy or Invoke Policy actions.",
        "document_section": "3.3.3.2",
        "description": "Rules must not include more than one Route, Busy, or Invoke Policy action, or any combination of them.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_084": {
        "requirement_text": "(Route action members)",
        "document_section": "3.3.3.2.1",
        "description": "The Route action specifies members for defining routing behavior.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_085": {
        "requirement_text": "(Route action members)",
        "document_section": "3.3.3.2.1",
        "description": "The Route action specifies members for defining routing behavior.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_086": {
        "requirement_text": "The “NotifyAction” object has the following members:\n \n • “recipient”, which is OPTIONAL. When present, it MUST be either a URI or a service URN. This member is used to notify a single entity registered for the “eventCode”. If “recipient” is a URI, notification is generated for that specific recipient. If “recipient” is a service URN, the ECRF is used to map the service URN to a URI, and a notification is generated for that URI. Recipients MUST have subscribed for the “eventCode” to get the notification. If “recipient” is omitted, notification is generated for all subscribers to the “eventCode”. In all cases, notifications are subject to per-recipient throttling.\n \n • “eventCode”, which MUST exist and be set to a value contained in the EsrpNotifyEventCodes registry (Section 10.19).\n \n • “urgency”, which MUST exist and be set to an integer value from 0 and 100 where 0 is no urgency and 100 is the highest possible urgency.\n \n • “comment”, which is OPTIONAL. If present, it is a text string that is included in the “Comment” field of the NOTIFY message.",
        "document_section": "3.3.3.2.3",
        "description": "The NotifyAction object specifies members for defining recipient, event code, urgency, and optional comment.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_087": {
        "requirement_text": "The “NotifyAction” object has the following members:\n \n • “recipient”, which is OPTIONAL. When present, it MUST be either a URI or a service URN. This member is used to notify a single entity registered for the “eventCode”. If “recipient” is a URI, notification is generated for that specific recipient. If “recipient” is a service URN, the ECRF is used to map the service URN to a URI, and a notification is generated for that URI. Recipients MUST have subscribed for the “eventCode” to get the notification. If “recipient” is omitted, notification is generated for all subscribers to the “eventCode”. In all cases, notifications are subject to per-recipient throttling.\n \n • “eventCode”, which MUST exist and be set to a value contained in the EsrpNotifyEventCodes registry (Section 10.19).\n \n • “urgency”, which MUST exist and be set to an integer value from 0 and 100 where 0 is no urgency and 100 is the highest possible urgency.\n \n • “comment”, which is OPTIONAL. If present, it is a text string that is included in the “Comment” field of the NOTIFY message.",
        "document_section": "3.3.3.2.3",
        "description": "The NotifyAction object specifies recipient, event code, urgency, and an optional comment for notifications.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_088": {
        "requirement_text": "The “NotifyAction” object has the following members:\n \n • “recipient”, which is OPTIONAL. When present, it MUST be either a URI or a service URN. This member is used to notify a single entity registered for the “eventCode”. If “recipient” is a URI, notification is generated for that specific recipient. If “recipient” is a service URN, the ECRF is used to map the service URN to a URI, and a notification is generated for that URI. Recipients MUST have subscribed for the “eventCode” to get the notification.",
        "document_section": "3.3.3.2.3",
        "description": "The NotifyAction object specifies recipient and event code for notifications, subject to throttling.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_089": {
        "requirement_text": "(Log Message action members)",
        "document_section": "3.3.3.2.4",
        "description": "The Log Message action defines members for generating log messages.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_090": {
        "requirement_text": "(Log Message action members)",
        "document_section": "3.3.3.2.4",
        "description": "The Log Message action defines members for generating log messages.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_091": {
        "requirement_text": "(Invoke Policy action members)",
        "document_section": "3.3.3.2.5",
        "description": "The Invoke Policy action defines members for invoking a policy.",
        "test_id": "",
        "subtests": []
    },
    "RQ_PS_092": {
        "requirement_text": "(Invoke Policy action members)",
        "document_section": "3.3.3.2.5",
        "description": "The Invoke Policy action defines members for invoking a policy.",
        "test_id": "",
        "subtests": []
    }
}