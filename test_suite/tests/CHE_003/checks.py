def validate_language_response(**response_data):
    result = response_data['response_result']
    if not result:
        return f"FAILED -> No language tags found"
    return 'PASS'
