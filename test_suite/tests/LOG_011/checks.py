import json

from services.aux_services.message_services import extract_json_data_from_http


def validate_incident_id_recorded(incident_id, incident_ids_response):
    """
    Validates that the LogEvent is still recorded despite the signature
    verification failure, confirmed by its incidentId being present in the
    HTTP GET /IncidentIds response.
    """
    try:
        assert (
            incident_id
        ), "NOT RUN-> No incidentId available to check against HTTP GET /IncidentIds response"

        assert (
            incident_ids_response
        ), "FAILED-> No response received for HTTP GET to /IncidentIds"
        assert (
            hasattr(incident_ids_response, "http")
            and incident_ids_response.http.response_code == "200"
        ), "FAILED-> Response code for HTTP GET to /IncidentIds is not 200"

        incident_ids_json = extract_json_data_from_http(incident_ids_response)
        assert (
            incident_ids_json
        ), "FAILED-> Cannot find JSON data in HTTP GET /IncidentIds response"

        assert incident_id in json.dumps(incident_ids_json), (
            f"FAILED-> LogEvent with incidentId '{incident_id}' was not found in HTTP "
            f"GET /IncidentIds response - LogEvent was not recorded despite signature "
            f"verification failure"
        )

        return "PASSED"
    except AssertionError as e:
        return str(e)
