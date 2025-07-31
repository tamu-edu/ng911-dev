from services.aux_services.sip_msg_body_services import get_message_bodies_matching_cid


def test_adding_geolocation_header_pointing_to_pidf_lo(
        stimulus_geolocation_header_cid_list: list,
        output_geolocation_header_cid_list: list,
        output_pidf_lo_body_list: list
):
    """
    Test to validate if geolocation header field is added to output message
    and contains CID to added PIDF-LO body
    :param stimulus_geolocation_header_cid_list: List of CID values from stimulus message Geolocation header fields
    :param output_geolocation_header_cid_list:  List of CID values from output message Geolocation header fields
    :param output_pidf_lo_body_list: List of message bodies (extracted by
    extract_header_field_value_from_raw_string_body) which are correct PIDF-LO
    """
    try:
        added_geolocation_cid_list = [cid for cid in output_geolocation_header_cid_list
                                      if cid not in stimulus_geolocation_header_cid_list]
        assert added_geolocation_cid_list, \
            "FAILED -> added Geolocation header fields not found in output SIP message"
        assert [cid for cid in added_geolocation_cid_list
                if get_message_bodies_matching_cid(output_pidf_lo_body_list, cid) != []], \
            "FAILED -> added Geolocation header fields CID do not point to PIDF-LO body"
        return "PASSED"
    except AssertionError as e:
        return str(e)
