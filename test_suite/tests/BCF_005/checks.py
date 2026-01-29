import base64
import json
from services.aux_services.json_services import decode_jws
from services.aux_services.aux_services import validate_ip_port_combo, is_valid_timestamp
from test_suite.services.aux_services.sip_msg_body_services import is_valid_sip_call_id
from test_suite.checks.sip.call_info_header_field_checks.checks import (
    test_emergency_call_id_urn,
    test_emergency_call_id_string_id,
    test_emergency_call_id_fqdn,
    test_incident_tracking_id_urn,
    test_incident_tracking_id_string_id,
    test_incident_tracking_id_fqdn
)


def _extract_call_id(sip_message):
    """Extract Call-ID from SIP message text"""
    for line in sip_message.split('\n'):
        if line.lower().startswith('call-id:'):
            return line.split(':', 1)[1].strip()
    return None

def _extract_sip_method(sip_message):
    """Extract SIP method from first line of message"""
    first_line = sip_message.split('\n')[0].strip()
    parts = first_line.split()
    if len(parts) > 0 and parts[0] in ['INVITE', 'MESSAGE', 'BYE', 'ACK', 'CANCEL', 'OPTIONS']:
        return parts[0]
    return None

def _normalize_sip_message(text):
    """Normalize SIP message for comparison (remove variable fields like Via, CSeq, etc.)"""
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith(('via:', 'call-id:', 'cseq:', 'contact:', 'content-length:', 'max-forwards:')):
            continue
        if not lines and not line:
            break
        lines.append(line)
    return '\n'.join(lines)

def validate_direction(http_post_requests):
    """
    Validate that for every CallSignalingMessageLogEvent, the direction is properly set.
    Also validates that for each incoming message, there's a matching outgoing message
    with the same Call-ID and SIP method, and that the message content matches.
    
    Args:
        http_post_requests: List of HTTP POST requests containing log events
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if all validations pass, False otherwise
        - error_message: None if valid, error message if invalid
    """
    if not http_post_requests:
        return False, "No HTTP POST requests found"

    messages = {
        'incoming': {},  # {call_id: {method: text}}
        'outgoing': {}   # {call_id: {method: text}}
    }
    
    for request in http_post_requests:
        http_layer = getattr(request, 'http', None)
        if not http_layer:
            continue

        payload_data = None
        for attr in ['file_data', 'msg_body', 'payload']:
            payload_data = getattr(http_layer, attr, None)
            if payload_data is not None:
                break
        if not payload_data:
            continue

        payload, error = _extract_and_validate_jws(payload_data)
        if error or not isinstance(payload, dict):
            continue

        if payload.get('logEventType') != 'CallSignalingMessageLogEvent':
            continue
            
        direction = payload.get('direction')
        if direction not in {"incoming", "outgoing"}:
            continue
            
        text = payload.get('text', '').strip()
        if not text:
            continue

        call_id = _extract_call_id(text)
        method = _extract_sip_method(text)
        
        if not call_id or not method:
            continue

        if call_id not in messages[direction]:
            messages[direction][call_id] = {}

        messages[direction][call_id][method] = _normalize_sip_message(text)

    all_call_ids = set(messages['incoming'].keys()) | set(messages['outgoing'].keys())
    
    for call_id in all_call_ids:
        incoming_methods = messages['incoming'].get(call_id, {})
        outgoing_methods = messages['outgoing'].get(call_id, {})

        for method in incoming_methods:
            if method not in outgoing_methods:
                return False, f"No matching outgoing {method} message found for Call-ID: {call_id}"

            if incoming_methods[method] != outgoing_methods[method]:
                return False, (
                    f"Message content mismatch for {method} (Call-ID: {call_id})\n"
                    f"Incoming:\n{incoming_methods[method]}\n\n"
                    f"Outgoing:\n{outgoing_methods[method]}"
                )

    for call_id in messages['outgoing']:
        if call_id not in messages['incoming']:
            methods = ', '.join(messages['outgoing'][call_id].keys())
            return False, f"Outgoing message(s) found without matching incoming: {methods} (Call-ID: {call_id})"
    
    return True, None


def _extract_and_validate_jws(body_data, jws_secret=None):
    """Helper to extract and validate JWS from request body.
    
    Args:
        body_data: Raw body data which should be a JWS token in JSON format
        jws_secret: Optional secret for JWS verification (not used in current implementation)
        
    Returns:
        Tuple of (decoded_payload, error_message)
        - On success: (payload_dict, None)
        - On failure: (None, error_message)
    """
    try:
        if isinstance(body_data, bytes):
            body_str = body_data.decode('utf-8', errors='replace')
        else:
            body_str = str(body_data)

        if ':' in body_str:
            try:
                body_str = bytes.fromhex(body_str.replace(':', '')).decode('utf-8', errors='replace')
            except (ValueError, UnicodeDecodeError):
                pass
        
        # Try to parse as JSON first (for JWS JSON Serialization)
        try:
            data = json.loads(body_str)
            # Handle array of JWS objects
            if isinstance(data, list):
                if not data:
                    return None, "Empty JWS array"
                data = data[0]
                
            # Handle JWS JSON Serialization format
            if isinstance(data, dict):
                if 'payload' not in data or 'protected' not in data:
                    return None, "Missing required JWS fields (payload, protected)"
                try:
                    # Try to decode the payload directly first
                    if isinstance(data['payload'], dict):
                        payload = data['payload']
                    else:
                        # else try to decode the base64url encoded payload
                        payload_str = base64.urlsafe_b64decode(
                            data['payload'] + '=' * (-len(data['payload']) % 4)
                        ).decode('utf-8')
                        payload = json.loads(payload_str)
                    
                    # Validate the payload structure
                    if not isinstance(payload, dict):
                        return None, "JWS payload is not a JSON object"
                        
                    # Check for required fields
                    required_fields = ['logEventType', 'timestamp', 'elementId', 'agencyId', 
                                     'direction', 'callId', 'incidentId', 'callIdSIP', 'ipAddressPort']
                    for field in required_fields:
                        if field not in payload:
                            return None, f"Missing required field in JWS payload: {field}"
                            
                    return payload, None
                    
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    return None, f"Failed to decode JWS payload: {str(e)}"
                except Exception as e:
                    return None, f"Error processing JWS payload: {str(e)}"
                
        except json.JSONDecodeError:
            # Not a JSON object, check if it's a compact JWS
            if body_str.count('.') == 2:
                try:
                    # Try to decode without verification first
                    jws_result = decode_jws(body_str, None)
                    if jws_result and len(jws_result) >= 2 and isinstance(jws_result[1], dict):
                        return jws_result[1], None
                except Exception as e:
                    return None, f"Failed to decode compact JWS: {str(e)}"
        
        return None, "Invalid JWS format: Expected JWS JSON object or compact format"
            
    except Exception as e:
        return None, f"Error processing JWS: {str(e)}"


def validate_log_post_presence(http_post_requests, jws_secret=None):
    """
    Validate that HTTP POST contains a valid JWS with LogEvent.
    The JWS payload must contain a LogEvent with one of the required logEventType values.
    Only JWS format is supported - plain JSON will be rejected.
    
    Returns:
        "PASSED" if valid JWS with correct logEventType is found
        Error message starting with "FAILED" if validation fails
    """
    try:
        assert http_post_requests, "FAILED -> No HTTP POST to /LogEvents found"
        requests = http_post_requests if isinstance(http_post_requests, list) else [http_post_requests]
        
        for req in requests:
            if not hasattr(req, 'http'):
                continue
                
            http_layer = req.http
            for attr in ['file_data', 'msg_body', 'payload']:
                if not hasattr(http_layer, attr):
                    continue
                    
                body_data = getattr(http_layer, attr)
                if not body_data:
                    continue
                
                payload, error = _extract_and_validate_jws(body_data, jws_secret)
                if error:
                    continue  # Skip to next request if JWS validation fails

                if isinstance(payload, dict):
                    if payload.get('logEventType') in {"MessageLogEvent", "CallSignalingMessageLogEvent"}:
                        return "PASSED"
                elif isinstance(payload, list):
                    if any(isinstance(item, dict) and 
                          item.get('logEventType') in {"MessageLogEvent", "CallSignalingMessageLogEvent"} 
                          for item in payload):
                        return "PASSED"
        
        return "FAILED -> No valid JWS with required LogEvent found in any request"
        
    except AssertionError as e:
        return str(e)
    except Exception as e:
        return f"FAILED -> Error during validation: {str(e)}"


def _is_valid_log_event(payload):
    """
    Backward-compatible boolean validator. Uses strict field checks under the hood.
    """
    ok, _ = _validate_log_event_record(payload)
    return ok


def _validate_log_event_record(payload):
    """
    Validate that a single log event record contains all required fields with basic sanity.
    "'timestamp', 'elementId', 'agencyId', 'direction','callId', 'incidentId', 'callIdSIP', 'ipAddressPort'"
    Returns True or None if valid, otherwise False
    """
    if not isinstance(payload, dict):
        return False, "Payload is not a JSON object"

    event_type = payload.get('logEventType')
    if event_type not in {"MessageLogEvent", "CallSignalingMessageLogEvent"}:
        return False, ("Missing or invalid 'logEventType'. Expected 'MessageLogEvent' + 'CallSignalingMessageLogEvent' for SIP MESSAGE, "
                     "or 'CallSignalingMessageLogEvent' for other SIP messages like INVITE")

    required_common = [
        'timestamp', 'elementId', 'agencyId', 'direction',
        'callId', 'incidentId', 'callIdSIP', 'ipAddressPort'
    ]
    for f in required_common:
        if f not in payload or payload.get(f) in (None, ""):
            return False, f"Missing required field '{f}'"
    # timestamp validation
    ts = payload.get('timestamp')
    if not is_valid_timestamp(ts):
        return False, "'timestamp' is not a valid format (e.g., '2023-01-01T12:00:00.00+00:00')"
    # Validate direction
    is_valid, error = validate_direction(payload)
    if not is_valid:
        return False, error
    # Validate callId using comprehensive validation methods
    call_id = str(payload.get('callId', ''))
    urn_validation = test_emergency_call_id_urn(call_id)
    if not urn_validation.startswith('PASSED'):
        string_id_validation = test_emergency_call_id_string_id(call_id)
        if not string_id_validation.startswith('PASSED'):
            fqdn_validation = test_emergency_call_id_fqdn(call_id)
            if not fqdn_validation.startswith('PASSED'):
                return False, "'callId' must be a valid URN, String ID, or FQDN format"
    # Validate incidentId using comprehensive validation methods
    incident_id = str(payload.get('incidentId', ''))
    urn_validation = test_incident_tracking_id_urn(incident_id)
    if not urn_validation.startswith('PASSED'):
        string_id_validation = test_incident_tracking_id_string_id(incident_id)
        if not string_id_validation.startswith('PASSED'):
            fqdn_validation = test_incident_tracking_id_fqdn(incident_id)
            if not fqdn_validation.startswith('PASSED'):
                return False, "'incidentId' must be a valid URN, String ID, or FQDN format"
    # Validate ipAddressPort
    ip_port = str(payload.get('ipAddressPort', ''))
    if not validate_ip_port_combo(ip_port):
        return False, "'ipAddressPort' must be a valid IPv4 address and port in format 'A.B.C.D:port' (port 1-65535)"
    # Validate callIdSIP
    call_id_sip = str(payload.get('callIdSIP', ''))
    if not is_valid_sip_call_id(call_id_sip):
        return False, "'callIdSIP' must be a valid SIP callIdSIP format"
    # CallSignalingMessageLogEvent SIP text validation
    if event_type == 'CallSignalingMessageLogEvent':
        text = payload.get('text')
        direction = payload.get('direction', '').lower()
        
        # Basic text validation
        if not isinstance(text, str) or not text.strip():
            return False, "'text' is required and must be a non-empty string for CallSignalingMessageLogEvent"
            
        # Check if it's a valid SIP message
        text_upper = text.upper()
        is_sip_message = ("SIP/2.0" in text_upper or 
                         any(text_upper.lstrip().startswith(method) 
                             for method in ["INVITE", "MESSAGE", "BYE", "ACK", "CANCEL", 
                                          "OPTIONS", "PRACK", "UPDATE", "INFO", "REFER", 
                                          "NOTIFY", "SUBSCRIBE", "PUBLISH"]))
        
        if not is_sip_message:
            return False, "'text' does not appear to contain a valid SIP message"
            
        # For incoming direction, should be a request TO the BCF
        if direction == 'incoming':
            # Should be a request (starts with method) and not a response (starts with SIP/2.0)
            if text_upper.lstrip().startswith('SIP/2.0'):
                return False, "For incoming direction, should contain SIP INVITE/SIP MESSAGE text incoming to the BCF"
        
        # For outgoing direction, should be a request FROM the BCF to TS-ESRP
        elif direction == 'outgoing':
            # Should be a request (starts with method) and not a response (starts with SIP/2.0)
            if text_upper.lstrip().startswith('SIP/2.0'):
                return False, "For outgoing direction, should contain SIP INVITE/SIP MESSAGE text sent by the BCF to TS ESRP"
            
            # Additional check for outgoing messages to TS-ESRP
            # Should contain appropriate headers for TS-ESRP communication
            required_headers = [
                'VIA:',
                'MAX-FORWARDS:',
                'FROM:',
                'TO:',
                'CALL-ID:',
                'CSEQ:',
                'CONTACT:',
                'ALLOW:'
            ]
            missing_headers = [h for h in required_headers if h not in text_upper]
            if missing_headers:
                return False, (f"Outgoing SIP message is missing required headers: "
                             f"{', '.join(h.rstrip(':') for h in missing_headers)}")

    return True, None


def validate_bcf_sip_forwarding(bcf_output_messages):
    """
    Validate that BCF forwarded SIP messages
    """
    try:
        assert bcf_output_messages, "INCONCLUSIVE -> No SIP messages forwarded by BCF found"
        return "PASSED"
    except AssertionError as e:
        return str(e)


def validate_log_event_by_sip_type(http_post_requests, sip_message_type, jws_secret=None):
    """
    Validate HTTP POST log events based on SIP message type.
    Only JWS format is accepted - plain JSON will be rejected.

    For SIP MESSAGE: MUST have two separate HTTP POST requests:
        - One with logEventType='MessageLogEvent'
        - Another with logEventType='CallSignalingMessageLogEvent'
    For other SIP types: MUST have one HTTP POST with logEventType='CallSignalingMessageLogEvent'

    Args:
        http_post_requests: List of HTTP POST request packets from pyshark, or a single request
        sip_message_type: The SIP message type (e.g., 'MESSAGE', 'INVITE', 'BYE')
        jws_secret: Optional JWS secret for decoding signed payloads

    Returns:
        "PASSED" if validation succeeds, error message otherwise
    """
    try:
        requests = [http_post_requests] if not isinstance(http_post_requests, list) else http_post_requests
        assert requests, "FAILED -> No HTTP POST to /LogEvents found"

        is_sip_message = sip_message_type.upper() == 'MESSAGE'
        required_types = {'MessageLogEvent', 'CallSignalingMessageLogEvent'} if is_sip_message else {'CallSignalingMessageLogEvent'}
        type_desc = "TWO separate HTTP POSTs with 'MessageLogEvent' and 'CallSignalingMessageLogEvent'" if is_sip_message \
                  else "ONE HTTP POST with 'CallSignalingMessageLogEvent'"

        found_types = set()
        valid_events_by_type = {"MessageLogEvent": [], "CallSignalingMessageLogEvent": []}
        invalid_reasons = []

        for request in requests:
            if not hasattr(request, 'http'):
                continue
                
            http_layer = request.http
            for attr in ['file_data', 'msg_body', 'payload']:
                if not hasattr(http_layer, attr):
                    continue
                    
                body_data = getattr(http_layer, attr)
                if not body_data:
                    continue
                
                # Extract and validate JWS
                payload, error = _extract_and_validate_jws(body_data, jws_secret)
                if error:
                    invalid_reasons.append(f"Invalid JWS: {error}")
                    continue
                
                # Process the JWS payload
                if isinstance(payload, dict):
                    payloads = [payload]
                elif isinstance(payload, list):
                    payloads = [p for p in payload if isinstance(p, dict)]
                else:
                    invalid_reasons.append("JWS payload is not a JSON object or array")
                    continue
                
                for p in payloads:
                    if 'logEventType' not in p:
                        continue
                        
                    event_type = p.get('logEventType')
                    ok, reason = _validate_log_event_record(p)
                    
                    if ok and event_type in required_types:
                        found_types.add(event_type)
                        valid_events_by_type[event_type].append(p)
                    elif reason:
                        invalid_reasons.append(f"{event_type or 'UnknownType'}: {reason}")

        # Validation logic
        if is_sip_message:
            if found_types == required_types and len(valid_events_by_type["MessageLogEvent"]) > 0 and len(valid_events_by_type["CallSignalingMessageLogEvent"]) > 0:
                # Check linkage between MessageLogEvent and CallSignalingMessageLogEvent
                mle = valid_events_by_type["MessageLogEvent"][0]
                cs = valid_events_by_type["CallSignalingMessageLogEvent"][0]
                linkage_fields = ["callId", "incidentId", "callIdSIP", "ipAddressPort"]
                mismatches = [f for f in linkage_fields if str(mle.get(f)) != str(cs.get(f))]
                
                if mismatches:
                    return (
                        "FAILED -> For SIP MESSAGE: linkage mismatch between MessageLogEvent and "
                        f"CallSignalingMessageLogEvent for fields: {mismatches}"
                    )
                return "PASSED"
            else:
                missing = required_types - found_types
                error_msg = f"FAILED -> For SIP MESSAGE: Expected {type_desc}. "
                if missing:
                    error_msg += f"Missing event types: {missing}. "
                if invalid_reasons:
                    error_msg += f"Validation errors: {sorted(set(invalid_reasons))}"
                return error_msg
        else:
            if 'CallSignalingMessageLogEvent' in found_types and valid_events_by_type['CallSignalingMessageLogEvent']:
                return "PASSED"
            else:
                error_msg = f"FAILED -> For {sip_message_type}: Expected {type_desc}. "
                if invalid_reasons:
                    error_msg += f"Validation errors: {sorted(set(invalid_reasons))}"
                return error_msg

    except AssertionError as e:
        return str(e)
    except Exception as e:
        return f"ERROR -> Unexpected error during validation: {str(e)}"