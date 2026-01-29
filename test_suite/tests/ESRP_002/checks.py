def verify_location_and_dereferencing(http_lost_request, dereferenced_geolocation_data):
    # Validate input data
    if not http_lost_request:
        return "FAILED -> HTTP LoST request from ESRP not found."

    if not hasattr(http_lost_request, 'xml') or not http_lost_request.xml.get('cdata', None):
        return "FAILED -> HTTP LoST request from ESRP has missing XML message body"

    if dereferenced_geolocation_data != http_lost_request.xml.get('cdata', None):
        return ("FAILED -> Location data doesn't match. HTTP LoST from ESRP does not contain geolocation "
                "dereferenced from requested LIS server")

    return "PASSED"
