def validate_esrp_retrieving_additional_data(emergency_call_data_list, bcf_invite_request,
                                            esrp_get_policies_request, is_jws_in_response_valid, esrp_get_adr_request,
                                            esrp_emergency_call_data_list):

    try:
        # TODO NOT IMPLEMENTED
        # assert emergency_call_data_list, \
        #     "STOP_EXECUTION -> Stimulus message from OSP to BCF has mot been found."
        #
        # assert bcf_invite_request, \
        #     "STOP_EXECUTION -> Request method from BCF to ESRP has not been found."

        if esrp_get_policies_request:
            assert is_jws_in_response_valid, \
                "INCONCLUSIVE -> JWS from PS has not been found."

        assert esrp_get_adr_request, \
            "FAILED -> ESRP request to ADR has not been found."

        assert esrp_emergency_call_data_list, \
            "FAILED -> Cannot found 'EmergencyCallData' sent from ESRP to TS-CHFE."

        emergency_call_data_set = set(emergency_call_data_list)
        esrp_emergency_call_data_set = set(esrp_emergency_call_data_list)

        missing = emergency_call_data_set - esrp_emergency_call_data_set
        assert not missing, \
            ("FAILED -> detected differences between SIP INVITE sent to ESRP"
             "and from ESRP to TS-CHFE in EmergencyCallData related header fields.")

        additional = esrp_emergency_call_data_set - emergency_call_data_set
        assert not additional, \
            ("FAILED -> detected additional header fields related with EmergencyCallData"
             "in SIP INVITE sent by ESRP to TS-CHFE.")

        return "PASSED"

    except AssertionError as e:
        return str(e)
