def validate_bridge_multi_party_session(
    che_to_bridge_invite_sent,
    bridge_to_chfe_rtpmap,
    bridge_to_chfe_mixer,
    che_to_bridge_communication_successful,
    bridge_to_bcf_rtpmap,
    bridge_to_bcf_mixer,
    bridge_to_chfe_message_text,
    chfe_message,
    bridge_to_bcf_invite_successful,
    bcf_to_osp_message_text,
    osp_message,
    bcf_ssrc,
    bridge_ssrc,
    chfe_ssrc,
    bcf_to_osp_ssrc,
    bridge_to_chfe_ssrc,
    bridge_to_chfe_csrc,
    bridge_to_bcf_csrc,
    bcf_to_osp_csrc,
    bridge_to_chfe_invite_response,
):
    try:
        rtpmap_str = "98 t140/1000"
        mixer_str = "rtt-mixer"

        assert che_to_bridge_invite_sent, "FAILED -> CHFE to BRIDGE INVITE not found."

        assert (
            bridge_to_chfe_invite_response
        ), "FAILED -> BRIDGE to CHFE INVITE 200 OK was not received."

        assert (
            bridge_to_chfe_rtpmap == rtpmap_str
        ), f"FAILED -> Unexpected BRIDGE to CHFE rtpmap value. Actual: {bridge_to_chfe_rtpmap}, Expected: {rtpmap_str}"

        assert (
            bridge_to_chfe_mixer
        ), f"FAILED -> '{mixer_str}' was not found in BRIDGE to CHFE INVITE 200 SDP"

        assert (
            che_to_bridge_communication_successful
        ), "FAILED -> Cannot find 200 OK SIP with media information from BRIDGE to CHFE."

        assert (
            bridge_to_bcf_rtpmap == rtpmap_str
        ), f"FAILED -> Unexpected BRIDGE to BCF rtpmap value. Actual: {bridge_to_chfe_rtpmap}, Expected: {rtpmap_str}"

        assert (
            not bridge_to_bcf_mixer
        ), f"FAILED -> '{mixer_str}' was found in BRIDGE to BCF INVITE SDP"

        assert (
            bridge_to_bcf_invite_successful
        ), "FAILED -> Cannot find SIP Invite from BRIDGE to BCF with t.140 information"

        assert (
            bridge_to_chfe_message_text == osp_message
        ), f"FAILED -> Message from OSP to BRIDGE and from BRIDGE to CHFE doesn't match. Actual: '{bridge_to_chfe_message_text}', Expected: '{osp_message}'"

        assert (
            bcf_to_osp_message_text == chfe_message
        ), f"FAILED -> Message from CHFE to BRIDGE and from BCF to OSP doesn't match. Actual: '{bcf_to_osp_message_text}', Expected: '{chfe_message}'"

        assert (
            len(bcf_to_osp_ssrc) == 1
        ), f"FAILED -> Number of SSRC in BCF to OSP is not equal to 1. Actual: {bcf_to_osp_ssrc} = {len(bcf_to_osp_ssrc)}"

        assert bcf_to_osp_ssrc not in (
            bridge_ssrc,
            chfe_ssrc,
        ), f"FAILED -> SSRC in BCF to OSP does not belong to BCF. Actual: {bcf_to_osp_ssrc}, Not Expected: {bridge_ssrc, chfe_ssrc}"

        assert (
            len(bridge_to_chfe_ssrc) == 1
        ), f"FAILED -> Number of SSRC in BRIDGE to CHFE is not equal to 1. Actual: {bridge_to_chfe_ssrc} = {len(bridge_to_chfe_ssrc)}"

        assert (
            bridge_to_chfe_ssrc == bridge_ssrc
        ), f"FAILED -> BRIDGE SSRC in BRIDGE to CHFE doesn't match. Actual: {bridge_to_chfe_ssrc}, Expected: {bridge_ssrc}"

        assert (
            len(bridge_to_chfe_csrc) == 2
        ), f"FAILED -> BRIDGE to CHFE CSRC list is not equal to 2. Actual:{bridge_to_chfe_csrc} = {len(bridge_to_chfe_csrc)}"

        assert bool(
            bcf_ssrc & bridge_to_chfe_csrc
        ), f"FAILED -> BCF SSRC {bcf_ssrc} not in BRIDGE to CHFE CSRC list. Actual:{bridge_to_chfe_csrc}"

        assert bool(
            chfe_ssrc & bridge_to_chfe_csrc
        ), f"FAILED -> CHFE SSRC {chfe_ssrc} not in BRIDGE to CHFE CSRC list. Actual: {bridge_to_chfe_csrc}"

        assert (
            not bridge_to_bcf_csrc
        ), f"FAILED -> Found BRIDGE to BCF CSRC IDs values. Actual: {bridge_to_bcf_csrc}. Expected: No IDs values"

        assert (
            not bcf_to_osp_csrc
        ), f"FAILED -> Found BCF to OSP CSRC IDs values. Actual: {bcf_to_osp_csrc}. Expected: No IDs values"

        return "PASSED"

    except AssertionError as e:
        return str(e)
