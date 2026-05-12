from services.aux_services.json_services import (
    get_jws_data,
)
from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
    get_messages,
    get_header_field_value,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    get_first_message_matching_filter,
)
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum, SIPStatusCodeEnum
from services.test_services.test_assessment_service import TestCheck
from tests.CHFE_009.checks import (
    validate_media_start_end_log_events,
)


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
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
    key_filepath = None

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
                    key_filepath = entity.certificate_key
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    out_scr_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_scr_ip is None
            or out_dst_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                key_filepath,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    key_found = True
    media_start_payload_data = None
    media_end_payload_data = None
    stimulus_invite_branch = None
    invite_ok_response_message = None
    invite_ok_sdp_body = None
    stimulus_timestamp = None
    bye_timestamp = None
    stimulus_call_id = None
    stimulus_incident_id = None
    stimulus_call_sip_id = None

    stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip, key_filepath = (
        get_filter_parameters(lab_config, filtering_options, variation)
    )

    stimulus_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.INVITE,
            ],
        ),
    )

    if stimulus_message and hasattr(stimulus_message, "sip"):
        stimulus_invite_branch = getattr(stimulus_message.sip, "via_branch", None)
        if hasattr(stimulus_message.sip, "Call-ID"):
            stimulus_call_sip_id = get_header_field_value(stimulus_message, "Call-ID")

        if hasattr(stimulus_message.sip, "Call-Info"):
            sip_raw = str(stimulus_message.sip)
            call_infos = []
            for line in sip_raw.splitlines():
                line = line.strip()
                if line.lower().startswith("call-info"):
                    if ":" in line:
                        call_infos.append(line.split(":", 1)[1].strip())

            stimulus_call_id, stimulus_incident_id = (call_infos + [None, None])[:2]

    if getattr(stimulus_message, "sniff_timestamp", None):
        stimulus_timestamp = float(stimulus_message.sniff_timestamp)

    chfe_invite_response_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.SIP,
            after_timestamp=stimulus_timestamp,
        ),
    )

    esrp_bye_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.BYE,
            ],
        ),
    )

    if getattr(esrp_bye_message, "sniff_timestamp", None):
        bye_timestamp = float(esrp_bye_message.sniff_timestamp)

    post_to_logger_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_scr_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
        ),
    )

    if chfe_invite_response_message and hasattr(chfe_invite_response_message, "sip"):
        response_status_code = getattr(
            chfe_invite_response_message.sip, "status_code", None
        )
        response_branch = getattr(chfe_invite_response_message.sip, "via_branch", None)

        if (
            response_status_code == str(SIPStatusCodeEnum.OK.value)
            and response_branch == stimulus_invite_branch
        ):
            invite_ok_response_message = chfe_invite_response_message

    if invite_ok_response_message:
        extract_content = extract_all_contents_from_message_body(
            invite_ok_response_message
        )
        if (
            extract_content
            and isinstance(extract_content[0], dict)
            and extract_content[0].get("body", None)
        ):
            body = extract_content[0]["body"]

            if body and isinstance(body, str):
                invite_ok_sdp_body = body

    if post_to_logger_messages:
        for message in post_to_logger_messages:
            jws, key_found = get_jws_data(message, key_filepath)
            if media_start_payload_data is None and any(
                x in str(jws) for x in ("MediaStartLogEvent", "sdp")
            ):
                media_start_payload_data = jws

            elif media_end_payload_data is None and any(
                x in str(jws) for x in ("MediaEndLogEvent", "mediaQualityStats")
            ):
                media_end_payload_data = jws

            if media_start_payload_data and media_end_payload_data:
                break

    return (
        stimulus_message,
        invite_ok_response_message,
        esrp_bye_message,
        key_found,
        media_start_payload_data,
        media_end_payload_data,
        post_to_logger_messages,
        stimulus_timestamp,
        bye_timestamp,
        invite_ok_sdp_body,
        stimulus_call_id,
        stimulus_incident_id,
        stimulus_call_sip_id,
    )


def get_test_names() -> list:
    return ["Verify logging of MediaStartLogEvent and MediaEndLogEvent"]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    (
        stimulus_message,
        invite_ok_response_message,
        esrp_bye_message,
        key_found,
        media_start_payload_data,
        media_end_payload_data,
        post_to_logger_messages,
        stimulus_timestamp,
        bye_timestamp,
        invite_ok_sdp_body,
        stimulus_call_id,
        stimulus_incident_id,
        stimulus_call_sip_id,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    return [
        TestCheck(
            test_name="Verify logging of MediaStartLogEvent and MediaEndLogEvent",
            test_method=validate_media_start_end_log_events,
            test_params={
                "stimulus_message": stimulus_message,
                "invite_ok_response_message": invite_ok_response_message,
                "esrp_bye_message": esrp_bye_message,
                "key_found": key_found,
                "post_to_logger_messages": post_to_logger_messages,
                "media_start_payload_data": media_start_payload_data,
                "media_end_payload_data": media_end_payload_data,
                "stimulus_timestamp": stimulus_timestamp,
                "bye_timestamp": bye_timestamp,
                "invite_ok_sdp_body": invite_ok_sdp_body,
                "stimulus_call_id": stimulus_call_id,
                "stimulus_incident_id": stimulus_incident_id,
                "stimulus_call_sip_id": stimulus_call_sip_id,
            },
        ),
    ]
