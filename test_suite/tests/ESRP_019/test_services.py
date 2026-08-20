from dataclasses import dataclass
from pyshark.packet.packet import Packet

from services.aux_services.message_services import (
    get_messages,
    get_message_and_jws_by_event_type,
)
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import FilterMessageType
from services.messages.http.http_message import HttpMessage
from services.messages.sip.sip_message import SipMessage
from services.pcap_service import PcapCaptureService, FilterConfig
from services.config.types.lab_config import LabConfig
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.aux_services.aux_services import (
    get_first_message_matching_filter,
)
from enums import PacketTypeEnum, SIPMethodEnum, HTTPMethodEnum
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.ESRP_019.checks import (
    validate_location_query_response,
)


@dataclass
class TestData:
    stimulus_message: Packet | None = None
    stimulus_timestamp: float = None
    variation_number: int = 3


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
    other = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    out_scr_ip = None
    out_dst_ip = None
    other_src_ip = None
    other_dst_ip = None
    key_filepath = None
    iut_entity = lab_config.get_conformance_iut_entity()
    esrp_fqdn = iut_entity.get_first_available_fqdn() if iut_entity else None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS:
            stimulus = message
        elif message.message_type == FilterMessageType.OUTPUT:
            output = message
        elif message.message_type == FilterMessageType.OTHER:
            other = message

    if stimulus and output and other:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
                elif interface.name == output.src_interface:
                    key_filepath = entity.certificate_key
                    out_scr_ip = interface.ip
                elif interface.name == output.dst_interface:
                    out_dst_ip = interface.ip
                elif interface.name == other.src_interface:
                    other_src_ip = interface.ip
                elif interface.name == other.dst_interface:
                    other_dst_ip = interface.ip

        if (
            stimulus_src_ip is None
            or stimulus_dst_ip is None
            or out_scr_ip is None
            or out_dst_ip is None
            or other_src_ip is None
            or other_dst_ip is None
        ):
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required parameters for IP addresses"
            )
        elif not esrp_fqdn:
            raise WrongConfigurationError(
                "It seems that the LabConfig does not contain required FQDN records for ESRP interfaces"
            )
        else:
            return (
                stimulus_src_ip,
                stimulus_dst_ip,
                out_scr_ip,
                out_dst_ip,
                other_src_ip,
                other_dst_ip,
                key_filepath,
                esrp_fqdn,
            )
    else:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )


def get_stimulus_msg_and_ts(
    pcap_service,
    stimulus_src_ip,
    stimulus_dst_ip,
):
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

    stimulus_timestamp = getattr(stimulus_message, "sniff_timestamp", 0)

    return stimulus_message, stimulus_timestamp


def get_esrp_to_lis_http_post_msg_and_ts(
    pcap_service, other_src_ip, other_dst_ip, timestamp
):
    esrp_to_lis_http_post_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=other_src_ip,
            dst_ip=other_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
            after_timestamp=timestamp,
        ),
    )

    esrp_to_lis_http_post_message_timestamp = getattr(
        esrp_to_lis_http_post_message, "sniff_timestamp", 0
    )

    return esrp_to_lis_http_post_message, esrp_to_lis_http_post_message_timestamp


def get_esrp_to_lis_subscribe_rq_and_ts(
    pcap_service, other_src_ip, other_dst_ip, timestamp
):
    esrp_to_lis_subscribe_request = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=other_src_ip,
            dst_ip=other_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.SUBSCRIBE,
            ],
            after_timestamp=timestamp,
        ),
    )

    esrp_to_lis_subscribe_request_timestamp = getattr(
        esrp_to_lis_subscribe_request, "sniff_timestamp", 0
    )

    return esrp_to_lis_subscribe_request, esrp_to_lis_subscribe_request_timestamp


def get_lis_to_esrp_notify_response_and_ts(
    pcap_service, other_src_ip, other_dst_ip, timestamp
):
    lis_to_esrp_notify_response = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=other_dst_ip,
            dst_ip=other_src_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[
                SIPMethodEnum.NOTIFY,
            ],
            after_timestamp=timestamp,
        ),
    )

    lis_to_esrp_notify_response_timestamp = getattr(
        lis_to_esrp_notify_response, "sniff_timestamp", 0
    )

    return lis_to_esrp_notify_response, lis_to_esrp_notify_response_timestamp


def get_lis_to_esrp_http_response_message(
    pcap_service, other_src_ip, other_dst_ip, timestamp
):
    lis_to_esrp_http_response_message = get_first_message_matching_filter(
        pcap_service,
        FilterConfig(
            src_ip=other_dst_ip,
            dst_ip=other_src_ip,
            packet_type=PacketTypeEnum.HTTP,
            after_timestamp=timestamp,
        ),
    )

    return lis_to_esrp_http_response_message, None


def get_esrp_to_logger_post_location_query_msg_jws_ts(
    pcap_service, out_src_ip, out_dst_ip, timestamp, key_filepath
):
    esrp_to_logger_post_location_query_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_src_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
            after_timestamp=timestamp,
        ),
    )

    jws, message = get_message_and_jws_by_event_type(
        esrp_to_logger_post_location_query_messages,
        "LocationQueryLogEvent",
        key_filepath,
    )

    ecrf_to_logger_http_post_message_timestamp = getattr(message, "sniff_timestamp", 0)

    return jws, message, ecrf_to_logger_http_post_message_timestamp


def get_esrp_to_logger_post_location_response_msg_jws_ts(
    pcap_service, out_src_ip, out_dst_ip, timestamp, key_filepath
):
    esrp_to_logger_post_location_response_messages = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=out_src_ip,
            dst_ip=out_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[
                HTTPMethodEnum.POST,
            ],
            after_timestamp=timestamp,
        ),
    )

    jws, message = get_message_and_jws_by_event_type(
        esrp_to_logger_post_location_response_messages,
        "LocationResponseLogEvent",
        key_filepath,
    )

    return jws, message


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
    variation_number: int = 1,
):
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        out_src_ip,
        out_dst_ip,
        other_src_ip,
        other_dst_ip,
        key_filepath,
        esrp_fqdn,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    test_data = TestData()
    geolocation_raw = None
    stimulus_call_id_sip = None
    stimulus_call_id = None
    stimulus_incident_id = None
    esrp_to_lis_http_post_message_timestamp = 0
    esrp_to_lis_http_post_message_body = None
    esrp_to_lis_http_post_message = None
    lis_to_esrp_http_response_message = None
    lis_response_status_code = None
    esrp_to_logger_post_location_query_message = None
    esrp_to_logger_post_location_query_jws = None
    esrp_to_logger_post_location_response_messages = None
    esrp_to_logger_post_location_response_jws = None
    esrp_to_logger_post_location_response_message = None
    esrp_to_lis_subscribe_request = None
    esrp_to_lis_subscribe_request_timestamp = None
    esrp_to_lis_subscribe_message_body = None
    lis_to_esrp_notify_response = None
    lis_to_esrp_notify_response_message_body = None
    lis_to_esrp_response_message_body = None

    # BCF to ESRP stimulus message
    stimulus_message, stimulus_timestamp = get_stimulus_msg_and_ts(
        pcap_service, stimulus_src_ip, stimulus_dst_ip
    )
    stimulus_msg = SipMessage.from_packet(stimulus_message)

    # ESRP to LIS HTTP POST request
    if stimulus_message and stimulus_timestamp:
        esrp_to_lis_http_post_message, esrp_to_lis_http_post_message_timestamp = (
            get_esrp_to_lis_http_post_msg_and_ts(
                pcap_service, other_src_ip, other_dst_ip, stimulus_timestamp
            )
        )

    # Get body from ESRP to LIS HTTP POST request
    if esrp_to_lis_http_post_message:
        message_content = HttpMessage.from_packet(esrp_to_lis_http_post_message)
        esrp_to_lis_http_post_message_body = message_content.body

    # ESRP to LIS SUBSCRIBE request
    if stimulus_message and stimulus_timestamp:
        esrp_to_lis_subscribe_request, esrp_to_lis_subscribe_request_timestamp = (
            get_esrp_to_lis_subscribe_rq_and_ts(
                pcap_service, other_src_ip, other_dst_ip, stimulus_timestamp
            )
        )

    # Get body from ESRP to LIS SUBSCRIBE request
    if esrp_to_lis_subscribe_request:
        message_content = SipMessage.from_packet(esrp_to_lis_subscribe_request)
        esrp_to_lis_subscribe_message_body = message_content.body

    # LIS to ESRP NOTIFY response
    if esrp_to_lis_subscribe_request and esrp_to_lis_subscribe_request_timestamp:
        lis_to_esrp_notify_response, lis_to_esrp_notify_response_timestamp = (
            get_lis_to_esrp_notify_response_and_ts(
                pcap_service,
                other_src_ip,
                other_dst_ip,
                esrp_to_lis_subscribe_request_timestamp,
            )
        )

    # Get body from LIS to ESRP NOTIFY response
    if lis_to_esrp_notify_response:
        message_content = SipMessage.from_packet(lis_to_esrp_notify_response)
        lis_to_esrp_notify_response_message_body = message_content.body

    # LIS to ESRP HTTP Response
    if esrp_to_lis_http_post_message and esrp_to_lis_http_post_message_timestamp:
        lis_to_esrp_http_response_message, _ = get_lis_to_esrp_http_response_message(
            pcap_service,
            other_src_ip,
            other_dst_ip,
            esrp_to_lis_http_post_message_timestamp,
        )

    # Get body from LIS to ESRP HTTP Response
    if lis_to_esrp_http_response_message:
        message_content = HttpMessage.from_packet(lis_to_esrp_http_response_message)
        lis_to_esrp_response_message_body = message_content.body

    # Get Geolocation
    if stimulus_message:
        if stimulus_msg.geolocation:
            geolocation_raw = stimulus_msg.geolocation[0]

    # Get LIS Response Status Code
    if lis_to_esrp_http_response_message:
        lis_response_msg = HttpMessage.from_packet(lis_to_esrp_http_response_message)

        lis_response_status_code = (
            str(lis_response_msg.status_code) if lis_response_msg.status_code else ""
        )

    # Get Message and JWS of ESRP to LOG LocationQueryLogEvent
    after_timestamp = (
        esrp_to_lis_http_post_message_timestamp
        if variation_number
        in (
            1,
            3,
        )
        else esrp_to_lis_subscribe_request_timestamp
    )

    if (
        esrp_to_lis_http_post_message
        or esrp_to_lis_subscribe_request
        and (
            esrp_to_lis_http_post_message_timestamp
            or esrp_to_lis_subscribe_request_timestamp
        )
    ):

        (
            esrp_to_logger_post_location_query_jws,
            esrp_to_logger_post_location_query_message,
            ecrf_to_logger_http_post_message_timestamp,
        ) = get_esrp_to_logger_post_location_query_msg_jws_ts(
            pcap_service, out_src_ip, out_dst_ip, after_timestamp, key_filepath
        )

        # Get Message and JWS of ESRP to LOG LocationResponseLogEvent
        if (
            esrp_to_logger_post_location_query_message
            and ecrf_to_logger_http_post_message_timestamp
        ):
            (
                esrp_to_logger_post_location_response_jws,
                esrp_to_logger_post_location_response_message,
            ) = get_esrp_to_logger_post_location_response_msg_jws_ts(
                pcap_service,
                out_src_ip,
                out_dst_ip,
                esrp_to_lis_http_post_message_timestamp,
                key_filepath,
            )

    # Get Stimulus Call-ID, CallId, IncidentId
    if stimulus_message and stimulus_msg:
        stimulus_call_id_sip = stimulus_msg.call_id
        call_info = stimulus_msg.call_info
        if call_info:
            stimulus_call_id = next(
                (line for line in call_info if "CallId" in line), None
            )
            stimulus_incident_id = next(
                (line for line in call_info if "IncidentId" in line), None
            )

    test_data.variation_number = variation_number
    test_data.esrp_fqdn = esrp_fqdn
    test_data.stimulus_message = stimulus_message
    test_data.geolocation_raw = geolocation_raw
    test_data.stimulus_call_id_sip = stimulus_call_id_sip
    test_data.stimulus_call_id = stimulus_call_id
    test_data.stimulus_incident_id = stimulus_incident_id
    test_data.esrp_to_lis_http_post_message_body = esrp_to_lis_http_post_message_body
    test_data.esrp_to_lis_http_post_message = esrp_to_lis_http_post_message
    test_data.lis_to_esrp_http_response_message = lis_to_esrp_http_response_message
    test_data.lis_response_status_code = lis_response_status_code
    test_data.esrp_to_logger_post_location_query_message = (
        esrp_to_logger_post_location_query_message
    )
    test_data.esrp_to_logger_post_location_query_jws = (
        esrp_to_logger_post_location_query_jws
    )
    test_data.esrp_to_logger_post_location_response_messages = (
        esrp_to_logger_post_location_response_messages
    )
    test_data.esrp_to_logger_post_location_response_jws = (
        esrp_to_logger_post_location_response_jws
    )
    test_data.esrp_to_logger_post_location_response_message = (
        esrp_to_logger_post_location_response_message
    )
    test_data.esrp_to_lis_subscribe_request = esrp_to_lis_subscribe_request
    test_data.esrp_to_lis_subscribe_request_timestamp = (
        esrp_to_lis_subscribe_request_timestamp
    )
    test_data.esrp_to_lis_subscribe_message_body = esrp_to_lis_subscribe_message_body
    test_data.lis_to_esrp_notify_response = lis_to_esrp_notify_response
    test_data.lis_to_esrp_notify_response_message_body = (
        lis_to_esrp_notify_response_message_body
    )
    test_data.lis_to_esrp_response_message_body = lis_to_esrp_response_message_body

    return test_data


def get_test_names() -> list:
    return [
        "Verify LocationQuery/LocationResponse LogEvents after HELD dereference",
        "Verify LocationQuery/LocationResponse LogEvents after SIP Presence dereference",
        "LocationResponseLogEvent 'responseStatus' after LIS error response",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    run_variation: RunVariation,
) -> list:

    variations = {
        "HELD_location_dereferencing": 1,
        "SIP_Presence_location_dereferencing": 2,
        "LIS_response_with_error": 3,
    }

    if run_variation.name in variations:
        variation_number = variations.get(run_variation.name)
    else:
        raise VariationNotFoundError(
            f"Unknown variation name: '{run_variation.name}'\n"
            f"Expected variation names by Test Case: '{variations}'"
        )

    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, run_variation, variation_number
    )

    if variation_number == 1:

        return [
            TestCheck(
                test_name="Verify LocationQuery/LocationResponse LogEvents after HELD dereference",
                test_method=validate_location_query_response,
                test_params={
                    "test_data": test_data,
                },
            ),
        ]

    elif variation_number == 2:

        return [
            TestCheck(
                test_name="Verify LocationQuery/LocationResponse LogEvents after SIP Presence dereference",
                test_method=validate_location_query_response,
                test_params={
                    "test_data": test_data,
                },
            ),
        ]
    else:
        return [
            TestCheck(
                test_name="LocationResponseLogEvent 'responseStatus' after LIS error response",
                test_method=validate_location_query_response,
                test_params={
                    "test_data": test_data,
                },
            ),
        ]
