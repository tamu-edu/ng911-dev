import re
from collections import defaultdict

import bcp47

from checks.sip.call_info_header_field_checks.constants import FQDN_PATTERN
from services.aux_services.message_services import get_header_field_value, strip_ansi
from services.aux_services.sip_services import extract_raw_sip_message_string

CODECS = ['PCMU', 'PCMA', 'H264', 'T140']


def clean_up_string(str_line: str) -> str:
    """
    Removes unnecessary codding symbols from sting
    """
    for element in ['\\r', '\\n', '>', '<']:
        str_line = str_line.replace(element, '')
    return str_line


def validate_ip_with_lr(ip_string: str) -> bool:
    """
    Validates IP address string with these rules:
    - May include SIP-style prefix (e.g., <sip:...)
    - Must include 'lr' either in the IP part or as a parameter (e.g., ;lr)
    - May include port (e.g., :5060)
    """
    ip_string = ip_string.strip('<>')

    if ip_string.startswith('sip:') or ip_string.startswith('sips:'):
        ip_string = ip_string[4:]

    if 'lr' not in ip_string:
        return False

    ip_match = re.match(r'^([0-9a-zA-Z\.\-]+)(?::\d+)?(?:;.*)?$', ip_string)
    if not ip_match:
        return False

    return True


def get_p_asserted_identities(raw_message_body_string: str) -> list:
    result = []
    """
    Extracts value of header field from raw message
    :param header_name: Name of header field
    :param raw_message_body_string: raw string body
    :return: Value of header field or None
    """
    header_name = 'P-Asserted-Identity'
    for line in extract_raw_sip_message_string(raw_message_body_string).splitlines():
        if line.lower().startswith(header_name.lower() + ":"):
            pai = line.split(":", 1)[1].strip()
            if pai not in result:
                result.append(pai)
    return result


def is_valid_tel_number(tel: str) -> bool:
    """
    Validates telephone number format
    """
    return bool(re.match(r'^\+?\d{10,15}$', tel))


def is_valid_tel_uri(uri: str) -> bool:
    """
    Validates telephone number format.
    Accepts:
      - Raw numbers like '1234567890' or '+5511912345678'
      - Tel URIs like 'tel:1234567890' or 'tel:+5511912345678'
    """
    # Strip optional 'tel:' prefix
    if uri.startswith("tel:"):
        uri = uri[4:]

    # Validate optional '+' followed by 10 to 15 digits
    return bool(re.fullmatch(r'\+?\d{10,15}', uri))


def is_valid_sip_uri(uri: str) -> bool:
    """
    Validates SIP URI format, supporting domain names or IP addresses with optional port numbers.
    """
    pattern = re.compile(
        r'^sips?:'  # SIP scheme # before r'^sip:'
        r'[a-zA-Z0-9_.+-]+'  # username
        r'@'  # @ symbol
        r'('
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain (e.g. example.com)
        r'|'  # or
        r'(\d{1,3}\.){3}\d{1,3}'  # IPv4 address (e.g. 192.168.64.11)
        r')'
        r'(:(\d{1,5}))?'  # optional port (e.g. :5060)
        r'$'
    )
    return bool(pattern.match(uri))


def extract_media_attributes(message) -> dict:
    """
    Extracts media attributes from raw SIP message
    Example:
        a=rtpmap:0 PCMA/8000
        a=hlang-send:es eu en
        a=hlang-recv:es eu en
    """
    # Pattern to match Media Attribute (a): key or Media Attribute Fieldname
    result = defaultdict(list)
    # Split message into lines
    if not hasattr(message, 'raw_sip'):
        message_data = str(message.sip)
    else:
        message_data = str(message.raw_sip)

    for line in strip_ansi(message_data).splitlines():
        line = "".join(line.strip())
        if line.startswith(('m=', 'a=')):
            # Remove prefix
            prefix = line[:2]
            content = line[2:]
            # Use ':' as delimiter if available
            if ':' in content:
                key, value = content.split(':', 1)
                codec = clean_up_string(value).split(' ')[-1].split('/')[0]
                result[key].append(codec)
    return result


def get_content_type_data(message) -> list:
    """
    Extracts Content-Type for message and stores all data into list
    """
    result = []

    if hasattr(message, "raw_sip"):
        raw_sip = message.raw_sip
        for line in str(raw_sip).splitlines():
            if "Content-Type" in line:
                record = "".join(line.strip()).split(" ")[1]
                if record not in result:
                    result.append(record)
    elif hasattr(message, "sip"):
        sip = message.sip
        for line in str(sip).splitlines():
            if "Content-Type" in line:
                record = "".join(line.strip()).split(" ")[1]
                if record not in result:
                    result.append(record)
    return result


# Variation 1 validations
def validate_che_sip_invite_for_callback(sip_invtie_to_che, che_response, ):
    """
    Method to validate SIP INVITE sent by CHE for callbacks
    """
    # Extract From and P-Asserted-Identity from initial SIP INVITE
    initial_from = get_header_field_value(sip_invtie_to_che, 'From')
    initial_pai = get_header_field_value(sip_invtie_to_che, 'P-Asserted-Identity', )

    # Validate From header format
    from_hdr = get_header_field_value(che_response, 'From', )
    if not from_hdr:
        return "FAILED ->Missing 'From' header"
    else:
        match = re.match(r'\b(sips?):(\+?\d{10,15})@([a-zA-Z0-9.-]+)(;user=phone)[\r\n>]*', from_hdr)
        if not match:
            return "FAILED -> 'From' header does not match required format"
        else:
            _, tel_number, che_fqdn, _ = match.groups()
            if not is_valid_tel_number(tel_number):
                return "FAILED ->Telephone number in 'From' is not a valid NANP or E.164 number"
            if not re.search(FQDN_PATTERN, che_fqdn):
                return "FAILED ->CHE FQDN in 'From' is not a valid domain"

    # Validate Request-URI
    request_uri_match = re.match(
        r'^INVITE (sips?):([^@]+)@([a-zA-Z0-9.-]+|'
        r'\d{1,3}(?:\.\d{1,3}){3})(?::\d+)? SIP/2\.0\s*$',
        che_response.sip.request_line
    )
    try:
        request_uri = request_uri_match.group().split(" ")[1]
    except IndexError:
        return "FAILED -> Cannot extract Request-URI from INVITE"

    if request_uri not in (initial_from or '') and request_uri not in (initial_pai or ''):
        return "FAILED -> Request-URI does not match initial From or P-Asserted-Identity"

    # Validate 'To' header
    to_hdr = get_header_field_value(che_response, 'To')
    if to_hdr and not any(val == to_hdr for val in [initial_from, initial_pai]):
        return "FAILED ->'To' header does not match initial 'From' or 'P-Asserted-Identity'"

    # Validate 'Priority'
    if clean_up_string("".join(get_header_field_value(che_response, 'Priority').strip())) != 'psap-callback':
        return "FAILED -> 'Priority' header field must be 'psap-callback'"

    # Validate 'Resource-Priority'
    if 'esnet.0' not in get_header_field_value(che_response, 'Resource-Priority'):
        return "FAILED -> 'Resource-Priority' header must be 'esnet.0'"

    # Validate P-Asserted-Identity matches From
    pai_hdr = get_header_field_value(che_response, 'P-Asserted-Identity')
    if pai_hdr != from_hdr:
        return "FAILED -> 'P-Asserted-Identity' does not match 'From' header"

    return "PASSED"


# Variation 2 validations
def validate_che_sip_invite_for_outbound_calls(che_response):
    """
    Method to validate SIP INVITE sent by CHE for outbound calls
    """
    # Validate Request-URI
    request_uri_match = re.match(
        r'^INVITE\s+'
        r'(sip:[^ ]+|'
        r'sips:[^ ]+|'
        r'tel:[^ ]+|'
        r'sip:\d{1,3}(.\d{1,3}){3}|'
        r'sips:\d{1,3}(.\d{1,3}){3}|'
        r'tel:\d{1,3}(.\d{1,3}){3})',
        che_response.sip.request_line
    )
    if request_uri_match:
        uri = request_uri_match.group(1)
        if not (is_valid_tel_uri(uri) or is_valid_sip_uri(uri)):
            return "FAILED -> Request-URI must be a valid tel: or sip: URI"
    else:
        return "FAILED -> Cannot extract 'Request-URI' from INVITE"

    # Validate 'To' header
    to_hdr = clean_up_string(get_header_field_value(che_response, 'To'))
    if not to_hdr:
        return "FAILED -> Missing 'To' header"
    else:
        uri_match = re.search(r'(sip:[^;>]+|tel:[^;>]+)', to_hdr)
        if not uri_match or not (is_valid_tel_uri(uri_match.group(1)) or is_valid_sip_uri(uri_match.group(1))):
            return "FAILED -> 'To' header must contain a valid tel: or sip: URI"

    # Validate 'From' header
    from_hdr = clean_up_string(get_header_field_value(che_response, 'From'))
    if not from_hdr:
        return "FAILED -> Missing 'From' header"
    else:
        anon_pattern = r'^sip:anonymous@anonymous\.invalid'
        phone_pattern = r'^sip:(\+?\d{10,15})@([a-zA-Z0-9.-]+);user=phone$'
        if not re.match(anon_pattern, from_hdr) and not re.match(phone_pattern, from_hdr):
            return ("FAILED -> 'From' header must be either 'sip:anonymous@anonymous.invalid' "
                    "or 'sip:TEL@FQDN;user=phone'")
        elif re.match(phone_pattern, from_hdr):
            tel, fqdn = re.match(phone_pattern, from_hdr).groups()
            if not is_valid_tel_number(tel):
                return "FAILED -> Telephone number in 'From' is invalid"
            if not re.search(FQDN_PATTERN, fqdn):
                return "FAILED -> CHE FQDN in 'From' is not valid FQDN"

    # Validate 'Resource-Priority'
    rpri = clean_up_string(get_header_field_value(che_response, 'Resource-Priority'))
    if rpri not in ['esnet.0', 'esnet.1', 'esnet.2']:
        return "FAILED -> 'Resource-Priority' must be one of: esnet.0, esnet.1, esnet.2"

    # Validate 'P-Asserted-Identity'
    pai_hdr = clean_up_string(get_header_field_value(che_response, 'P-Asserted-Identity'))
    if not pai_hdr:
        return "FAILED -> Missing 'P-Asserted-Identity'"
    else:
        match = re.match(r'^sip:(\+?\d{10,15})@([a-zA-Z0-9.-]+);user=phone$', pai_hdr)
        if not match:
            return "FAILED -> 'P-Asserted-Identity' must be in format 'sip:TEL@FQDN;user=phone'"
        else:
            tel, fqdn = match.groups()
            if not is_valid_tel_number(tel):
                return "FAILED -> Telephone number in 'P-Asserted-Identity' is invalid"
            if not re.search(FQDN_PATTERN, fqdn):
                return "FAILED -> CHE FQDN in 'P-Asserted-Identity' is not valid FQDN"

    # Validate 'Privacy' only when From is anonymous
    if 'sip:anonymous@anonymous.invalid' in from_hdr:
        privacy = clean_up_string(get_header_field_value(che_response, 'Privacy'))
        if privacy != 'user':
            return "FAILED -> 'Privacy' header must be 'user' when 'From' is 'sip:anonymous@anonymous.invalid'"
    return "PASSED"


# Common validation for both variations and specific check for each variation
def validate_che_callbacks_and_outbound(sip_invite_to_che, che_response, variation_method):
    """
    Method that parses incoming test data: SIP initial INVITE,
                                           CHE INVITE response,
                                           Variation method
    """
    if not che_response:
        return "FAILED -> CHE response not found"

    # Check 'Content-Type'
    content_type_list = get_content_type_data(che_response)
    for content_type in content_type_list:
        if 'application/sdp' not in clean_up_string(content_type):
            return "FAILED -> 'Content-Type' must be 'application/sdp'"

    # Check 'Via'
    via = clean_up_string(get_header_field_value(che_response, 'Via'))
    if not via:
        return "FAILED -> Missing 'Via' header"
    else:
        if not re.match(r'^SIP/2.0/(UDP|TCP|TLS|SCTP) ([\w.-]+):\d+(;.*)?$', via):
            return f"FAILED -> Invalid 'Via' header format: {via}"

    # Check 'Contact'
    contact = clean_up_string(get_header_field_value(che_response, 'Contact'))
    if not contact or not re.search(r'\b(?:sip|sips|tel):[^@<>\s]+@[^;:<>\s]+(?::\d+)?(?:;[^<>\s]*)?', contact):
        return "FAILED ->Invalid or missing Contact header"

    # Check 'Cseq'
    cseq = clean_up_string(get_header_field_value(che_response, 'Cseq'))
    if not cseq or not re.match(r'^\d+ INVITE$', cseq):
        return "FAILED -> 'CSeq' must be in format '<number> INVITE'"

    # Check 'Call-ID'
    call_id = clean_up_string(get_header_field_value(che_response, 'Call-ID'))
    # TODO: Potential place where "INCONCLUSIVE" result may be applied since there might be a problem with regex
    if not call_id or not re.match(r"[a-zA-Z0-9\-_.!%*+`'~]+(?:@[a-zA-Z0-9\-._]+)?", call_id):
        return "FAILED -> 'Call-ID' is missing or invalid format"

    # Check 'Content-Length'
    content_length = clean_up_string(get_header_field_value(che_response, 'Content-Length'))
    if not content_length or not content_length.isdigit():
        return "FAILED -> 'Content-Length' is missing or not an integer"

    # Check 'Route'
    route_hdr = clean_up_string(get_header_field_value(che_response, 'Route'))
    if not route_hdr:
        return "FAILED -> Missing 'Route' header field"
    route_hdr_split = route_hdr.split(";")
    if len(route_hdr_split) < 2 or route_hdr_split[1] != 'lr':
        return "FAILED -> Invalid 'Route' header field (should contain 'lr')"
    else:
        if not re.search(FQDN_PATTERN, route_hdr) or not validate_ip_with_lr(route_hdr):
            return "FAILED -> 'Route' host has not valid FQDN or IP"

    # Check second P-Asserted-Identity (e.g., agent identity)
    pai_list = get_p_asserted_identities(che_response)
    if len(pai_list) < 2:
        return "FAILED -> Second P-Asserted-Identity (agent identity) is missing"
    else:
        second_pai = pai_list[1]
        if not re.match(r'^sip:[^@]+@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$', clean_up_string(second_pai)):
            return "FAILED -> Second P-Asserted-Identity must be a valid SIP URI with domain"

    # Check SDP body
    sdp = extract_media_attributes(che_response)

    if not sdp:
        return "FAILED ->Missing SDP body in INVITE"
    else:
        # Required media
        rtpmap = sdp.get('rtpmap', None)
        if not rtpmap or not any(codec in rtpmap for codec in CODECS):
            return "FAILED -> Missing required media codecs in SDP"

        # Required language tags
        for hlang in ['hlang-send', 'hlang-recv']:
            hlang_sdp = sdp.get(hlang, None)
            if not hlang_sdp or not all([lang in bcp47.tags for lang in hlang_sdp.split(" ")]):
                return f"FAILED -> Required BCP 47 conformant language tags not found in '{hlang}'"

    # Specific checks for each variation
    if variation_method == 'send':
        if not sip_invite_to_che:
            return "FAILED -> SIP INVITE to CHE not found"
        if (result := validate_che_sip_invite_for_callback(sip_invite_to_che, che_response)) != 'PASSED':
            return result

    else:
        if (result := validate_che_sip_invite_for_outbound_calls(che_response)) != 'PASSED':
            return result

    return "PASSED"
