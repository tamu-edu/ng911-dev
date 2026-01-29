from services.aux_services.sip_msg_body_services import is_valid_pidf_lo


def test_keeping_original_message_bodies(stimulus_message_body_list, output_message_body_list):
    """
    Test to validate if outgoing message contains original message bodies
    :param stimulus_message_body_list: List of message bodies (extracted by extract_all_contents_from_message_body)
    from stimulus SIP message
    :param output_message_body_list: List of message bodies (extracted by extract_all_contents_from_message_body)
    from output SIP message
    """
    try:
        assert [body for body in stimulus_message_body_list if body in output_message_body_list], \
            "FAILED - outgoing message does not contain all bodies from the original"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_adding_default_pidf_lo(stimulus_message_body_list: list, output_message_body_list: list):
    """
    Test to validate if default pidf_lo body has been added to message
    :param stimulus_message_body_list: list of bodies from stimulus message
    (returned by function extract_all_contents_from_message_body)
    :param output_message_body_list: list of bodies from output message
    (returned by function extract_all_contents_from_message_body)
    """
    try:
        assert output_message_body_list, "FAILED -> message bodies not found in outgoing message"
        new_message_bodies = [body for body in output_message_body_list if body not in stimulus_message_body_list]
        assert new_message_bodies, "FAILED -> not found added message bodies"
        assert any(is_valid_pidf_lo(body['body']) for body in new_message_bodies), \
            "FAILED -> correct PIDF-LO not found in added message bodies"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def test_if_xml_body_list_contains_pidf_lo_location(message_xml_body_list: list):
    """
    Test to validate if XML body in message contains correct PIDF-LO location object
    :param message_xml_body_list: XML message bodies as a list of dicts from
    function extract_all_contents_from_message_body
    """
    try:
        assert message_xml_body_list, "FAILED -> failed to find any XML body in message"
        assert any(is_valid_pidf_lo(body['body']) for body in message_xml_body_list), \
            "FAILED -> XML bodies do not contain correct PIDF-LO location object"
        return "PASSED"
    except AssertionError as e:
        return str(e)
