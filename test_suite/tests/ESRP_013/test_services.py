from services.aux_services.sip_services import extract_sip_header_values
from services.config.types.run_config import MessageFilter, RunVariation

from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import get_first_message_matching_filter
from enums import PacketTypeEnum, HTTPMethodEnum, SIPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_013.checks import validate_esrp_multiple_additional_data


def get_filter_parameters(
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
    pcap_service: PcapCaptureService,
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :param pcap_service: PcapCaptureService instance
    :return: Dictionary with interfaces
    """
    interfaces_dict = {}

    for entity in lab_config.entities:
        for interface in entity.interfaces:
            port_dict = {}
            for pm in interface.port_mapping:
                port_dict[pm.name] = {
                    "protocol": pm.protocol,
                    "port": pm.port,
                    "transport_protocol": pm.transport_protocol,
                }

            interfaces_dict[interface.name] = {
                "ip": interface.ip,
                "port_mapping": port_dict,
            }

    if not interfaces_dict:
        raise WrongConfigurationError(
            "Lab Config file error - cannot extract interface data"
        )

    required_interfaces = [
        "IF_BCF_ESRP",
        "IF_ESRP_BCF",
        "IF_ESRP_ADR",
        "IF_ADR_ESRP",
        "IF_ESRP_ADR-2",
        "IF_ADR-2_ESRP",
        "IF_ESRP_ADR-3",
        "IF_ADR-3_ESRP",
        "IF_ESRP_CHFE",
        "IF_CHFE_ESRP",
    ]
    missing = [iface for iface in required_interfaces if iface not in interfaces_dict]
    if missing:
        raise WrongConfigurationError(
            f"Lab Config file error - missing required interfaces: {missing}"
        )

    return interfaces_dict


def get_http_get_request_data_for(from_address, to_address, pcap_service):
    """
    Retrieve the first HTTP GET request matching the given source and destination addresses.

    :param from_address: Source IP address to filter on
    :param to_address: Destination IP address to filter on
    :param pcap_service: PcapCaptureService instance used to query captured packets
    :return: First matching HTTP GET message, or None if not found
    """
    return get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=from_address,
            dst_ip=to_address,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.GET,
            ],
        ),
    )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    interfaces_dict = get_filter_parameters(
        lab_config, filtering_options, variation, pcap_service
    )

    init_adr_reference = None
    esrp_to_chfe_adr_reference = None

    # Filter out Test System OSP cal to ESRP
    stimulus_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_BCF_ESRP"]["ip"],
            dst_ip=interfaces_dict["IF_ESRP_BCF"]["ip"],
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
        ),
    )

    if stimulus_request:
        init_adr_reference = extract_sip_header_values(
            stimulus_request, "Call-Info", "purpose=EmergencyCallData.ProviderInfo"
        )
    esrp_to_ts_adr = get_http_get_request_data_for(
        interfaces_dict["IF_ESRP_ADR"]["ip"],
        interfaces_dict["IF_ADR_ESRP"]["ip"],
        pcap_service,
    )

    esrp_to_ts_adr2 = get_http_get_request_data_for(
        interfaces_dict["IF_ESRP_ADR-2"]["ip"],
        interfaces_dict["IF_ADR-2_ESRP"]["ip"],
        pcap_service,
    )

    esrp_to_ts_adr3 = get_http_get_request_data_for(
        interfaces_dict["IF_ESRP_ADR-3"]["ip"],
        interfaces_dict["IF_ADR-3_ESRP"]["ip"],
        pcap_service,
    )

    # Filter out ESRP to TS CHFE SIP INVITE request
    esrp_to_chfe_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=interfaces_dict["IF_ESRP_CHFE"]["ip"],
            dst_ip=interfaces_dict["IF_CHFE_ESRP"]["ip"],
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
        ),
    )

    if esrp_to_chfe_request:
        esrp_to_chfe_adr_reference = extract_sip_header_values(
            esrp_to_chfe_request, "Call-Info", "purpose=EmergencyCallData.ProviderInfo"
        )

    return (
        stimulus_request,
        init_adr_reference,
        esrp_to_ts_adr,
        esrp_to_ts_adr2,
        esrp_to_ts_adr3,
        esrp_to_chfe_adr_reference,
    )


def get_test_names() -> list:
    return [
        "Validate ESRP accommodates multiple additional data services and structures for the same call",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_request,
        init_adr_reference,
        esrp_to_ts_adr,
        esrp_to_ts_adr2,
        esrp_to_ts_adr3,
        esrp_to_chfe_adr_reference,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Validate ESRP accommodates multiple additional data services and structures for the same call",
            test_method=validate_esrp_multiple_additional_data,
            test_params={
                "stimulus_request": stimulus_request,
                "init_adr_reference": init_adr_reference,
                "esrp_to_ts_adr": esrp_to_ts_adr,
                "esrp_to_ts_adr2": esrp_to_ts_adr2,
                "esrp_to_ts_adr3": esrp_to_ts_adr3,
                "esrp_to_chfe_adr_reference": esrp_to_chfe_adr_reference,
            },
        )
    ]
