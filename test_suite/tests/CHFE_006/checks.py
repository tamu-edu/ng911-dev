def validate_sip_notify_ok_responses_from_chfe(esrp_notify_msgs, chfe_ok_msgs):
    # TODO write method
    chfe_ok_filtered = [message for message in chfe_ok_msgs if 'NOTIFY' in message.sip.cseq]

    matches = 0
    if len(esrp_notify_msgs) > len(chfe_ok_filtered):
        return False
    for message in esrp_notify_msgs:
        message_timestamp = message.sniff_timestamp
        for ok_message in chfe_ok_filtered:
            if message_timestamp < ok_message.sniff_timestamp:
                chfe_ok_filtered.remove(ok_message)
                matches += 1
                break

    if matches == len(esrp_notify_msgs):
        return True
    else:
        return False


# Variation 1 check
def verify_routing_via_conference_aware(osp_invite_request, chfe_invite_response_code,
                                        esrp_initial_conference_id, chfe_subscribe_request, chfe_conference_id,
                                        chfe_refer_request, chfe_request_uri_refer, chfe_refer_to, sip_bye,
                                        esrp_notify_msgs, chfe_ok_msgs, media_transfer_esrp_to_t_chfe,
                                        media_transfer_esrp_bcf, media_transfer_osp_bcf,
                                        bcf_osp_media_type, esrp_to_bcf_media_type,
                                        media_attr_response_t_chfe, esrp_to_t_chfe_payload_type,
                                        esrp_to_bcf_payload_type, osp_to_bcf_payload_type, bridge_call):

    if not osp_invite_request:
        return "STOP EXECUTION"  # TODO update this part when test termination feature added

    try:
        assert chfe_invite_response_code, "FAILED -> response code from CHFE found."
        if chfe_invite_response_code == 486:
            return "INCONCLUSIVE -> CHFE is busy"
        if chfe_invite_response_code == 404:
            return "INCONCLUSIVE -> Test service not supported"

        assert chfe_invite_response_code == '200', "FAILED -> No 200 OK response code from CHFE found."

        assert chfe_subscribe_request, "FAILED -> CHFE SUBSCRIBE request not found."

        assert esrp_initial_conference_id, "FAILED -> Conference_id from ESRP not found."

        assert chfe_conference_id, "FAILED -> Conference_id from CHFE SUBSCRIBE request not found."

        assert esrp_initial_conference_id == chfe_conference_id, \
            ("FAILED -> 'Conference_id' in SUBSCRIBE request URI from CHFE doesn't match to initial Conference_id from "
             "ESRP's 'Contact' header field.")

        assert chfe_refer_request, "FAILED -> CHFE REFER request not found."

        assert chfe_request_uri_refer, "FAILED -> CHFE 'Request URI' attribute from REFER request not found."

        assert esrp_initial_conference_id in chfe_request_uri_refer, \
            "FAILED -> 'Conference_id' not in CHFE Request URI."

        assert chfe_refer_to, "FAILED -> Request 'Refer-to' attribute from REFER request not found."

        assert sum(len(lst) for lst in media_transfer_esrp_to_t_chfe) > 2, \
            "FAILED -> No media data exchange between ESRP and TS-CHFE."

        assert sum(len(lst) for lst in media_transfer_esrp_bcf) > 2, \
            "FAILED -> No media data exchange between ESRP and BCF."

        assert sum(len(lst) for lst in media_transfer_osp_bcf) > 2, \
            "FAILED -> No media data exchange between OSP and BCF."

        assert any(item in esrp_to_t_chfe_payload_type for item in media_attr_response_t_chfe), \
            "FAILED -> Media payload types doesn't match between ESRP and TS-CHFE."

        assert any(item in esrp_to_bcf_payload_type for item in esrp_to_bcf_media_type), \
            "FAILED -> Media payload types doesn't match between ESRP and BCF."

        assert any(item in osp_to_bcf_payload_type for item in bcf_osp_media_type), \
            "FAILED -> Media payload types doesn't match between OSP and BCF."

        assert sip_bye, "FAILED -> CHFE BYE request not found."

        assert not bridge_call, "FAILED -> CHFE shouldn't send any requests to the BRIDGE."

        assert validate_sip_notify_ok_responses_from_chfe(esrp_notify_msgs, chfe_ok_msgs), \
            "FAILED -> Cannot find CHFE OK response message for SIP NOTIFY."

        return "PASSED"
    except AssertionError as e:
        return str(e)


# Variation 2/3 check
def verify_routing_w_or_wo_b2bua(osp_invite_request, osp_call_id, osp_to, osp_from, init_sip_chfe_response,
                                 chfe_invite_response_code, chfe_invite_request_ts, conf_response,
                                 esrp_conference_id_init, chfe_invite_request_bridge, chfe_conference_id_bridge,
                                 chfe_subscribe_request, chfe_conference_id_subscribe, chfe_refer_request,
                                 chfe_bye_after_refer, chfe_request_uri, chfe_refer_to, chfe_call_id, chfe_to_tag,
                                 chfe_from_tag, chfe_sip_refer_2, chfe_cof_id_refer2, sip_bye, esrp_notify_msgs,
                                 chfe_ok_msgs, media_transfer_data, media_attr_request_from_chfe_dict, payload_type):
    if not osp_invite_request:
        return "STOP EXECUTION"  # TODO update this part when test termination feature added

    try:
        assert init_sip_chfe_response, "FAILED -> No CHFE response found for SIP INVITE."
        
        assert chfe_invite_response_code, "FAILED -> Response code from CHFE found."
        if chfe_invite_response_code == 486:
            return "INCONCLUSIVE -> CHFE is busy"
        if chfe_invite_response_code == 404:
            return "INCONCLUSIVE -> Test service not supported"

        assert chfe_invite_response_code == 200, "FAILED -> No 200 OK response code from CHFE found."

        assert chfe_invite_request_ts, "FAILED -> No CHFE INVITE to Test Conference App found."

        assert conf_response, "INCONCLUSIVE -> Test Conference App doesn't respond to CHFE."

        assert esrp_conference_id_init, "INCONCLUSIVE -> 'Conference_Id' not found."

        assert chfe_invite_request_bridge, "FAILED -> CHFE INVITE request to BRIDGE not found."

        assert chfe_conference_id_bridge, "FAILED -> 'Conference_Id' not found in SIP INVITE from CHFE to BRIDGE."

        assert chfe_conference_id_bridge == esrp_conference_id_init, \
            ("FAILED -> 'Conference_Id' from CHFE doesn't match initial 'Conference_id'"
             "from the Test System Conference App.")

        assert chfe_subscribe_request, "FAILED -> CHFE SUBSCRIBE request not found."

        assert chfe_conference_id_subscribe, "FAILED -> 'Conference_Id' not found in SIP SUBSCRIBE from CHFE to BRIDGE."

        assert chfe_conference_id_subscribe == esrp_conference_id_init, \
            ("FAILED -> 'Conference_Id' from CHFE doesn't match initial 'Conference_id' "
             "from the Test System Conference App.")

        assert chfe_refer_request, "FAILED -> SIP REFER request from the CHFE not found."

        attributes = {
            "osp_call_id": osp_call_id,
            "osp_to": osp_to,
            "osp_from": osp_from,
            "chfe_refer_to": chfe_refer_to,
            "chfe_call_id": chfe_call_id,
            "chfe_to_tag": chfe_to_tag,
        }

        for name, value in attributes.items():
            assert value, f"FAILED -> No {name} not found"

        assert chfe_call_id == osp_call_id, \
            "FAILED -> 'Call_id' in CHFE REFER doesn't match to value from initial Test System OSP call"

        assert chfe_to_tag in osp_to, \
            "FAILED -> 'TO' from CHFE doesn't match to 'To:' header field in initial Test System OSP call"

        assert chfe_from_tag in osp_from, \
            "FAILED -> 'FROM' from CHFE doesn't match to 'From:' header field in initial Test System OSP call"

        assert chfe_request_uri == esrp_conference_id_init, \
            "FAILED -> CHFE REFER Request-URI doesn't match Conference ID"

        assert chfe_bye_after_refer, "FAILED -> SIP BYE from CHFE after SIP REFER is not found."

        assert chfe_sip_refer_2, "FAILED -> Second SIP REFER request from the CHFE not found."

        assert chfe_cof_id_refer2, "FAILED -> 'Conference_Id' in 2nd SIP REFER from CHFE is not found."

        assert chfe_cof_id_refer2 == esrp_conference_id_init, \
            ("FAILED -> 'Conference_Id' from CHFE doesn't match initial 'Conference_id'"
             "from the Test System Conference App.")

        assert sip_bye, "FAILED -> SIP BYE (call end) from CHFE is not found."

        assert validate_sip_notify_ok_responses_from_chfe(esrp_notify_msgs, chfe_ok_msgs), \
            "FAILED -> Cannot find CHFE OK response message for SIP NOTIFY."

        assert sum(len(lst) for lst in media_transfer_data) > 2, \
            "FAILED -> No media data exchange found."

        assert any(item in media_attr_request_from_chfe_dict for item in payload_type), \
            "FAILED -> Media payload types doesn't match between ESRP and BCF."

        return "PASSED"
    except AssertionError as e:
        return str(e)
