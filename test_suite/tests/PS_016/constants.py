NOT_RUN = "NOT RUN -> No stimulus message found."
NO_PS_RESPONSE = "FAILED -> No Policy Store response found."
POLICIES_URL_PART = "Policies"

PUT_VARIATIONS = (7, 8, 9, 10, 11)
SUCCESS_VARIATION = 1

VARIATIONS = {
    "HTTP_POST_with_correct_LostServiceUrnCondition": 1,
    "HTTP_POST_with_LostServiceUrnCondition_missing_urn": 2,
    "HTTP_POST_with_LostServiceUrnCondition_urn_integer": 3,
    "HTTP_POST_with_LostServiceUrnCondition_with_urn_value_urn_servicee_sos": 4,
    "HTTP_POST_with_LostServiceUrnCondition_with_urn_value_urn_emergencyy_service_sos": 5,
    "HTTP_POST_with_LostServiceUrnCondition_with_urn_value_missing_in_2nd_condition": 6,
    "HTTP_PUT_with_LostServiceUrnCondition_missing_urn": 7,
    "HTTP_PUT_with_LostServiceUrnCondition_urn_integer": 8,
    "HTTP_PUT_with_LostServiceUrnCondition_with_urn_value_urn_servicee_sos": 9,
    "HTTP_PUT_with_LostServiceUrnCondition_with_urn_value_urn_emergencyy_service_sos": 10,
    "HTTP_PUT_with_LostServiceUrnCondition_with_urn_value_missing_in_2nd_condition": 11,
}

# Expected Policy Store response code to the preliminary POST in PUT variations
SETUP_POST_EXPECTED_CODE = "201"
