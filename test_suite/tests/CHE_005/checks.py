from services.aux_services.sip_msg_body_services import is_having_similar_attrs


def validate_che_response_code(**test_data):
    response_code, expected_media_attrs, actual_media_attrs = test_data.values()
    if not response_code:
        return "FAILED -> No 200 OK response code from CHE found."
    if not actual_media_attrs:
        return "FAILED -> No media information is found in CHE response."

    for media_attr in expected_media_attrs:
        # Check if expected string with media attribute is present in any of actual string returned by CHE
        if media_attr in actual_media_attrs:
            continue
        else:
            # If expected attribute is not fond try to find the same attributes
            # in messages but in a different attribute order
            if not is_having_similar_attrs(media_attr, actual_media_attrs):
                return "FAILED -> Media information in SIP INVITE and CHE response doesn't match."

    if str(response_code) == '200':
        return "PASSED"
    elif str(response_code) == '486':
        return "PASSED -> CHE is busy"
    elif str(response_code) == '404':
        return "PASSED -> Test service not supported"
    else:
        return "FAILED -> No response from CHE"
