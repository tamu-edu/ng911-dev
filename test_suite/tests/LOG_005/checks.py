import json
from json import JSONDecodeError

from checks.http.checks import is_type
from services.aux_services.json_services import validate_identifier


def validate_response_json_body_for_http_get_on_log_event_ids_entry_point(**result_data: dict[str: str]):
    if not result_data['response']:
        return "FAILED-> No output message found"

    if result_data['response'].http.response_code != '200':
        return "FAILED-> Response code is not 200"

    fields = {"count": int,
              "totalCount": int}
    fields.update(result_data['additional_element'])

    array_name = result_data['array_name']
    id_name = result_data['id_name']

    for key, value in fields.items():
        try:
            elem = json.loads(result_data['response'].json.object)[key]
        except AttributeError or JSONDecodeError:
            return "FAILED -> Cannot find JSON data in output message"
        if (result := is_type(elem, key, value)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result
    for element in json.loads(result_data['response'].json.object)[array_name]:
        # Validate that only one 'logEventId' exists which is a string
        log_event_id = element.get(id_name, None)
        if not log_event_id:
            return f"FAILED-> '{id_name}' is missing"
        if (result := is_type(log_event_id, 'logEvent', str)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result
        if (result := validate_identifier(log_event_id, id_name)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

    return "PASSED"
