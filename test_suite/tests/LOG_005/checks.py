from json import JSONDecodeError

from checks.http.checks import is_type
from services.aux_services.json_services import validate_identifier

from test_suite.services.aux_services.message_services import (
    extract_json_data_from_http,
)


def validate_response_json_body_for_http_get_on_log_event_ids_entry_point(
    **result_data: dict[str:str],
):
    try:
        assert result_data.get("response", None), "FAILED-> No output message found"

        assert (
            result_data["response"].http.response_code == "200"
        ), "FAILED-> Response code is not 200"

        fields = {"count": int, "totalCount": int}
        fields.update(result_data["additional_element"])

        array_name = result_data["array_name"]
        id_name = result_data["id_name"]

        call_id = result_data.get("call_id", None)
        incident_id = result_data.get("incident_id", None)

        for key, value in fields.items():
            try:
                elem = extract_json_data_from_http(result_data["response"])
            except (AttributeError, JSONDecodeError):
                return "FAILED -> Cannot find JSON data in output message"
            try:
                elem = elem[key]
            except KeyError:
                return f"FAILED -> Cannot find {key} in JSON data"

            assert (
                result := is_type(elem, key, value)
            ) == "PASSED", f"FAILED -> {result}"

        for record in extract_json_data_from_http(result_data["response"])[array_name]:
            # Validate that only one 'logEventId' exists which is a string
            log_event_id = record.get(id_name, None)

            assert log_event_id, f"FAILED-> '{id_name}' is missing"

            # Test step result FAILED in case of invalid format
            assert (
                result := is_type(log_event_id, "logEvent", str)
            ) == "PASSED", f"FAILED -> {result}"

            # Test step result FAILED in case of invalid format
            assert (
                result := validate_identifier(log_event_id, id_name)
            ) == "PASSED", f"FAILED -> {result}"

            if call_id:
                for logger_record_call_id in record[id_name]:
                    assert (
                        call_id == logger_record_call_id
                    ), "FAILED -> callId from Logger doesn't match initial callId sent by ESRP TS"
            if incident_id:
                for logger_record_call_id in record[id_name]:
                    assert (
                        call_id == logger_record_call_id
                    ), "FAILED -> incidentID from Logger doesn't match initial incidentId sent by ESRP TS"

        return "PASSED"
    except (AssertionError, ValueError, AttributeError, JSONDecodeError, KeyError) as e:
        return str(e)
