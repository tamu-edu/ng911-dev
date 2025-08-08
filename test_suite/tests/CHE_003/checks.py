def validate_language_response(response_result):
    if not response_result:
        return f"FAILED -> No language tags found"
    return 'PASS'
