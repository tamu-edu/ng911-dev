from checks.http.checks import validate_response_code_class


def verify_logger_response_code_extended(
    response_code,
    expected_response_code,
    request_x5u,
    logger_to_lis_request,
    is_x5u_the_same,
):
    print()
    try:
        # # TODO NOT IMPLEMENTED - STOP ITERATION
        # assert expected_response_code, \
        #     f"STOP ITERATION - No expected response code found"
        if expected_response_code == "201":
            assert (
                response_code == expected_response_code
            ), f"FAILED - Response code should be {expected_response_code}"
        else:
            _result = validate_response_code_class(
                expected_response_code_class=expected_response_code,
                response_code=response_code,
            )
            assert (
                _result == "PASSED"
            ), f"FAILED - Response code should be {expected_response_code}"

        if request_x5u:
            assert (
                logger_to_lis_request
            ), "FAILED - HTTP GET request to from Logging Service to Test System LIS not found"
            assert (
                is_x5u_the_same
            ), "FAILED - 'x5u' in in Logging service request to LIS doesn't match to original request"

        return "PASSED"
    except (AssertionError, ValueError) as e:
        return str(e)
