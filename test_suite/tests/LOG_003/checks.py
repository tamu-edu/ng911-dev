import json
import re

from checks.http.checks import is_type
from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN


def validate_logger_response_data(**result_data: dict[str: str]):
    """
    Validation of response code. Expected value code - 201.
    """

    if result_data['response'].http.response_code != '201':
        return "FAILED-> Response code is not 201"

    logEventId = json.loads(result_data['response'].json.object)['logEventId']
    if (result := is_type(logEventId, 'logEventId', str)) != 'PASSED':
        # Test step result FAILED in case of invalid format
        return result

    if 'urn:emergency:uid:logid:' not in logEventId:
        return "FAILED-> Missing 'urn:emergency:uid:logid:' in 'logEventId' "

    match = re.search(r'logid:([^:]+):', logEventId)
    logId_string = match.group(1)
    if not (10 <= len(set(logId_string)) <= 36):
        return "FAILED-> 'logEventId' doesn't contain unique string 10 to 36 characters long"

    fqdn = logEventId.split(f'{logId_string}:')[1]
    if not re.search(FQDN_PATTERN, fqdn):
        return "FAILED-> 'logEventId' doesn't contain FQDN of Logging Service"

    return "PASSED"
