import json
from json import JSONDecodeError

from checks.http.checks import is_type
from services.aux_services.json_services import is_jws


def validate_policy_store_response_body(**response_data: dict[str: str]):
    """
    Validation of policyStore response boody for 200 response code.
    Expected data in body:
     *'PolicyArray' with 'count', 'totalCount' and 'policies' members
     *'count' has integer value with number of items in 'policies'
     *'totalCount' has integer value
     *'policies' is array with JWS elements.
    """
    if not response_data['response']:
        return "FAILED-> Output message is not found"
    if response_data['response'].http.response_code != '200':
        return "FAILED-> Response code is not 200"
    try:
        policy_store_data = json.loads(response_data['response'].json.object)
    except JSONDecodeError:
        return f"FAILED ->'Invalid JSON response"

    # Validate that 'PolicyArray' is an array
    if (result := is_type(policy_store_data['PolicyArray'],
                          'PolicyArray',
                          (list, dict))) != 'PASSED':
        # Test step result FAILED in case of invalid format
        return result

    # Validate policyArray elements
    for policy_element in policy_store_data['PolicyArray']:
        try:
            # Validate each element of 'policyArray'
            # Test step result FAILED in case of invalid format

            # Validate 'count' is int
            if (result := is_type(policy_element.get('count', None), 'count', int)) != 'PASSED':
                return result
            assert policy_element['count'] == len(policy_element['policies']), \
                "FAILED ->'PolicyArray' has different number of policies"

            # Validate 'totalCount' is int
            if (result := is_type(policy_element.get('totalCount', None), 'totalCount', int)) != 'PASSED':
                return result

            # Validate that 'policies' is an array
            if (result := is_type(policy_element.get('policies', None),
                                  'policies',
                                  (list, dict))) != 'PASSED':
                return result
            for policy in policy_element['policies']:
                assert is_jws(policy), \
                    "FAILED ->'Invalid JWS token"
                return "PASSED"
        except AssertionError as e:
            return str(e)
