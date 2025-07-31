from services.aux_services.aux_services import get_messages
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import MessageFilter, RunVariation
from services.pcap_service import PcapCaptureService, FilterConfig
from enums import PacketTypeEnum, SIPMethodEnum
from services.aux_services.sip_msg_body_services import get_json_value_from_sip_body
from services.test_services.test_assessment_service import TestCheck
from checks.general.checks import test_if_parameter_has_expected_value


def get_filter_parameters(lab_config: LabConfig, filtering_options: list[MessageFilter]) -> tuple[str, str]:
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, out_scr_ip, out_dst_ip), strings
    """
    stimulus = None
    stimulus_src_ip = None
    stimulus_dst_ip = None

    for message in filtering_options:
        if message.message_type == FilterMessageType.STIMULUS.value:
            stimulus = message

    if stimulus:
        for entity in lab_config.entities:
            for interface in entity.interfaces:
                if interface.name == stimulus.src_interface:
                    stimulus_src_ip = interface.ip
                elif interface.name == stimulus.dst_interface:
                    stimulus_dst_ip = interface.ip

        if stimulus_src_ip is None or stimulus_dst_ip is None:
            raise WrongConfigurationError("It seems that the LabConfig does not contain required parameters")
        else:
            return stimulus_src_ip, stimulus_dst_ip
    else:
        raise WrongConfigurationError("It seems that the Run Config does not contain required "
                                      "parameters for filtering")


def get_test_parameters(pcap_service: PcapCaptureService, lab_config: LabConfig,
                        filtering_options: list[MessageFilter]) -> list:
    stimulus_src_ip, stimulus_dst_ip = get_filter_parameters(lab_config, filtering_options)

    sip_notify_messages_from_esrp = get_messages(
        pcap_service,
        FilterConfig(
            src_ip=stimulus_src_ip,
            dst_ip=stimulus_dst_ip,
            packet_type=PacketTypeEnum.SIP,
            message_method=[SIPMethodEnum.NOTIFY, ]
        )
    )
    service_state_status_initial, queue_state_status_initial = "", ""
    service_state_status, queue_state_status = "", ""

    if sip_notify_messages_from_esrp:
        for sip_notify in sip_notify_messages_from_esrp:
            if hasattr(sip_notify, 'sip'):
                if ";" in sip_notify.sip.get('Event'):
                    event = sip_notify.sip.get('Event').split(";")[0]
                else:
                    event = sip_notify.sip.get('Event')
                if event == 'emergency-ServiceState':
                    state = get_json_value_from_sip_body(
                        sip_notify,
                        'application/EmergencyCallData.ServiceState+json',
                        'state'
                    )
                    if not service_state_status_initial:
                        service_state_status_initial = state
                    elif state != service_state_status_initial:
                        service_state_status = state
                elif event == 'emergency-QueueState':
                    state = get_json_value_from_sip_body(
                        sip_notify,
                        'application/EmergencyCallData.QueueState+json',
                        'state'
                    )
                    if not queue_state_status_initial:
                        queue_state_status_initial = state
                    elif state != queue_state_status_initial:
                        queue_state_status = state

    return [service_state_status_initial, service_state_status,
            queue_state_status_initial, queue_state_status]


def get_test_list(pcap_service: PcapCaptureService, lab_config: LabConfig,
                  filtering_options: list[MessageFilter], variation: RunVariation) -> list:
    (
        service_state_status_initial,
        service_state_status,
        queue_state_status_initial,
        queue_state_status
    ) = get_test_parameters(pcap_service, lab_config, filtering_options)
    return [
        TestCheck(
            test_name="Initial ServiceState=Normal",
            test_method=test_if_parameter_has_expected_value,
            test_params={
                "parameter_name": 'ServiceState',
                "parameter_value": service_state_status_initial,
                "expected_value": 'Normal'
            }
        ),
        TestCheck(
            test_name="Initial QueueState=Active",
            test_method=test_if_parameter_has_expected_value,
            test_params={
                "parameter_name": 'QueueState',
                "parameter_value": queue_state_status_initial,
                "expected_value": 'Active'
            }
        ),
        TestCheck(
            test_name="ServiceState=Down",
            test_method=test_if_parameter_has_expected_value,
            test_params={
                "parameter_name": 'ServiceState',
                "parameter_value": service_state_status,
                "expected_value": 'Down'
            }
        ),
        TestCheck(
            test_name="QueueState=Inactive",
            test_method=test_if_parameter_has_expected_value,
            test_params={
                "parameter_name": 'QueueState',
                "parameter_value": queue_state_status,
                "expected_value": 'Inactive'
            }
        )
    ]
