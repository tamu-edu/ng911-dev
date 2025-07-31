from services.aux_services.json_services import get_jws_from_http_media_layer


def validate_jws_in_http_response_from_ps(**test_data):
    jws_in_request = test_data['jws_from_request'].replace('\n', '')
    http_response = test_data['http_response']

    if not jws_in_request:
        return "FAILED-> No HTTP POST request with JWS found."

    jws_from_ps_response = get_jws_from_http_media_layer(http_response).replace('\n', '')

    if not jws_from_ps_response:
        return "FAILED-> No JWS found in PS response."
    if jws_in_request != jws_from_ps_response:
        return "FAILED-> JWS from POST REQUEST doesn't match JWS from Policy Store."

    return "PASSED"
