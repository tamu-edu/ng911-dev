from services.aux_services.aux_services import is_valid_http_https_url

_UNSET = object()


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
        assert any(
            str(item) in str(parameter_value) for item in expected_values
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


def is_data_present(
    test_data,
    error="FAILED -> Data not found",
    precondition=_UNSET,
    precondition_error="Precondition is not met",
):
    """
    Asserts that the provided data is truthy.

    If precondition is supplied, it is validated first — if it is None the check
    returns FAILED immediately without evaluating test_data.
    If precondition is not supplied, no precondition check is performed.

    :param test_data: Data to validate for presence
    :param error: Error message if data is falsy
    :param precondition: Optional precondition value; must not be None when provided
    :param precondition_error: Error message if precondition is falsy

    """
    try:
        if precondition is not _UNSET:
            assert precondition is not None, f"NOT RUN -> {precondition_error}"
        assert test_data is not None, error
        assert test_data != [], error
        assert test_data != "", error
        assert test_data != {}, error
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


def check_each_element(check_method, collection, *args, element_attrs=None, **kwargs):
    """
    Runs the provided check method against every element of a collection.

    By default the element is passed as the first positional argument to
    check_method. If `element_attrs` is provided, per-element attributes are
    extracted and forwarded as keyword arguments instead — the element itself
    is NOT passed positionally. Any additional args/kwargs are forwarded
    unchanged on every iteration. Iteration stops at the first failing element
    and the failure is reported with its index (and key, when the collection
    is a mapping).

    :param check_method: A check function that returns "PASSED" on success or
        a string starting with "FAILED" / "NOT RUN" on failure
    :param collection: Iterable (list, tuple, set) or mapping whose elements
        will be validated
    :param element_attrs: Optional mapping of {kwarg_name: attribute_name}. When
        provided, for each element the named attributes are read via getattr
        and passed to check_method as the given kwargs
    :param args: Extra positional arguments forwarded to check_method
    :param kwargs: Extra keyword arguments forwarded to check_method
    """
    try:
        assert check_method is not None, "FAILED -> check method not provided"
        assert callable(check_method), "FAILED -> check method is not callable"
        assert collection is not None, "FAILED -> collection not provided"

        if isinstance(collection, dict):
            items = collection.items()
        else:
            items = enumerate(collection)

        checked = 0
        for index, element in items:
            checked += 1
            if element_attrs:
                element_kwargs = {
                    param: getattr(element, attr)
                    for param, attr in element_attrs.items()
                }
                result = check_method(*args, **element_kwargs, **kwargs)
            else:
                result = check_method(element, *args, **kwargs)
            assert (
                result == "PASSED"
            ), f"FAILED -> element at index {index} failed check: {result}"

        assert checked > 0, "FAILED -> collection is empty"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def is_parameter_not_equal_to_expected_value(
    parameter_name: str, parameter_value: str, unexpected_value: str
):
    """
    Test validating if parameter doesn't have one of expected values
    :param parameter_name: Name of parameter being tested
    :param parameter_value: Parameter value
    :param unexpected_value: Unexpected values as a list of string
    """
    try:
        assert parameter_name, "FAILED -> parameter name not found"
        assert (
            parameter_value
        ), f"FAILED -> parameter value for {parameter_name} not found"
        assert (
            unexpected_value
        ), f"FAILED -> unexpected value for {parameter_name} not found"
        assert (
            str(unexpected_value).lower() not in str(parameter_value).lower()
        ), f"FAILED -> Unexpected value '{unexpected_value}' found in {parameter_name}"
        return "PASSED"
    except AssertionError as e:
        return str(e)
