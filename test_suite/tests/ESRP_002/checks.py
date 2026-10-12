from test_suite.services.aux_services.message_services import (
    extract_all_contents_from_message_body,
)
from test_suite.services.aux_services.xml_services import extract_location_from_text


def verify_location_and_dereferencing(http_lost_request, dereferenced_geolocation_data):
    # Validate input data
    if not dereferenced_geolocation_data:
        return "NOT RUN -> geolocation coordinates were not found in XML source for location dereferencing"

    if not http_lost_request:
        return "FAILED -> HTTP LoST request from ESRP not found."

    http_lost_request_body = extract_all_contents_from_message_body(http_lost_request)[
        0
    ].get("body", None)

    if not http_lost_request_body:
        return "FAILED -> HTTP LoST request from ESRP has missing XML message body"

    http_lost_geolocation_data = extract_location_from_text(http_lost_request_body)

    if not http_lost_geolocation_data:
        return "FAILED -> geolocation coordinates were not found in the HTTP LoST XML message body"

    dereferenced_geolocation_data = (
        dereferenced_geolocation_data.replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
        .strip()
    )
    http_lost_geolocation_data = (
        http_lost_geolocation_data.replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
        .strip()
    )

    if dereferenced_geolocation_data != http_lost_geolocation_data:
        return (
            f"FAILED -> geolocation coordinates in HTTP LoST request to ECRF-LVF '{http_lost_geolocation_data}' "
            f"do not match the ones received/dereferenced '{dereferenced_geolocation_data}'"
        )

    return "PASSED"
