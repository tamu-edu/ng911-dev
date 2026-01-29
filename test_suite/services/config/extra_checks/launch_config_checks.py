def some_check(field_name: str, field_value) -> (bool, str):
    """
    EXAMPLE
    :param field_name: str
    :param field_value: value of the field form config
    :return: tuple(bool,str)
    """
    if field_value:
        return True, ""
    return False, f"Error, {field_name} value is missing while is required"
