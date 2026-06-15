from checks.general.checks import is_data_present, is_test_data_the_same
from checks.http.checks import is_type
from services.aux_services.message_services import (
    get_logevent_list_by_type,
    extract_all_contents_from_message_body,
)
from services.aux_services.sip_msg_body_services import clean_up_string
from services.aux_services.sip_services import (
    extract_all_header_fields_matching_name_from_sip_message,
)
from services.aux_services.xml_services import is_valid_xml
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    get_first_message_matching_filter,
)
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Retrieve required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, out_src_ip, out_dst_ip, other_src_ip, other_dst_ip,
                    header_contains, sip_method)
    """
    stimulus = None
    output = None
    other = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_src_ip = None
    out_dst_ip = None
    other_src_ip = None
    other_dst_ip = None
    header_contains = None
    key_filepath = None
    lost_url = None
    # No response-code validation anymore

    for message in filtering_options or []:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message
            header_contains = message.header_contains
        elif message.message_type == FilterMessageType.OTHER:
            other = message

    if stimulus and output and other:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                    key_filepath = entity.certificate_key
                elif interface.name == output.src_interface:
                    out_src_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
                elif interface.name == other.src_interface:
                    other_src_ip = interface.ip
                elif interface.name == other.dst_interface:
                    other_dst_ip = interface.ip
                    if hasattr(entity, "api_http_url_prefix"):
                        lost_url = entity.api_http_url_prefix
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_src_ip is None
            or out_dst_ip is None
            or key_filepath is None
            or lost_url is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_src_ip,
                out_dst_ip,
                other_src_ip,
                other_dst_ip,
                header_contains,
                key_filepath,
                lost_url,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        header_contains,
        key_filepath,
        lost_url,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    init_call_id = None
    xml_content_from_esrp_to_ecrf = None
    xml_content_from_esrp_to_logger = None
    direction = None
    query_id = None

    stimulus_sip_messages = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.INVITE],
        ),
    )

    if stimulus_sip_messages:
        init_call_id_list = extract_all_header_fields_matching_name_from_sip_message(
            stimulus_sip_messages, "Call-ID"
        )
        if init_call_id_list:
            init_call_id = clean_up_string(init_call_id_list[0]).strip("Call-ID: ")

    esrp_to_ecrf_msg = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=other_src_ip,  # ESRP interface IP
            dst_ip=other_dst_ip,  # ECRF interface IP
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST],
            header_part=header_contains,
        ),
    )

    if esrp_to_ecrf_msg:
        for body in extract_all_contents_from_message_body(esrp_to_ecrf_msg):
            if is_valid_xml(body["body"]):
                xml_content_from_esrp_to_ecrf = clean_up_string(
                    body["body"], is_xml=True
                )

    http_post_requests_to_logger = list(
        pcap_service.get_messages_by_config(
            FilterConfig(
                src_ip=out_src_ip,  # ESRP interface IP
                dst_ip=out_dst_ip,  # LOG interface IP
                packet_type=PacketTypeEnum.HTTP,
                message_method=[HTTPMethodEnum.POST],
                header_part=lost_url,
            )
        )
    )

    if key_filepath == "":
        print(
            "⚠️ WARNING: The ESRP 'certificate_key' value is set to '' (empty line). There is a risk that message payload may not be decoded."
        )
    log_event_list = get_logevent_list_by_type(
        http_post_requests_to_logger, "LostQueryLogEvent", key_filepath, init_call_id
    )

    if log_event_list:
        xml_content_from_esrp_to_logger = clean_up_string(
            log_event_list[0].get("queryAdapter"), is_xml=True
        )

        direction = log_event_list[0].get("direction")

        query_id = log_event_list[0].get("queryId")

    return (
        xml_content_from_esrp_to_ecrf,
        xml_content_from_esrp_to_logger,
        log_event_list,
        direction,
        query_id,
    )


def get_test_names() -> list:
    return [
        "Validate ESRP sends HTTP POST 'LostQueryLogEvent' go to /LogEvents",
        "Validate ESRP send 'queryAdapter' string",
        "Validate ESRP send 'queryAdapter' string with LoST query XML data",
        "Validate 'direction' attribute value",
        "Validate 'queryId' attribute value",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        xml_content_from_esrp_to_ecrf,
        xml_content_from_esrp_to_logger,
        log_event_list,
        direction,
        query_id,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Validate ESRP sends HTTP POST 'LostQueryLogEvent' go to /LogEvents",
            test_method=is_data_present,
            test_params={
                "test_data": log_event_list,
                "error": "FAILED -> No HTTP POST 'LostQueryLogEvent' found",
            },
        ),
        TestCheck(
            test_name="Validate ESRP send 'queryAdapter' string",
            test_method=is_data_present,
            test_params={
                "test_data": xml_content_from_esrp_to_logger,
                "error": "FAILED -> No 'queryAdapter' found in JWS",
            },
        ),
        TestCheck(
            test_name="Validate ESRP send 'queryAdapter' string with LoST query XML data",
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": xml_content_from_esrp_to_ecrf,
                "actual_data": xml_content_from_esrp_to_logger,
            },
        ),
        TestCheck(
            test_name="Validate 'direction' attribute value",
            test_method=is_test_data_the_same,
            test_params={"expected_data": "outgoing", "actual_data": direction},
        ),
        TestCheck(
            test_name="Validate 'queryId' attribute value",
            test_method=is_type,
            test_params={
                "param": query_id,
                "param_name": "queryId",
                "expected_type": str,
            },
        ),
    ]
