from checks.jws.checks import (
    validate_jws_payload_serialization_format,
)


def validate_json_serialization_jws_format(
    test_data,
):
    try:
        assert test_data.stimulus_message, "NOT RUN -> No stimulus message found."

        assert (
            test_data.post_to_logger_message
        ), "FAILED -> No POST to logger message found."

        assert test_data.content_body, "FAILED -> No content found in HTTP POST body."

        jws_validation = validate_jws_payload_serialization_format(
            test_data.content_body,
            test_data.json_dict_body_from_message,
            test_data.cert_filepath,
            test_data.key_filepath,
        )
        assert jws_validation == "PASSED", jws_validation

        return "PASSED"
    except AssertionError as e:
        return str(e)
