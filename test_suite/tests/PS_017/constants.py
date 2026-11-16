NOT_RUN = "NOT RUN -> No stimulus message found."
NO_PS_RESPONSE = "FAILED -> No Policy Store response found."
POLICIES_URL_PART = "Policies"

PUT_VARIATIONS = (8, 9, 10, 11, 12, 13)
SUCCESS_VARIATION = 1

VARIATIONS = {
    "HTTP_POST_with_correct_NormalNextHopCondition": 1,
    "HTTP_POST_with_NormalNextHopCondition_missing_operator": 2,
    "HTTP_POST_with_NormalNextHopCondition_operator_integer": 3,
    "HTTP_POST_with_NormalNextHopCondition_with_operator_unsupported_value": 4,
    "HTTP_POST_with_NormalNextHopCondition_missing_content": 5,
    "HTTP_POST_with_NormalNextHopCondition_content_integer": 6,
    "HTTP_POST_with_NormalNextHopCondition_with_content_value_missing_in_2nd_condition": 7,
    "HTTP_PUT_with_NormalNextHopCondition_missing_operator": 8,
    "HTTP_PUT_with_NormalNextHopCondition_operator_integer": 9,
    "HTTP_PUT_with_NormalNextHopCondition_with_operator_unsupported_value": 10,
    "HTTP_PUT_with_NormalNextHopCondition_missing_content": 11,
    "HTTP_PUT_with_NormalNextHopCondition_content_integer": 12,
    "HTTP_PUT_with_NormalNextHopCondition_with_content_value_missing_in_2nd_condition": 13,
}

# Expected Policy Store response code to the preliminary POST in PUT variations
SETUP_POST_EXPECTED_CODE = "201"
