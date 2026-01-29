from checks.http.checks import is_type
from services.aux_services.aux_services import is_valid_timestamp


def validate_support_of_discrepancy_report(sip_invite_str, out_message_json, emergency_call_info_header):

    try:
        assert out_message_json, \
            "INCONCLUSIVE -> No Discrepancy Report JSON from ESRP has been found."

        response_comments = out_message_json.get('request', None)
        assert response_comments == sip_invite_str, \
            "INCONCLUSIVE -> 'request' doesn't match to original SIP invite message."

        sos_source = out_message_json.get('sosSource', None)
        assert sos_source.lower() == emergency_call_info_header.lower(), \
            "INCONCLUSIVE -> Wrong 'sos_source' data doesn't match to SIP INVITE"

        problem = out_message_json.get('problem', None)
        assert problem.lower() == 'BasSIP'.lower(), \
            "INCONCLUSIVE -> Wrong 'problem' data in ESRP response"

        event_timestamp = out_message_json.get('eventTimestamp', None)
        if event_timestamp:
            assert is_valid_timestamp(event_timestamp), \
                "INCONCLUSIVE -> Invalid datetime format for 'eventTimestamp'."

        packet_header = out_message_json.get('packetHeader', None)
        if packet_header:
            assert (result := is_type(packet_header, 'packetHeader', str)) == 'PASSED', \
                f"INCONCLUSIVE -> {result}"

        return "PASSED"

    except AssertionError as e:
        return str(e)
