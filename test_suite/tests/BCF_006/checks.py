from services.aux_services.sip_msg_body_services import clean_up_string

from test_suite.services.aux_services.message_services import get_header_field_value


def validate_ack_fields(
    bcf_invite_messages,
    bcf_ack_messages,
    stimulus_src_ip,
    stimulus_dst_ip,
    bcf_invite_to,
    bcf_invite_call_id,
    bcf_invite_contacts,
    fqdn_dict,
):
    try:
        assert (
            bcf_invite_messages
        ), "FAILED -> No SIP INVITE messages from BCF to ESRP found."
        assert bcf_ack_messages, "FAILED -> No ACK messages from BCF to ESRP found."

        for msg in bcf_ack_messages:
            ack_via = (
                clean_up_string(msg.sip.get("via")) if hasattr(msg.sip, "via") else ""
            )
            assert (
                fqdn_dict.get("IF_BCF_ESRP") in ack_via or stimulus_dst_ip in ack_via
            ), "FAILED -> ACK message should contain ESRP address/fqdn."
            ack_from = (
                clean_up_string(msg.sip.get("from")) if hasattr(msg.sip, "from") else ""
            )
            assert (
                fqdn_dict.get("IF_OSP_BCF") in ack_from or stimulus_src_ip in ack_from
            ), "FAILED -> ACK message should contain TS OSP address/fqdn."
            ack_to = (
                clean_up_string(msg.sip.get("to")) if hasattr(msg.sip, "to") else ""
            )
            assert (
                bcf_invite_to in ack_to
            ), "FAILED -> 'To' header in ACK message doesn't match SIP INVITE 'To' header."
            ack_call_id = (
                clean_up_string(msg.sip.get("call_id"))
                if hasattr(msg.sip, "call_id")
                else ""
            )
            assert (
                bcf_invite_call_id == ack_call_id
            ), "FAILED -> 'Call-ID' should be the same in SIP INVITE and SIP ACK."
            ack_contact = (
                clean_up_string(msg.sip.get("contact"))
                if hasattr(msg.sip, "contact")
                else ""
            )
            assert (
                ack_contact in bcf_invite_contacts
            ), f"FAILED -> ACK 'Contact' '{ack_contact}' does not match any SIP INVITE 'Contact' header."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_bcf_sends_aks_for_each_invite_confirmation(
    esrp_invite_responses_messages, bcf_ack_messages
):
    try:
        assert (
            esrp_invite_responses_messages
        ), "FAILED -> No ESRP 2xx OK messages found."
        assert bcf_ack_messages, "FAILED -> No BCF ACK messages found."
        assert len(esrp_invite_responses_messages) == len(
            bcf_ack_messages
        ), "FAILED -> BCF should send ACK for each 2xx response for SIP INVITE."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_bcf_forwards_bye(osp_bye_messages, bcf_bye_messages):
    try:
        assert osp_bye_messages, "NOT RUN -> Cannot find OSP BYE messages."
        assert (
            bcf_bye_messages
        ), "FAILED -> No BCF BYE messages found. BCF should forward BYE."
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_bye_transaction_no_ack(ack_after_bye_messages, bye_call_id):
    """
    Validates that BCF completes BYE transaction without sending ACK.
    :param ack_after_bye_messages: list of ACK messages sent after BYE
    :param bye_call_id: Call-ID header field value of SIP BYE message
    terminating the transaction
    :return: 'PASSED' or 'FAILED' with error description
    """
    ack_for_bye_call_id = []
    try:
        assert bye_call_id, "FAILED -> not found SIP BYE from the BCF"
        if ack_after_bye_messages:
            ack_for_bye_call_id = [
                ack
                for ack in ack_after_bye_messages
                if get_header_field_value(ack, "Call-ID") == bye_call_id
            ]
        assert (
            not ack_for_bye_call_id
        ), f"FAILED -> found ACK for SIP BYE with Call-ID: {bye_call_id}"
        return "PASSED"
    except AssertionError as e:
        return str(e)
