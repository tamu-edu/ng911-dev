def verify_location_and_dereferencing(geolocation_request, geolocation_incoming_data):
    # Validate input data
    if not geolocation_request:
        return "FAILED -> Cannot found dereferencing message from ESRP to Test System."

    if not hasattr(geolocation_request, 'xml') or not geolocation_request.xml.get('cdata', None):
        return "FAILED -> Cannot found XML data in dereferencing message from ESRP."

    if geolocation_incoming_data != geolocation_request.xml.get('cdata', None):
        return "FAILED -> Location data doesn't match"

    return "PASSED"
