import json

from services.aux_services.json_services import is_jws
from services.aux_services.message_services import extract_json_data_from_http
from services.aux_services.sip_services import extract_sip_header_values
from services.config.types.run_config import MessageFilter, RunVariation

from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (get_first_message_matching_filter,
                                                get_dns_packets_from_pcap, get_dns_list, get_messages)
from enums import PacketTypeEnum, HTTPMethodEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_008.checks import validate_esrp_retrieving_additional_data


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter], variation,
                          pcap_service: PcapCaptureService) -> dict:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :param pcap_service: PcapCaptureService instance
    :return: Dictionary with interfaces
    """
    interfaces_dict = {}

    dns_packets = get_dns_packets_from_pcap(pcap_service)

    for entity in lab_config.entities:
        for interface in entity.interfaces:
            port_dict = {}
            for pm in interface.port_mapping:
                port_dict[pm.name] = {
                    "protocol": pm.protocol,
                    "port": pm.port,
                    "transport_protocol": pm.transport_protocol
                }

            interfaces_dict[interface.name] = {
                "ip": interface.ip,
                "ip_list": get_dns_list(dns_packets, interface.fqdn) or [],
                "port_mapping": port_dict
            }

    if not interfaces_dict:
        raise WrongConfigurationError("Lab Config file error - cannot extract interface data")
    else:
        return interfaces_dict


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter], variation) -> tuple:
    interfaces_dict = (get_filter_parameters(lab_config, filtering_options, variation, pcap_service))

    emergency_call_data_list = []
    is_jws_in_response_valid = False
    esrp_emergency_call_data_list = []

    # Filter out Test System OSP cal to BCF
    osp_invite_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict['IF_OSP_BCF']['ip'],
            dst_ip=interfaces_dict['IF_BCF_OSP']['ip'],
            src_ip_list=interfaces_dict['IF_OSP_BCF']['ip_list'],
            dst_ip_list=interfaces_dict['IF_BCF_OSP']['ip_list'],
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )

    if osp_invite_request:
        emergency_call_data_list = extract_sip_header_values(osp_invite_request,
                                                             "Call-Info",
                                                             'purpose=EmergencyCallData')

    bcf_invite_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict['IF_BCF_ESRP']['ip'],
            dst_ip=interfaces_dict['IF_ESRP_BCF']['ip'],
            src_ip_list=interfaces_dict['IF_BCF_ESRP']['ip_list'],
            dst_ip_list=interfaces_dict['IF_ESRP_BCF']['ip_list'],
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )

    esrp_get_policies_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict['IF_ESRP_PS']['ip'],
            dst_ip=interfaces_dict['IF_PS_ESRP']['ip'],
            src_ip_list=interfaces_dict['IF_ESRP_PS']['ip_list'],
            dst_ip_list=interfaces_dict['IF_PS_ESRP']['ip_list'],
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.GET, ]
        )
    )

    if esrp_get_policies_request:
        ps_response_mgs = get_messages(
            pcap_service,
            FilterConfig(
                src_ip=interfaces_dict['IF_PS_ESRP']['ip'],
                dst_ip=interfaces_dict['IF_ESRP_PS']['ip'],
                src_ip_list=interfaces_dict['IF_PS_ESRP']['ip_list'],
                dst_ip_list=interfaces_dict['IF_ESRP_PS']['ip_list'],
                packet_type=PacketTypeEnum.HTTP,
                after_timestamp=float(esrp_get_policies_request.sniff_timestamp)
            )
        )

        if ps_response_mgs:
            for msg in ps_response_mgs:
                if hasattr(msg, 'http') and hasattr(msg.http, 'response_code') and msg.http.response_code == '200':
                    if hasattr(msg, 'xml'):
                        jws = extract_json_data_from_http(msg)
                        is_jws_in_response_valid = is_jws(jws)
                        if not is_jws_in_response_valid:
                            json_string = jws.replace("'", '"')
                            # Parse as JSON
                            jsw_dict = json.loads(json_string)
                            is_jws_in_response_valid = is_jws(jsw_dict)

    esrp_get_adr_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict['IF_ESRP_ADR']['ip'],
            dst_ip=interfaces_dict['IF_ADR_ESRP']['ip'],
            src_ip_list=interfaces_dict['IF_ESRP_ADR']['ip_list'],
            dst_ip_list=interfaces_dict['IF_ADR_ESRP']['ip_list'],
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.GET, ]
        )
    )

    esrp_to_chfe_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict['IF_ESRP_CHFE']['ip'],
            dst_ip=interfaces_dict['IF_CHFE_ESRP']['ip'],
            src_ip_list=interfaces_dict['IF_ESRP_CHFE']['ip_list'],
            dst_ip_list=interfaces_dict['IF_CHFE_ESRP']['ip_list'],
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE, ]
        )
    )

    if esrp_to_chfe_request:
        esrp_emergency_call_data_list = extract_sip_header_values(esrp_to_chfe_request,
                                                                  "Call-Info",
                                                                  'purpose=EmergencyCallData')

    return (emergency_call_data_list, bcf_invite_request, esrp_get_policies_request,
            is_jws_in_response_valid, esrp_get_adr_request, esrp_emergency_call_data_list)


def get_test_names() -> list:
    return [f"Validate ESRP for retrieving Additional Data.", ]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    (emergency_call_data_list, bcf_invite_request, esrp_get_policies_request, is_jws_in_response_valid,
     esrp_get_adr_request, esrp_emergency_call_data_list) = (
        get_test_parameters(pcap_service, lab_config, filtering_options, variation))
    return [
        TestCheck(
            test_name="Validate ESRP for retrieving Additional Data.",
            test_method=validate_esrp_retrieving_additional_data,
            test_params={
                "emergency_call_data_list": emergency_call_data_list,
                "bcf_invite_request": bcf_invite_request,
                "esrp_get_policies_request": esrp_get_policies_request,
                "is_jws_in_response_valid": is_jws_in_response_valid,
                "esrp_get_adr_request": esrp_get_adr_request,
                "esrp_emergency_call_data_list": esrp_emergency_call_data_list
            }
        )
    ]
