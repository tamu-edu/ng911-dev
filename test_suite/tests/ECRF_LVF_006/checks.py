from checks.http.checks import is_type
from datetime import datetime

from services.aux_services.json_services import is_valid_json
from services.aux_services.message_services import (
    is_valid_catype_schema,
    is_equal_or_after,
)
from services.aux_services.xml_services import is_valid_xml


def validate_ecrf_response_data(
    response_data, expected_response_code, response_code, variation_url, xml_tag_as_of
):
    """
    Verification of variations #1/3/4 and 5 for ECRF-LVF_006 test.

    Variation 1:
    Responds with 200 OK response containing correct findServiceResponse XML body
    findServiceResponse contains 'asOf' with timestamp the same date and time as requested in the stimulus 'asOf'

    Variation 3:
    responds with 200 OK containing correct JSON body
    JSON body contains PlannedChangeIdList array with string items

    Variation 4:
    initial and latest JSON should be different - updating planned changes database
    should trigger ECRF-LVF to update PlannedChangeIdList as well

    Variation 5:
    responds with 200 OK containing correct JSON body
    JSON body contains ChangeSet object with:
        'changeSetID' string value
        'changeSetEffective' with timestamp (containing timezone)
        'partialLocationList' array with:
            'namespace' string value being "Namespace URI"
            from CAtype IANA registry (f.e. urn:ietf:params:xml:ns:pidf:geopriv10:civicAddr)
            'caType' string value with CAtype from IANA registry (f.e. 16)
            'value' string

    :param response_data: timestamp data/ JSON or XML data to verify
    :param expected_response_code: expected response code string
    :param response_code: actual response code string
    :param variation_url: url specific to variation
    :param xml_tag_as_of: xml tag from request
    :return: 'PASSED' or 'FAILED' test result
    """

    try:
        assert (
            response_code == expected_response_code
        ), f"FAILED-> Response code is not {expected_response_code}"

        assert response_data, "FAILED-> No output message found"

        # TODO NOT IMPLEMENTED - STOP ITERATION
        # assert xml_tag_as_of, \
        #     "STOP ITERATION> Cannot found stimulus xml file"

        # Variation 1
        if (
            response_data
            and not isinstance(response_data, dict)
            and "LoST".lower() in variation_url.lower()
        ):
            # findServiceResponse has timestamp as requested in 'asOf'
            assert is_valid_xml(response_data), "FAILED-> Malformed XML data"

            assert is_equal_or_after(
                xml_tag_as_of, response_data
            ), "FAILED-> 'findServiceResponse' timestamp should be equal or after requested."
        else:
            assert is_valid_json(response_data), "FAILED-> Malformed JSON data"
            # Variation #3/4
            if "PlannedChangePoll".lower() in variation_url.lower():
                # Variation #4
                if isinstance(response_data, set):
                    assert (
                        len(response_data) > 1
                    ), "FAILED-> ECRF-LVF response should be a data array with at least 2 responses."
                else:
                    # Variation #3
                    assert isinstance(
                        response_data, dict
                    ), "FAILED-> ECRF-LVF response should be a data array."

                    assert (
                        "PlannedChangeIdList" in response_data.keys()
                    ), "FAILED-> No 'PlannedChangeIdList' in JSON response"

                    planned_changed_id_list = response_data.get(
                        "PlannedChangeIdList", None
                    )

                    assert (
                        result := is_type(
                            planned_changed_id_list, "PlannedChangeIdList", (list, dict)
                        )
                    ) == "PASSED", f"FAILED-> {result}"
                    assert all(
                        [isinstance(item, str) for item in planned_changed_id_list]
                    ), "FAILED-> All items inside of 'PlannedChangeIdList' should be strings"
            else:
                # VARIATION #5
                assert (
                    "ChangeSet" in response_data
                ), "FAILED->  'ChangeSet' key missing from response_data."

                change_set = response_data["ChangeSet"]

                assert (
                    result := is_type(change_set, "ChangeSet", (list, dict))
                ) == "PASSED", f"FAILED-> {result}"

                assert (
                    "changeSetId" in change_set
                ), "FAILED-> 'changeSetID' key missing from ChangeSet."

                assert (
                    result := is_type(change_set["changeSetId"], "changeSetId", str)
                ) == "PASSED", f"FAILED-> {result}"

                assert (
                    "changeSetEffective" in change_set
                ), "FAILED->  'changeSetEffective' key missing from ChangeSet."

                assert (
                    result := is_type(
                        change_set["changeSetEffective"], "changeSetEffective", str
                    )
                ) == "PASSED", f"FAILED-> {result}"

                dt = datetime.fromisoformat(change_set["changeSetEffective"])

                # Check if timezone info is present
                assert dt.tzinfo, (
                    f"FAILED->  Validation Error: 'changeSetEffective' "
                    f"timestamp '{change_set['changeSetEffective']}' is missing timezone info."
                )

                assert (
                    "partialLocationList" in change_set
                ), "FAILED-> 'partialLocationList' key missing from ChangeSet."

                assert (
                    result := is_type(
                        change_set["partialLocationList"],
                        "partialLocationList",
                        (list, dict),
                    )
                ) == "PASSED", f"FAILED-> {result}"

                partial_location_list = change_set["partialLocationList"]

                # Check for 'namespace'
                for record in partial_location_list:
                    assert (
                        "namespace" in record
                    ), "FAILED-> 'namespace' missing in 'partialLocationList'"

                    assert (
                        "caType" in record
                    ), "FAILED-> 'caType' missing in 'partialLocationList item'."

                    ca_type = record.get("caType", None)
                    namespace = record.get("namespace", None)
                    assert is_valid_catype_schema(
                        ca_type, namespace
                    ), "FAILED-> Invalid 'caType' or 'namespace'."

                    # Check for 'value'
                    assert (
                        "value" in record
                    ), "FAILED-> 'value' missing in 'partialLocationList item'."

                    assert (
                        result := is_type(record["value"], "value", str)
                    ) == "PASSED", f"FAILED-> {result}"

        return "PASSED"
    except (AssertionError, ValueError) as e:
        return str(e)
