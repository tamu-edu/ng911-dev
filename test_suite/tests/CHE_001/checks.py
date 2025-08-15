from test_suite.services.aux_services.message_services import extract_all_contents_from_message_body
from test_suite.services.aux_services.xml_services import is_valid_xml


def verify_http_held(response, geolocation):
    if not response:
        return "FAILED-> No HTTP HELD response found."
    # TODO Liubomyr - verification to seed our message from list of messasges
    response = response[0]
    if not response or not hasattr(response, 'http'):
        return "FAILED-> HELD request to LIS has not been found"
    if response.http.get('request_method') not in ('POST', 'GET'):
        return "FAILED-> HELD request to LIS has incorrect method"
    try:
        if (response.http.get('request_full_uri').removeprefix("http://").removeprefix("https://")
                not in geolocation):
            return "FAILED-> Wrong request URI in HELD request"
    except AttributeError:
        return "FAILED-> correct Request URI has not been found in HELD request"
    if response.http.get('request_method') == 'POST':
        msg_bodies = [c.get('body') for c in extract_all_contents_from_message_body(response)
                      if is_valid_xml(c.get('body'))]
        if all(not xml for xml in msg_bodies):
            return "FAILED-> not found any valid XML body"

        required_str = ['xmlns="urn:ietf:params:xml:ns:geopriv:held"', '<locationRequest']
        for body in msg_bodies:
            has_all_required = all(s in body for s in required_str)
            if has_all_required:
                break
        else:
            return "FAILED-> not found any valid locationRequest XML body"

    return "PASSED"


def verify_sip_subscribe(**response_data):
    try:
        subscribe_resp, ok_resp = response_data['response']
    except ValueError:
        return "FAILED-> Missing SIP SUBSCRIBE/OK message"
    try:
        status_code = ok_resp.sip.status_code
        if status_code != '200':
            return "FAILED-> CHE does not respond for SIP NOTIFY with status code 200"
    except AttributeError:
        return "FAILED-> No 200 OK status code found."
    try:
        subscribe_resp_to_header = str(subscribe_resp.sip.get('to'))
        if response_data['geolocation'].removeprefix("<cid:").removesuffix(">") not in subscribe_resp_to_header:
            return "FAILED-> Wrong Geolocation data"
    except AttributeError:
        return "FAILED-> correct SIP SUBSCRIBE message has not been found"

    if str(subscribe_resp.sip.get('event')) != 'presence':
        return "FAILED-> Wrong Event data"
    if str(subscribe_resp.sip.get('accept')) != 'application/pidf+xml':
        return "FAILED-> Wrong Accept data"
    return "PASSED"
