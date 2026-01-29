from services.aux_services.sip_msg_body_services import is_having_similar_attrs


def validate_chfe_response(response_code, expected_media_attrs, actual_media_attrs):
    try:
        assert response_code, "FAILED -> No 200 OK response code from CHFE found."
        assert actual_media_attrs,  "FAILED -> No media information is found in CHFE response."

        for media_attr in expected_media_attrs:
            # Check if expected string with media attribute is present in any of actual string returned by CHFE
            if media_attr in actual_media_attrs:
                continue
            else:
                # If expected attribute is not fond try to find the same attributes
                # in messages but in a different attribute order
                assert is_having_similar_attrs(media_attr, actual_media_attrs), \
                    "FAILED -> Media information in SIP INVITE and CHFE response doesn't match."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_chfe_response_code(response_code):
    try:
        response_code = str(response_code)

        assert response_code in ('200', '486', '404'), "FAILED -> No response from CHFE"

        if response_code == '200':
            return "PASSED"
        elif response_code == '486':
            return "PASSED -> CHFE is busy"
        elif response_code == '404':
            return "PASSED -> Test service not supported"
    except AssertionError as e:
        return str(e)
