from services.aux_services.aux_services import is_valid_http_https_url
from services.aux_services.sip_msg_body_services import is_valid_pidf_lo


def test_geolocation_is_valid(message_data) -> str:
    """
    Validates that the Geolocation header references a valid location.

    If the value is an HTTP/HTTPS URL, it is accepted as-is.
    If it is a CID reference (e.g. '<cid:id@host>'), the matching body part is
    located by Content-ID and its content is validated as a PIDF-LO document.

    :param message_data: InviteData or MessageData instance containing the
                         geolocation header value and the parsed message body parts.
    :return: "PASSED" or a "FAILED -> ..." error string.
    """
    try:
        geolocation_value = message_data.geolocation
        assert geolocation_value, "FAILED -> Geolocation not found in message data"

        if is_valid_http_https_url(geolocation_value):
            return "PASSED"

        cid = geolocation_value.removeprefix("<cid:").removesuffix(">")

        for body in message_data.message_body or []:
            if cid in (body.get("Content-ID") or ""):
                if is_valid_pidf_lo(body.get("body", "")):
                    return "PASSED"

        return "FAILED -> Geolocation is not a valid URL and no valid PIDF-LO body found for Content-ID reference"
    except AssertionError as e:
        return str(e)


def validate_contact_header_field(contact, sip_uri, bcf_fqdn_or_ip):
    """
    Validates that the Contact header field contains the BCF FQDN or IP address.

    Extracts the host part from the SIP URI in the Contact header (the segment
    between '@' and the optional port ':') and compares it against the expected
    BCF FQDN/IP.

    :param contact: Raw value of the Contact header field (e.g. 'sip:bcf@10.0.0.1:5060').
    :param sip_uri: SIP URI associated with the contact (used for presence validation).
    :param bcf_fqdn_or_ip: Expected BCF FQDN or IP address.
    :return: "PASSED" or a "FAILED -> ..." error string.
    """
    try:
        assert contact, "FAILED -> Data for 'Contact' header field not found."

        assert sip_uri, "FAILED -> No 'SIP URI' header field data found."
        assert (
            bcf_fqdn_or_ip
        ), "FAILED -> No 'BCF FQDN/IP' data found to verify 'Contact' header field."
        contact_fqdn_or_ip = contact.split("@")[-1].split(":")[0]
        if ";" in contact_fqdn_or_ip:
            contact_fqdn_or_ip = contact_fqdn_or_ip.split(";")[0]

        assert bcf_fqdn_or_ip == contact_fqdn_or_ip, (
            f"FAILED -> 'Contact' header field doesn't contain valid FQDN.\n"
            f"Expected: {bcf_fqdn_or_ip},\n"
            f"Actual: {contact_fqdn_or_ip}"
        )

        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_sdp_media_message_body(media_data, bcf_fqdn_or_ip):
    """
    Validates that the SDP body anchors media through the BCF.

    Finds the SDP part in the multipart message body, locates the Connection
    Information line ('c='), and verifies that the connection address matches
    the expected BCF FQDN or IP address.

    :param media_data: List of body part dicts (each with 'Content-Type' and 'body' keys)
                       as returned by extract_all_contents_from_message_body().
    :param bcf_fqdn_or_ip: Expected BCF FQDN or IP address that must appear in 'c=' line.
    :return: "PASSED" or a "FAILED -> ..." error string.
    """
    try:
        assert media_data, "FAILED -> SDP media message data field not found."
        assert (
            bcf_fqdn_or_ip
        ), "FAILED -> No 'BCF FQDN/IP' data found to verify 'Contact' header field."
        sdp_parts = [p for p in media_data if "sdp" in p.get("Content-Type", "")]
        assert sdp_parts, "FAILED -> No SDP body part found in media data."

        for sdp in sdp_parts:
            lines = sdp.get("body", "").splitlines()
            assert len(lines) > 2, "FAILED -> Invalid SDP body data."

            c_lines = [line for line in lines if line.startswith("c=")]
            assert (
                c_lines
            ), "FAILED -> No 'c=' (Connection Information) line found in SDP body."

            for line in c_lines:
                parts = line.split()
                assert (
                    len(parts) == 3
                ), f"FAILED -> Malformed SDP Connection Information: '{line}'"
                connection_address = parts[2]
                assert connection_address == bcf_fqdn_or_ip, (
                    f"FAILED -> SDP media address should be FQDN/IP of BCF."
                    f"\nExpected: {bcf_fqdn_or_ip},"
                    f"\nActual: {connection_address}"
                )
        return "PASSED"
    except AssertionError as e:
        return str(e)
