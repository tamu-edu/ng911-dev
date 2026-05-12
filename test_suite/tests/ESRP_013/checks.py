def validate_esrp_multiple_additional_data(
    stimulus_request,
    init_adr_reference,
    esrp_to_ts_adr,
    esrp_to_ts_adr2,
    esrp_to_ts_adr3,
    esrp_to_chfe_adr_reference,
):
    """
    Validate that the ESRP correctly accommodates multiple additional data services and
    structures for the same call.

    Checks that:
    - A stimulus SIP INVITE was received from the BCF.
    - The initial ADR reference (Call-Info with purpose=EmergencyCallData.ProviderInfo) is
      present in the stimulus message.
    - The ESRP sends HTTP GET requests to the Test Systems: Policy Store, ADR, ADR-2, and ADR-3.
    - The ESRP forwards the ADR reference unchanged in the outgoing SIP INVITE to the CHFE.

    :param stimulus_request: The incoming SIP INVITE from the Test System BCF to the ESRP
    :param init_adr_reference: ADR reference extracted from the stimulus SIP INVITE Call-Info header
    :param esrp_to_ts_adr: HTTP GET request sent by ESRP to Test System ADR
    :param esrp_to_ts_adr2: HTTP GET request sent by ESRP to Test System ADR-2
    :param esrp_to_ts_adr3: HTTP GET request sent by ESRP to Test System ADR-3
    :param esrp_to_chfe_adr_reference: ADR reference extracted from the ESRP SIP INVITE to CHFE
    :return: "PASSED" if all assertions pass, otherwise the assertion error message
    """
    try:
        assert stimulus_request, "NOT RUN -> stimulus request not found."
        assert (
            init_adr_reference
        ), "NOT RUN -> initial ADR reference from stimulus message not found."
        assert (
            esrp_to_ts_adr
        ), "FAILED -> ESRP should send HTTP GET request to Test Testem ADR."
        assert (
            esrp_to_ts_adr2
        ), "FAILED -> ESRP should send HTTP GET request to Test Testem ADR-2."
        assert (
            esrp_to_ts_adr3
        ), "FAILED -> ESRP should send HTTP GET request to Test Testem ADR-3."
        assert (
            esrp_to_chfe_adr_reference
        ), "FAILED -> ESRP should send HTTP GET request to Test Testem ADR-3."
        assert init_adr_reference == esrp_to_chfe_adr_reference, (
            "FAILED -> ESRP should send unchanged ADR reference "
            "the same as received from Test System BCF."
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)
