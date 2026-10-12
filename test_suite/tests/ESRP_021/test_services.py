from checks.general.checks import (
    is_data_present,
    is_test_data_the_same,
    check_each_element,
    test_if_parameter_has_expected_value,
)
from checks.log_events.checks import (
    validate_optional_log_event_fields,
    validate_timestamps,
    validate_parameter_sequence,
    validate_expiration_sequence,
    validate_response_sequence,
    validate_purpose_sequence,
    validate_subscription_id_consistency,
)
from checks.log_events.log_events import SubscribeLogEvent
from services.aux_services.aux_services import get_messages
from services.aux_services.message_services import get_logevent_list_by_type
from services.aux_services.sip_msg_body_services import clean_up_string
from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
)
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.message_collector_service import MessageCollectorService
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_021.checks import (
    precondition_check,
    validate_fqdn_field,
)
from tests.ESRP_021.constants import (
    EXPECTED_COUNTS,
    EXPECTED_PURPOSES,
    EXPECTED_RESPONSES,
    TIMESTAMP_THRESHOLD,
    VARIATIONS,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, key_filepath, esrp_fqdn, peer_fqdn)
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    key_filepath = None
    peer_fqdn = None

    iut_entity = lab_config.get_conformance_iut_entity()
    esrp_fqdn = iut_entity.get_first_available_fqdn() if iut_entity else None

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if not stimulus or not output:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    for entity in lab_config.entities:
        for interface in entity.interfaces:
            if interface.name == stimulus.src_interface:
                stimulus_src_ip = interface.ip
                peer_fqdn = interface.fqdn or entity.get_first_available_fqdn()
            elif interface.name == stimulus.dst_interface:
                stimulus_dst_ip = interface.ip
            if interface.name == output.src_interface:
                key_filepath = entity.certificate_key

    if stimulus_src_ip is None or stimulus_dst_ip is None:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )
    if not esrp_fqdn or not peer_fqdn:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required FQDN records "
            "for ESRP/CHFE interfaces"
        )

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        key_filepath,
        esrp_fqdn,
        peer_fqdn,
    )


def _extract_expiration(stimulus_message, response_message):
    """
    Prefers the 'Expires' header on the SIP response (the negotiated
    expiration returned in the 200 OK); falls back to the 'Expires' header
    of the stimulus SUBSCRIBE for negative responses (489) that carry no
    Expires header of their own.
    """
    for message in (response_message, stimulus_message):
        if not message:
            continue
        expires_fields = extract_all_header_fields_matching_name_from_sip_message(
            message, "Expires"
        )
        if expires_fields:
            try:
                return int(clean_up_string(expires_fields[0].split(":", 1)[1].strip()))
            except (ValueError, IndexError):
                return None
    return None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    variation_number = VARIATIONS.get(variation.name)
    if variation_number is None:
        raise VariationNotFoundError(
            f"Unknown variation name: '{variation.name}'\n"
            f"Expected variation names by Test Case: '{VARIATIONS}'"
        )
    expected_package = (
        "UnsupportedPackage" if variation_number == 3 else "AbandonedCall"
    )

    (
        stimulus_src_ip,
        stimulus_dst_ip,
        key_filepath,
        esrp_fqdn,
        peer_fqdn,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    # There are 2 SIP SUBSCRIBE event - initial/refresh, initial/terminate
    stimulus_messages = (
        get_messages(
            pcap_service,
            FilterConfig(
                src_ip=stimulus_src_ip,
                dst_ip=stimulus_dst_ip,
                packet_type=PacketTypeEnum.SIP,
                message_method=[SIPMethodEnum.SUBSCRIBE],
            ),
        )
        or []
    )
    stimulus_messages = sorted(
        stimulus_messages, key=lambda msg: float(getattr(msg, "sniff_timestamp", 0))
    )

    response_messages = []
    if stimulus_messages:
        first_timestamp = float(stimulus_messages[0].sniff_timestamp)
        response_candidates = (
            get_messages(
                pcap_service,
                FilterConfig(
                    src_ip=stimulus_dst_ip,
                    dst_ip=stimulus_src_ip,
                    packet_type=PacketTypeEnum.SIP,
                    after_timestamp=first_timestamp,
                ),
            )
            or []
        )

        # Collect final (non-provisional) responses for SIP SUBSCRIBE messages
        response_messages = sorted(
            (
                message
                for message in response_candidates
                if message.sip.get("cseq_method") == SIPMethodEnum.SUBSCRIBE
                and message.sip.get("status_code")
                and int(message.sip.get("status_code")) >= 200
            ),
            key=lambda msg: float(getattr(msg, "sniff_timestamp", 0)),
        )

    # Collect HTTP logEvent messages
    http_collector = MessageCollectorService(
        interfaces=["IF_ESRP_LOG"],
        pcap_service=pcap_service,
        lab_config=lab_config,
        packet_type=[PacketTypeEnum.HTTP],
    )
    esrp_log_events = http_collector.get_requests("IF_ESRP_LOG")

    # Filter out non-SubscribeLogEvent
    subscribe_payloads = get_logevent_list_by_type(
        esrp_log_events, "SubscribeLogEvent", key_filepath
    )
    subscribe_log_events = [
        SubscribeLogEvent(payload) for payload in subscribe_payloads
    ]

    stimulus_timestamps = [
        float(getattr(message, "sniff_timestamp", 0)) for message in stimulus_messages
    ]

    expected_parameters = []
    expected_expirations = []
    for idx, stimulus_message in enumerate(stimulus_messages):
        response_message = (
            response_messages[idx] if idx < len(response_messages) else None
        )

        parameters = SipMessage.from_packet(stimulus_message).event.params
        expected_parameters.append(
            [{"type": name, "value": value} for name, value in parameters.items()]
        )
        expected_expirations.append(
            _extract_expiration(stimulus_message, response_message)
        )

    expected_count = EXPECTED_COUNTS.get(variation_number, 0)
    expected_purposes = EXPECTED_PURPOSES.get(variation_number, [])
    expected_responses = EXPECTED_RESPONSES.get(variation_number, [])

    return (
        esrp_fqdn,
        peer_fqdn,
        stimulus_messages,
        stimulus_timestamps,
        subscribe_log_events,
        expected_count,
        expected_purposes,
        expected_responses,
        expected_parameters,
        expected_expirations,
        expected_package,
    )


def get_test_names() -> list:
    return [
        "Validate ESRP sends HTTP POST 'SubscribeLogEvent' record(s) to /LogEvents",
        "Validate the number of 'SubscribeLogEvent' records matches the number of SUBSCRIBE transactions",
        "Validate 'logEventType' attribute value in 'SubscribeLogEvent'",
        "Validate 'timestamp' attribute format and match with SIP SUBSCRIBE",
        "Validate 'elementId' attribute is a valid FQDN",
        "Validate 'elementId' attribute has value of ESRP FQDN",
        "Validate 'agencyId' attribute is a valid FQDN",
        "Validate 'direction' attribute value in 'SubscribeLogEvent'",
        "Validate 'package' attribute value in 'SubscribeLogEvent'",
        "Validate 'peer' attribute references Test System CHFE",
        "Validate 'parameter' attribute matches SIP Event header parameters",
        "Validate 'expiration' attribute matches negotiated/Expires header value",
        "Validate 'response' attribute value in 'SubscribeLogEvent'",
        "Validate 'purpose' attribute sequence in 'SubscribeLogEvent'",
        "Validate 'subscriptionId' attribute is consistent between initial and refresh/terminate SubscribeLogEvent",
        "Validate optional fields in 'SubscribeLogEvent'",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:

    (
        esrp_fqdn,
        peer_fqdn,
        stimulus_messages,
        stimulus_timestamps,
        subscribe_log_events,
        expected_count,
        expected_purposes,
        expected_responses,
        expected_parameters,
        expected_expirations,
        expected_package,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    precondition = precondition_check(stimulus_messages, subscribe_log_events)
    precondition_error = precondition

    return [
        TestCheck(
            test_name="Validate ESRP sends HTTP POST 'SubscribeLogEvent' record(s) to /LogEvents",
            precondition=stimulus_messages,
            precondition_error="NOT RUN -> No SIP SUBSCRIBE stimulus message found",
            test_method=is_data_present,
            test_params={
                "test_data": subscribe_log_events,
                "error": "FAILED -> No HTTP POST 'SubscribeLogEvent' record found",
            },
        ),
        TestCheck(
            test_name="Validate the number of 'SubscribeLogEvent' records matches the number of SUBSCRIBE transactions",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=is_test_data_the_same,
            test_params={
                "actual_data": len(subscribe_log_events),
                "expected_data": expected_count,
            },
        ),
        TestCheck(
            test_name="Validate 'logEventType' attribute value in 'SubscribeLogEvent'",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": subscribe_log_events,
                "element_attrs": {"actual_data": "logEventType"},
                "expected_data": "SubscribeLogEvent",
            },
        ),
        TestCheck(
            test_name="Validate 'timestamp' attribute format and match with SIP SUBSCRIBE",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=validate_timestamps,
            test_params={
                "subscribe_log_events": subscribe_log_events,
                "stimulus_timestamps": stimulus_timestamps,
                "threshold": TIMESTAMP_THRESHOLD,
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute is a valid FQDN",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=check_each_element,
            test_params={
                "check_method": validate_fqdn_field,
                "collection": subscribe_log_events,
                "element_attrs": {"fqdn_string": "elementId"},
            },
        ),
        TestCheck(
            test_name="Validate 'elementId' attribute has value of ESRP FQDN",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": subscribe_log_events,
                "element_attrs": {"actual_data": "elementId"},
                "expected_data": esrp_fqdn,
            },
        ),
        TestCheck(
            test_name="Validate 'agencyId' attribute is a valid FQDN",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=check_each_element,
            test_params={
                "check_method": validate_fqdn_field,
                "collection": subscribe_log_events,
                "element_attrs": {"fqdn_string": "agencyId"},
            },
        ),
        TestCheck(
            test_name="Validate 'direction' attribute value in 'SubscribeLogEvent'",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=check_each_element,
            test_params={
                "check_method": is_test_data_the_same,
                "collection": subscribe_log_events,
                "element_attrs": {"actual_data": "direction"},
                "expected_data": "incoming",
            },
        ),
        TestCheck(
            test_name="Validate 'package' attribute value in 'SubscribeLogEvent'",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=check_each_element,
            test_params=(
                {
                    "check_method": is_test_data_the_same,
                    "collection": subscribe_log_events,
                    "element_attrs": {"actual_data": "package"},
                    "expected_data": expected_package,
                }
            ),
        ),
        TestCheck(
            test_name="Validate 'peer' attribute references Test System CHFE",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=check_each_element,
            test_params={
                "check_method": test_if_parameter_has_expected_value,
                "collection": subscribe_log_events,
                "element_attrs": {"parameter_value": "peer"},
                "parameter_name": "peer",
                "expected_value": peer_fqdn,
            },
        ),
        TestCheck(
            test_name="Validate 'parameter' attribute matches SIP Event header parameters",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=validate_parameter_sequence,
            test_params={
                "subscribe_log_events": subscribe_log_events,
                "expected_parameters": expected_parameters,
            },
        ),
        TestCheck(
            test_name="Validate 'expiration' attribute matches negotiated/Expires header value",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=validate_expiration_sequence,
            test_params={
                "subscribe_log_events": subscribe_log_events,
                "expected_expirations": expected_expirations,
            },
        ),
        TestCheck(
            test_name="Validate 'response' attribute value in 'SubscribeLogEvent'",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=validate_response_sequence,
            test_params={
                "subscribe_log_events": subscribe_log_events,
                "expected_responses": expected_responses,
            },
        ),
        TestCheck(
            test_name="Validate 'purpose' attribute sequence in 'SubscribeLogEvent'",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=validate_purpose_sequence,
            test_params={
                "subscribe_log_events": subscribe_log_events,
                "expected_purposes": expected_purposes,
            },
        ),
        TestCheck(
            test_name="Validate 'subscriptionId' attribute is consistent between initial and refresh/terminate SubscribeLogEvent",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=validate_subscription_id_consistency,
            test_params={
                "subscribe_log_events": subscribe_log_events,
            },
        ),
        TestCheck(
            test_name="Validate optional fields in 'SubscribeLogEvent'",
            precondition=precondition == "PASSED",
            precondition_error=precondition_error,
            test_method=check_each_element,
            test_params={
                "check_method": validate_optional_log_event_fields,
                "collection": subscribe_log_events,
            },
        ),
    ]
