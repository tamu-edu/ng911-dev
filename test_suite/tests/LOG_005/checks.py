import json
from checks.http.checks import is_type
from services.aux.json_services import validate_log_event_id


def validate_response_json_body_for_http_get_on_log_event_ids_entry_point(**result_data: dict[str: str]):

    fields = {"count": int,
              "totalCount": int,
              "logEventIds": (list, dict, tuple)}

    if result_data['response'].http.response_code != '200':
        return "FAILED-> Response code is not 200"

    for key, value in fields.items():
        elem = json.loads(result_data['response'].json.object)[key]
        if (result := is_type(elem, key, value)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result
    for element in json.loads(result_data['response'].json.object)['logEventIds']:
        # Validate that only one 'logEventId' exists which is a string
        log_event_id = element.get('logEventId', None)
        if not log_event_id:
            return "FAILED-> 'logEventId' is missing"
        if (result := is_type(log_event_id, 'logEvent', str)) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result
        if (result := validate_log_event_id(log_event_id, 'logEventId')) != 'PASSED':
            # Test step result FAILED in case of invalid format
            return result

    return "PASSED"
