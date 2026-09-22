def validate_language_response(response_result):
    try:
        assert response_result, "FAILED -> No language tags found"
        return "PASSED"
    except AssertionError as e:
        return str(e)
