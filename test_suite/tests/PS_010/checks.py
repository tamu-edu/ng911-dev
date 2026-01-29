from checks.http.checks import validate_response_code_class


def validate_policy_created_successfully(send_policy, policy_created_status_code, exp_resp_code_policy_created):
    try:
        # # TODO NOT IMPLEMENTED - STOP ITERATION
        # assert send_policy, \
        #     f"STOP ITERATION - No message has been found"
        # assert exp_resp_code_policy_created, \
        #     f"STOP ITERATION - No expected response code found"

        assert policy_created_status_code, \
            f"INCONCLUSIVE - No '201 Policy Successfully Created' response code not found"
        assert policy_created_status_code == exp_resp_code_policy_created, \
            f"INCONCLUSIVE - PS response code:{policy_created_status_code} doesnt match expected response code:{exp_resp_code_policy_created}"
        return "PASSED"
    except (AssertionError, ValueError) as e:
        return str(e)


def validate_expired_policy_response(is_get_request_time_correct,
                                     expired_get_request,
                                     policy_expired_status_code,
                                     exp_resp_code_expired):
    try:
        # # TODO NOT IMPLEMENTED - STOP ITERATION
        # assert is_get_request_time_correct, \
        #      f"STOP ITERATION - GET request from TS to PS sent too early OR cannot find 'timestamp' in the payload."
        # assert expired_get_request, \
        #     f"STOP ITERATION - No stimulus message has been found"
        # assert exp_resp_code_expired, \
        #     f"STOP ITERATION - No expected response code found"

        assert policy_expired_status_code, \
            f"FAILED - No '4XX' response code from Policy Store not found"
        assert (result := validate_response_code_class(exp_resp_code_expired,
                                                       policy_expired_status_code)) == 'PASSED', \
            result
        return "PASSED"
    except (AssertionError, ValueError) as e:
        return str(e)

