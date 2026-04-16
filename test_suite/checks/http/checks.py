import re

TYPE_NAMES = {
    "str": "a string",
    "int": "an integer",
}


def validate_response_code(**result_data):
    """
    Validation of expected response code.
    """
    expected_code = result_data.get("expected_response_code", None)
    response_code = result_data.get("response", None)

    try:
        assert (
            response_code == expected_code
        ), f"FAILED-> Response code is not {expected_code}. Actual response code - {response_code}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_response_code_class(expected_response_code_class, response_code):
    """
    Validation of response code class, example 1XX, 2XX, 3XX, 4XXX, 5XX.
    """
    pattern_template = r"^{prefix}\d{{2}}$"

    try:
        assert (
            expected_response_code_class
        ), "FAILED-> Response code class cannot be None"
        assert response_code, "FAILED-> Response code cannot be None"
        code_class_first_digit = str(expected_response_code_class)[0]
        assert bool(
            re.match(
                pattern_template.format(prefix=code_class_first_digit), response_code
            )
        ), f"FAILED-> Response code class is not {code_class_first_digit}XX. Actual response code - {response_code}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def is_type(param, param_name, expected_type) -> str:
    if not param:
        return "FAILED-> No input data found for type verification."
    if isinstance(expected_type, tuple):
        type_name = "an array"
    else:
        type_name = TYPE_NAMES[expected_type.__name__]
    return (
        "PASSED"
        if isinstance(param, expected_type)
        else f"FAILED-> '{param_name}' is not {type_name} type."
    )
