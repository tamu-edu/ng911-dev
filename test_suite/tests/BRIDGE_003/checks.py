def validate_bridge_multi_party_session(
    che_to_bridge_communication_successful,
    is_csrs_present_from_bridge_to_chfe,
    bridge_to_chfe_message_text,
    chfe_message,
    is_bridge_to_osp_communications_successful,
    is_ssrc_correct,
    bridge_to_osp_message_text,
    osp_message,
):
    try:
        assert (
            che_to_bridge_communication_successful
        ), "FAILED -> Cannot find 200 OK SIP with media information from BRIDGE to CHFE."
        assert (
            not is_csrs_present_from_bridge_to_chfe
        ), "FAILED -> RTP packets sent by BRIDGE to Test System CHFE shouldn't contain any ids in CSRC."
        assert (
            bridge_to_chfe_message_text
        ), "FAILED -> Cannot find RTP packets sent by BRIDGE to CHFE."
        assert (
            bridge_to_chfe_message_text == osp_message
        ), "FAILED -> Message from OSP to BRIDGE and from BRIDGE to CHFE doesn't match."
        assert (
            is_bridge_to_osp_communications_successful
        ), "Cannot find 200 OK SIP with media information from BRIDGE to OSP."
        assert is_ssrc_correct, "FAILED -> Invalid SSRC data."
        assert (
            bridge_to_osp_message_text == chfe_message
        ), "FAILED -> Message from CHFE to BRIDGE and from BRIDGE to OSP doesn't match."

        return "PASSED"

    except AssertionError as e:
        return str(e)
