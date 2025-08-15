from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from checks.general.checks import test_if_parameter_has_expected_value, test_if_parameter_has_one_of_expected_values
from checks.http.lost_checks.checks import test_if_geolocation_included_in_find_service
from checks.sip.call_info_header_field_checks.checks import (
    test_incident_tracking_id_string_id,
    test_emergency_call_id_urn,
    test_emergency_call_id_fqdn,
    test_incident_tracking_id_urn,
    test_emergency_call_id_string_id,
    test_incident_tracking_id_fqdn,
    test_call_info_header_contains_correct_purpose
)
from checks.sip.header_field_checks.checks import test_keeping_original_header_fields_in_sip_message
from services.aux_services.sip_services import extract_all_header_fields_matching_name_from_sip_message
from services.test_services.test_assessment_service import TestCheck

from services.aux_services.message_services import (
    get_header_field_value,
    extract_ip_and_port_from_text,
    extract_sip_uri_from_text, get_header_field_multiple_values
)
from services.aux_services.xml_services import extract_all_values_for_xml_tag_name


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation) -> tuple[
    str, str, str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip,
                                            xml_sender_data_path), strings
    """
    stimulus = None
    output = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    xml_sender_data_path = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT.value:
            output = message

    for message in variation.params['messages']:
        if all((message.get('action', None) == 'receive',
                message.get('type', None) == 'HTTP',
                message.get('method', None) == 'GET',
                message.get('response_code', None) == '200')):
            xml_sender_data_path = message.get('body').removeprefix('file.')

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
        if (stimulus_src_ip is None or stimulus_dst_ip is None
                or out_scr_ip is None or out_dst_ip is None):
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, xml_sender_data_path
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> list:
    (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, http_stub_server_response_path) = (
        get_filter_parameters(lab_config, filtering_options, variation))

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )

    output_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )
    content = ''
    if http_stub_server_response_path:
        with open(http_stub_server_response_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

    geolocation_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            # TODO find a way to get exact method GET/POST
            #message_method=[HTTPMethodEnum.GET, ]
        )
    )

    find_service_request = None
    stimulus_geolocation = None
    if geolocation_request:
        find_service_request = geolocation_request.xml.get('cdata', None)

    if stimulus_message:
        stimulus_geolocation = stimulus_message.sip.get('xml_cdata', None)

    esrp_via_header_address_port = [extract_ip_and_port_from_text(via_string)
                                    for via_string
                                    in get_header_field_multiple_values(output_message,
                                                                        'Via',
                                                                        coma_separated=False)]

    try:
        esrp_address_port = f'{output_message.ip.addr}:{output_message.tcp.dstport}'
        esrp_route_header_queue_uri_set = get_header_field_multiple_values(output_message,
                                                                           'Route',
                                                                           coma_separated=False)
    except AttributeError:
        esrp_route_header_queue_uri_set = ""
        esrp_address_port = ""

    ecrf_response_queue_uri_list = [uri for uri in extract_all_values_for_xml_tag_name(content, 'uri')
                                    if extract_sip_uri_from_text(uri)]
    try:
        esrp_route_header_lr_param = get_header_field_value(output_message, 'Route') \
            .replace(" ", "") \
            .split(";")[1] \
            .split(">")[0]
    except (IndexError, AttributeError):
        esrp_route_header_lr_param = ""

    esrp_call_info_header_emergency_call_id = []
    esrp_call_info_header_incident_tracking_id = []
    for header in extract_all_header_fields_matching_name_from_sip_message('Call-Info', output_message):
        if 'uid:callid' in header:
            esrp_call_info_header_emergency_call_id.append(header)
        if 'uid:incidentid' in header:
            esrp_call_info_header_incident_tracking_id.append(header)

    return [stimulus_message, output_message, esrp_via_header_address_port, esrp_address_port,
            esrp_route_header_queue_uri_set, ecrf_response_queue_uri_list, esrp_route_header_lr_param,
            esrp_call_info_header_emergency_call_id, esrp_call_info_header_incident_tracking_id,
            find_service_request, stimulus_geolocation]


def get_test_names() -> list:
    return [
         f"'findService' contains geolocations from received SIP INVITE",
         f"Adding 'Via' header field specifying ESRP",
         f"Adding 'Route' header field with queue URI received from ECRF",
         f"Added 'Route' header field contains 'lr' parameter",
         f"Emergency Call Identifier URN",
         f"Emergency Call Identifier String ID",
         f"Emergency Call Identifier FQDN",
         f"Emergency Call Identifier 'purpose' parameter",
         f"Incident Tracking Identifier URN",
         f"Incident Tracking Identifier String ID",
         f"Incident Tracking Identifier FQDN",
         f"Incident Tracking Identifier 'purpose' parameter",
         f"Keeping original header fields",
    ]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    (
        stimulus_message,
        output_message,
        esrp_via_header_address_port,
        esrp_address_port,
        esrp_route_header_queue_uri_set,
        ecrf_response_queue_uri_list,
        esrp_route_header_lr_param,
        esrp_call_info_header_emergency_call_id,
        esrp_call_info_header_incident_tracking_id,
        find_service_request,
        stimulus_geolocation
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="'findService' contains geolocations from received SIP INVITE",
            test_method=test_if_geolocation_included_in_find_service,
            test_params={
                "parameter_value": find_service_request,
                "expected_value": stimulus_geolocation
            }
        ),
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
                "parameter_value": esrp_route_header_queue_uri_set,
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
            test_name="Emergency Call Identifier 'purpose' parameter",
            test_method=test_call_info_header_contains_correct_purpose,
            test_params={
                "parameter_value": esrp_call_info_header_emergency_call_id,
                "expected_purpose": "emergency-CallId"
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
            test_name="Incident Tracking Identifier 'purpose' parameter",
            test_method=test_call_info_header_contains_correct_purpose,
            test_params={
                "parameter_value": esrp_call_info_header_incident_tracking_id,
                "expected_purpose": "emergency-IncidentId"
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
