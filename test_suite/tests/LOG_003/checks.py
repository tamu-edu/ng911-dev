import re
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN


def validate_logger_response_data(response, log_event_id, log_id_string, fqdn):
    try:
        assert response, "FAILED-> Not response message found."
        assert log_event_id, "FAILED-> Not 'logEventId' found in response message."
        assert log_id_string, "FAILED-> Not 'logId' string data found in response message."
        assert fqdn, "FAILED-> Not 'fqdn' found in response message."

        assert 'urn:emergency:uid:logid:' in log_event_id, \
            "FAILED-> Missing 'urn:emergency:uid:logId:' in 'logEventId'."

        assert (10 <= len(set(log_id_string)) <= 36), \
            "FAILED-> 'logEventId' doesn't contain unique string 10 to 36 characters long."

        assert re.search(FQDN_PATTERN, fqdn), \
            "FAILED-> 'logEventId' doesn't contain FQDN of Logging Service."

        return "PASSED"
    except AssertionError as e:
        return str(e)
