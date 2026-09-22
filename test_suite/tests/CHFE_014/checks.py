def validate_multipart_mixed_support(
    response_code, expected_response_code, stimulus_content_type
):
    try:
        assert (
            stimulus_content_type
        ), "NOT RUN -> No SIP INVITE with Content-Type header found in stimulus."
        assert "multipart/mixed" in stimulus_content_type.lower(), (
            "NOT RUN -> Stimulus SIP INVITE is not multipart/mixed "
            f"(Content-Type: '{stimulus_content_type}')."
        )

        assert response_code, "FAILED -> No 200 OK response code from CHFE found."
        assert str(response_code) == str(expected_response_code), (
            f"FAILED -> Wrong CHFE response code: "
            f" expected '{expected_response_code}', got '{response_code}'."
        )

        return "PASSED"
    except AssertionError as e:
        return str(e)
