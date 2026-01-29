def is_expected_response(responses, call_id):
    result = True
    for response in responses:
        if hasattr(response.sip, 'call_id'):
            if response.sip.call_id == call_id:
                # NOTE: White-listed checks that ESRP may send as response
                # May need to be extended with additional checks
                # Candidate for INCONCLUSIVE status
                status_line = getattr(response.sip, 'status_line', None)
                cseq_method = getattr(response.sip, 'cseq_method', None)

                if cseq_method and response.sip.cseq_method == 'BYE':
                    continue
                if status_line and 'request terminated' in status_line.lower():
                    continue
                # If any of non white-listed responses found return FAILED result
                result = False
    return result


def validate_processing_data_by_esrp(exp_response_code, call_id, esrp_resp):
    if not esrp_resp:
        return "FAILED -> No response found from ESRP."

    after_timestamp = None

    # Find 200 OK response
    has_200_ok = None
    for response in esrp_resp:
        if str(getattr(response.sip, 'status_code', None)) == str(exp_response_code):
            has_200_ok = True
            after_timestamp = response.sniff_timestamp
            break

    if not has_200_ok:
        return "FAILED -> No 200 OK response from ESRP."

    # Filter out all the responses that came after 200 OK
    esrp_resp_after_ok = []
    for resp in esrp_resp:
        if resp.sniff_timestamp > after_timestamp:
            esrp_resp_after_ok.append(resp)

    # Check if responses after CANCEL are acceptable
    if not is_expected_response(esrp_resp_after_ok, call_id):
        return "FAILED -> ESRP send a call which was canceled."

    return "PASSED"
