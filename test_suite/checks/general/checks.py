from services.aux_services.aux_services import is_valid_http_https_url


def test_if_parameter_has_expected_value(
    parameter_name: str, parameter_value: str, expected_value: str
):
    """
    Test validating if parameter has expected value
    :param parameter_name: Name of parameter being tested
    :param parameter_value: Parameter value
    :param expected_value: Expected value of parameter
    """
    try:
        assert parameter_name, "FAILED -> parameter name not found"
        assert (
            parameter_value
        ), f"FAILED -> parameter value for {parameter_name} not found"
        assert (
            expected_value
        ), f"FAILED -> expected value for {parameter_name} not found"
        assert (
            expected_value in parameter_value
            or f"{expected_value.split(':')[0]}:None" in parameter_value
        ), f"FAILED -> expected value '{expected_value}' not found in {parameter_name}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_if_parameter_has_one_of_expected_values(
    parameter_name: set, parameter_value: str, expected_values: list
):
    """
    Test validating if parameter has one of expected values
    :param parameter_name: Name of parameter being tested
    :param parameter_value: Parameter value
    :param expected_values: Expected values as a list of string
    """
    try:
        assert parameter_name, "FAILED -> parameter name not found"
        assert (
            parameter_value
        ), f"FAILED -> parameter value for {parameter_name} not found"
        assert (
            expected_values
        ), f"FAILED -> expected values list for {parameter_name} not found"
        assert all(
            item in parameter_value for item in expected_values
        ), f"FAILED -> Some parameters are missing in expected values: {expected_values}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_if_url_is_valid(url: str):
    """
    Test validating if parameter is a valid URL
    :param url: URL string for test
    """
    try:
        assert url, "FAILED -> URL not found"
        assert is_valid_http_https_url(url), "FAILED -> incorrect URL"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def is_data_present(test_data, error="FAILED -> Data not found"):
    """
    Asserts that the provided data is truthy.
    :param test_data: Data to validate for presence
    :param error: Error message if data is falsy
    :raises AssertionError: If data is falsy
    """
    try:
        assert test_data is not None, error
        assert test_data, error
        return "PASSED"
    except AssertionError as e:
        return str(e)


def is_test_data_the_same(expected_data, actual_data, error=None):
    """
    Asserts that expected and actual data are equal in value and type.
    :param expected_data: The expected value to compare against
    :param actual_data: The actual value produced by the system under test
    :param error: Optional custom error message prefix on mismatch
    :raises AssertionError: If either value is falsy, types differ, or values are not equal
    """
    if not error:
        error = f"FAILED -> Data doesn't match.\n***Expected***:\n{expected_data}\n***Actual***:\n{actual_data}"
    else:
        error = f"FAILED -> {error}.\n ***Expected***:\n{expected_data}\n***Actual***:\n{actual_data}"
    try:
        assert expected_data is not None, "FAILED -> expected data cannot be None."
        assert actual_data is not None, "FAILED -> actual data cannot be None."
        assert isinstance(
            actual_data, type(expected_data)
        ), f"FAILED -> type mismatch.\n***Expected***:\n{type(expected_data)}\n***Actual***:\n{type(actual_data)}"
        assert actual_data == expected_data, error
        return "PASSED"
    except AssertionError as e:
        return str(e)
