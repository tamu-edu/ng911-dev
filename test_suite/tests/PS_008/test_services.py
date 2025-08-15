from services.aux_services.aux_services import get_messages
from services.aux_services.json_services import get_jws_from_http_media_layer
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, HTTPMethodEnum
from services.test_services.test_assessment_service import TestCheck
from tests.PS_008.checks import validate_jws_in_http_response_from_ps


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter],
                          variation) -> tuple[str, str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :param variation: RunVariation instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, http_url),strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None
    http_url = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    for param in variation.params:
        if param == 'messages':
            http_url = variation.params[param][0].get('http_url', None)

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip
        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("Lab Config file error - src and dst ip addresses not found")
        else:
            return stimulus_src_ip, stimulus_dst_ip, http_url
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options:  list[MessageFilter], variation) -> tuple or None:
    stimulus_src_ip, stimulus_dst_ip, http_url = get_filter_parameters(lab_config, filtering_options, variation)

    http_post_request = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.HTTP,
            message_method=[HTTPMethodEnum.POST, ]
        ),
    )

    jws = ""
    if http_post_request:
        # Get the first request if multiple
        jws = get_jws_from_http_media_layer(http_post_request[0])

    http_responses = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_dst_ip,
            dst_ip=stimulus_src_ip,
            packet_type=PacketTypeEnum.HTTP,
        ),
    )
    http_response = ''
    if http_responses:
        # Get the last response with 200 OK
        http_response = [http_resp for http_resp in http_responses
                         if http_resp.http.get('response_code', None) == '200'][-1]

    return jws, http_response


def get_test_names() -> list:
    return [f"Verify if JWS objects are unaltered after fetching from Policy Store", ]


def get_test_list(pcap_service: PcapCaptureService,
                  lab_config: LabConfig,
                  filtering_options:  list[MessageFilter], variation: RunVariation) -> list:
    (
        jws_from_request, http_response
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)
    return [
        TestCheck(
            test_name="Verify if JWS objects are unaltered after fetching from Policy Store",
            test_method=validate_jws_in_http_response_from_ps,
            test_params={
                "jws_from_request": jws_from_request,
                "http_response": http_response
            }
        )
    ]
