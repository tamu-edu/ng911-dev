from checks.sip.header_field_checks.checks import test_urn_service_sos_in_request_uri, \
    test_urn_service_sos_in_to_header_field
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    extract_header_by_pattern, get_first_message_matching_filter, split_sip_header_by_pattern
)
from enums import PacketTypeEnum, SIPMethodEnum
from checks.sip.call_info_header_field_checks.checks import (
    test_incident_tracking_id_string_id,
    test_emergency_call_id_urn,
    test_emergency_call_id_fqdn,
    test_emergency_call_id_header,
    test_incident_tracking_id_urn,
    test_emergency_call_id_string_id,
    test_incident_tracking_id_fqdn,
)
from checks.sip.call_info_header_field_checks.constants import (
    EMERGENCY_IDENTIFIER_URN_PATTERN,
    INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN
)
from checks.sip.resource_priority_header_field_checks.constants import RESOURCE_PRIORITY_PATTERN
from checks.sip.resource_priority_header_field_checks.checks import test_resource_priority
from checks.sip.stimulus_output_by_call_id_check.checks import test_compare_stimulus_and_output_messages
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter]) -> tuple[str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message

    if stimulus and output:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_scr_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None or out_scr_ip is None or out_dst_ip is None:
            raise WrongConfigurationError("It seems that the LabConfig does not contain required"
                                          "parameters for osp_ip, bcf_ip, esrp_ip addresses")
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter]) -> list:
    # TODO design what to do for multiply stimulus and outputs
    stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip = get_filter_parameters(lab_config, filtering_options)
    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE,]
        )
    )
    bcf_output_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE,]
        )
    )

    if bcf_output_message is not None and hasattr(bcf_output_message, 'sip'):
        bcf_o_headers = split_sip_header_by_pattern(bcf_output_message.sip.get('msg_hdr'))
        emergency_call_id_header = extract_header_by_pattern(
            # bcf_output_message.sip.get('Call-Info'),
            bcf_o_headers.get('Call-Info'),
            EMERGENCY_IDENTIFIER_URN_PATTERN
        )
        incident_tracking_id_header = extract_header_by_pattern(
            # bcf_output_message.sip.get('Call-Info'),
            bcf_o_headers.get('Call-Info'),
            INCIDENT_TRACKING_IDENTIFIER_URN_PATTERN
        )
        resource_priority_header = extract_header_by_pattern(
            # bcf_output_message.sip.get('Resource-Priority'),
            bcf_o_headers.get('Resource-Priority'),
            RESOURCE_PRIORITY_PATTERN
        )
    else:
        emergency_call_id_header, incident_tracking_id_header, resource_priority_header = None, None, None

    return [stimulus_message, bcf_output_message, emergency_call_id_header,
            incident_tracking_id_header, resource_priority_header]


def get_test_names() -> list:
    return [
        f"Stimulus and Output messages comparison",
        f"Emergency Call Identifier header",
        f"Emergency Call Identifier URN",
        f"Emergency Call Identifier String ID",
        f"Emergency Call Identifier FQDN",
        f"Incident Tracking Identifier URN",
        f"Incident Tracking Identifier String ID",
        f"Incident Tracking Identifier FQDN",
        f"Resource Priority header",
        f"Verify 'urn:service:sos' in request URI",
        f"Verify 'urn:service:sos' is in 'TO' header field"
    ]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        stimulus_message,
        bcf_output_message,
        emergency_call_id_header,
        incident_tracking_id_header,
        resource_priority_header
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)
    return [
        TestCheck(
            test_name="Stimulus and Output messages comparison",
            test_method=test_compare_stimulus_and_output_messages,
            test_params={
                "stimulus": stimulus_message,
                "output": bcf_output_message
            }
        ),
        TestCheck(
            test_name="Emergency Call Identifier header",
            test_method=test_emergency_call_id_header,
            test_params={
                "emergency_call_id_header": emergency_call_id_header,
            }
        ),
        TestCheck(
            test_name="Emergency Call Identifier URN",
            test_method=test_emergency_call_id_urn,
            test_params={
                "emergency_call_id_header": emergency_call_id_header,
            }
        ),
        TestCheck(
            test_name="Emergency Call Identifier String ID",
            test_method=test_emergency_call_id_string_id,
            test_params={
                "emergency_call_id_header": emergency_call_id_header,
            }
        ),
        TestCheck(
            test_name="Emergency Call Identifier FQDN",
            test_method=test_emergency_call_id_fqdn,
            test_params={
                "emergency_call_id_header": emergency_call_id_header,
            }
        ),
        TestCheck(
            test_name="Incident Tracking Identifier URN",
            test_method=test_incident_tracking_id_urn,
            test_params={
                "incident_tracking_id_header": incident_tracking_id_header,
            }
        ),
        TestCheck(
            test_name="Incident Tracking Identifier String ID",
            test_method=test_incident_tracking_id_string_id,
            test_params={
                "incident_tracking_id_header": incident_tracking_id_header,
            }
        ),
        TestCheck(
            test_name="Incident Tracking Identifier FQDN",
            test_method=test_incident_tracking_id_fqdn,
            test_params={
                "incident_tracking_id_header": incident_tracking_id_header,
            }
        ),
        TestCheck(
            test_name="Resource Priority header",
            test_method=test_resource_priority,
            test_params={
                "resource_priority_header": resource_priority_header,
            }
        ),
        TestCheck(
            test_name="Verify 'urn:service:sos' in request URI",
            test_method=test_urn_service_sos_in_request_uri,
            test_params={
                "output": bcf_output_message,
            }
        ),
        TestCheck(
            test_name="Verify 'urn:service:sos' is in 'TO' header field",
            test_method=test_urn_service_sos_in_to_header_field,
            test_params={
                "output": bcf_output_message,
            }
        )
    ]


