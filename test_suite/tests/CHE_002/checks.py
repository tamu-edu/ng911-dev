from services.aux_services.sip_msg_body_services import is_having_similar_attrs


def validate_supported_media_type(response_code, expected_response_code, expected_media_attrs, actual_media_attrs):

    if not response_code:
        return "FAILED -> No 200 OK response code from CHE found."
    if not actual_media_attrs:
        return "FAILED -> No media information is found in CHE response."

    if str(response_code) != str(expected_response_code):
        return "FAILED -> Wrong CHE response code."

    if not actual_media_attrs:
        return "FAILED -> No media information present in CHE response."

    for media_attr in expected_media_attrs:
        # Check if expected string with media attribute is present in any of actual string returned by CHE
        if media_attr in actual_media_attrs:
            continue
        else:
            # If expected attribute is not fond try to find the same attributes
            # in messages but in a different attribute order
            if not is_having_similar_attrs(media_attr, actual_media_attrs):
                return "FAILED -> Media information in SIP INVITE and CHE response doesn't match."

    return "PASSED"
