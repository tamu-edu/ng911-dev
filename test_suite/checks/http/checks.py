import re

TYPE_NAMES = {'str': "a string",
              "int": "an integer",
              }


def validate_response_code(**result_data: dict[str: str]):
    """
    Validation of expected response code.
    """
    expected_code = result_data.get('expected_response_code', None)
    response_code = int(result_data.get('response', 0))
    try:
        assert response_code == expected_code, \
            f"FAILED-> Response code is not {expected_code}"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_response_code_class(**result_data: dict[str: str]):
    """
    Validation of response code class, example 1XX, 2XX, 3XX, 4XXX, 5XX.
    """
    code_class = result_data.get('expected_response_code_class', None)
    code_class_first_digit = str(code_class)[0]
    pattern = rf"^{code_class_first_digit}\d{{2}}$"
    response_code = str(result_data.get('response', 0))
    try:
        assert bool(re.match(pattern, response_code)), \
            f"FAILED-> Response code is not {code_class_first_digit}XX"
        return "PASSED"
    except AssertionError as e:
        return str(e)

 
def is_type(param, param_name,  expected_type) -> str:
    if isinstance(expected_type, tuple):
        type_name = 'an array'
    else:
        type_name = TYPE_NAMES[expected_type.__name__]
    return "PASSED" if isinstance(param, expected_type) \
        else f"FAILED-> '{param_name}' is not {type_name} type."

