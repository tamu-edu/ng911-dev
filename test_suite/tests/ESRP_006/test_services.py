from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, SIPMethodEnum
from checks.general.checks import test_if_parameter_has_expected_value, test_if_parameter_has_one_of_expected_values
from checks.sip.call_info_header_field_checks.checks import (
    test_incident_tracking_id_string_id,
    test_emergency_call_id_urn,
    test_emergency_call_id_fqdn,
    test_incident_tracking_id_urn,
    test_emergency_call_id_string_id,
    test_incident_tracking_id_fqdn,
)
from checks.sip.header_field_checks.checks import test_keeping_original_header_fields_in_sip_message
from services.aux.sip_services import extract_all_header_fields_matching_name_from_sip_message
from services.test_services.test_conduction_service import TestCheck
from .constants import (
    BCF_IP,
    ESRP_IP,
    ECRF_LVF_IP
)
from services.aux.message_services import (
    get_header_field_value,
    extract_all_contents_from_message_body,
    extract_ip_and_port_from_text,
    extract_sip_uri_from_text
)
from services.aux.xml_services import extract_all_values_for_xml_tag_name


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
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT.value:
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
        raise WrongConfigurationError("It seems that the Run Config does not contain required"
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter]) -> list:

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
    output_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE,]
        )
    )
    http_response = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            http_status_code=200
        )
    )
    esrp_via_header_address_port = extract_ip_and_port_from_text(
        get_header_field_value(output_message, 'Via')
    )
    esrp_address_port = f'{output_message.ip.addr}:{output_message.tcp.dstport}'
    esrp_route_header_queue_uri = extract_sip_uri_from_text(
        get_header_field_value(output_message, 'Route')
    )
    ecrf_response_xml = extract_all_contents_from_message_body(http_response)[0]['body']
    ecrf_response_queue_uri_list = [uri for uri in extract_all_values_for_xml_tag_name(ecrf_response_xml, 'uri')
                                    if extract_sip_uri_from_text(uri)]
    try:
        esrp_route_header_lr_param = get_header_field_value(output_message, 'Route')\
            .replace(" ","")\
            .split(";")[1]\
            .split(">")[0]
    except IndexError:
        esrp_route_header_lr_param = ""

    esrp_call_info_header_emergency_call_id = ""
    for header in extract_all_header_fields_matching_name_from_sip_message('Call-Info', output_message):
        if 'uid:callid' in header:
            esrp_call_info_header_emergency_call_id = header
            break
    esrp_call_info_header_incident_tracking_id = ""

    for header in extract_all_header_fields_matching_name_from_sip_message('Call-Info', output_message):
        if 'uid:incidentid' in header:
            esrp_call_info_header_incident_tracking_id = header
            break

    return [stimulus_message, output_message, esrp_via_header_address_port, esrp_address_port,
            esrp_route_header_queue_uri, ecrf_response_queue_uri_list, esrp_route_header_lr_param,
            esrp_call_info_header_emergency_call_id, esrp_call_info_header_incident_tracking_id]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        stimulus_message,
        output_message,
        esrp_via_header_address_port,
        esrp_address_port,
        esrp_route_header_queue_uri,
        ecrf_response_queue_uri_list,
        esrp_route_header_lr_param,
        esrp_call_info_header_emergency_call_id,
        esrp_call_info_header_incident_tracking_id
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)
    return [
        TestCheck(
            test_name="Adding 'Via' header field specifying ESRP",
            test_method=test_if_parameter_has_expected_value,
            test_params={
                "parameter_name": "address:port in 'Via' header field",
                "parameter_value": esrp_via_header_address_port,
                "expected_value": esrp_address_port
            }
        ),
        TestCheck(
            test_name="Adding 'Route' header field with queue URI received from ECRF",
            test_method=test_if_parameter_has_one_of_expected_values,
            test_params={
                "parameter_name": "queue URI in 'Route' header field",
                "parameter_value": esrp_route_header_queue_uri,
                "expected_values": ecrf_response_queue_uri_list
            }
        ),
        TestCheck(
            test_name="Added 'Route' header field contains 'lr' parameter",
            test_method=test_if_parameter_has_expected_value,
            test_params={
                "parameter_name": "'Route' header field",
                "parameter_value": esrp_route_header_lr_param,
                "expected_value": "lr"
            }
        ),
        TestCheck(
            test_name="Emergency Call Identifier URN",
            test_method=test_emergency_call_id_urn,
            test_params={
                "emergency_call_id_header": esrp_call_info_header_emergency_call_id
            }
        ),
        TestCheck(
            test_name="Emergency Call Identifier String ID",
            test_method=test_emergency_call_id_string_id,
            test_params={
                "emergency_call_id_header": esrp_call_info_header_emergency_call_id
            }
        ),
        TestCheck(
            test_name="Emergency Call Identifier FQDN",
            test_method=test_emergency_call_id_fqdn,
            test_params={
                "emergency_call_id_header": esrp_call_info_header_emergency_call_id
            }
        ),
        TestCheck(
            test_name="Incident Tracking Identifier URN",
            test_method=test_incident_tracking_id_urn,
            test_params={
                "incident_tracking_id_header": esrp_call_info_header_incident_tracking_id
            }
        ),
        TestCheck(
            test_name="Incident Tracking Identifier String ID",
            test_method=test_incident_tracking_id_string_id,
            test_params={
                "incident_tracking_id_header": esrp_call_info_header_incident_tracking_id
            }
        ),
        TestCheck(
            test_name="Incident Tracking Identifier FQDN",
            test_method=test_incident_tracking_id_fqdn,
            test_params={
                "incident_tracking_id_header": esrp_call_info_header_incident_tracking_id
            }
        ),
        TestCheck(
            test_name="Keeping original header fields",
            test_method=test_keeping_original_header_fields_in_sip_message,
            test_params={
                "stimulus": stimulus_message,
                "output": output_message
            }
        )
    ]
