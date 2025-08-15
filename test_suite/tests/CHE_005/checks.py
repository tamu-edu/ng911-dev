from services.aux_services.sip_msg_body_services import is_having_similar_attrs


def validate_che_response(response_code, expected_media_attrs, actual_media_attrs):
    try:
        assert response_code, "FAILED -> No 200 OK response code from CHE found."
        assert actual_media_attrs,  "FAILED -> No media information is found in CHE response."

        for media_attr in expected_media_attrs:
            # Check if expected string with media attribute is present in any of actual string returned by CHE
            if media_attr in actual_media_attrs:
                continue
            else:
                # If expected attribute is not fond try to find the same attributes
                # in messages but in a different attribute order
                assert is_having_similar_attrs(media_attr, actual_media_attrs), \
                    "FAILED -> Media information in SIP INVITE and CHE response doesn't match."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_che_response_code(response_code):
    try:
        response_code = str(response_code)

        assert response_code in ('200', '486', '404'), "FAILED -> No response from CHE"

        if response_code == '200':
            return "PASSED"
        elif response_code == '486':
            return "PASSED -> CHE is busy"
        elif response_code == '404':
            return "PASSED -> Test service not supported"
    except AssertionError as e:
        return str(e)
