from dataclasses import dataclass
from typing import Optional, Any

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present, is_test_data_the_same
from services.aux_services.aux_services import is_valid_timestamp
from services.aux_services.json_services import is_valid_fqdn
from services.aux_services.message_services import extract_json_data_from_http
from services.aux_services.sip_msg_body_services import is_valid_sip_uri
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation, MessageFilter
from services.messages.http.http_message import HttpMessage
from services.messages.packet_fetcher import PacketFetcher
from services.pcap_service import PcapCaptureService

from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from checks.http.checks import validate_response_code_class
from tests.PS_013.constants import (
    NOT_RUN,
    NO_PS_RESPONSE,
    POLICY_ENUM_REQUIRED_MEMBERS,
    POLICY_ENUMS,
    POLICY_TYPES,
    VARIATIONS,
)


def get_filter_parameters(
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip, expected_code)
    """
    messages_by_type = {m.message_type: m for m in filtering_options or []}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)

    if not stimulus:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    expected_code = stimulus.response_status_code
    if not expected_code:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "response_status_code value"
        )

    ip_by_interface_name = {}
    for entity in lab_config.entities:
        for interface in entity.interfaces:
            ip_by_interface_name[interface.name] = interface.ip

    stimulus_src_ip = ip_by_interface_name.get(stimulus.src_interface)
    stimulus_dst_ip = ip_by_interface_name.get(stimulus.dst_interface)

    required_ips = (
        stimulus_src_ip,
        stimulus_dst_ip,
    )
    if None in required_ips:
        raise WrongConfigurationError(
            "It seems that the LabConfig does not contain required parameters for IP addresses"
        )

    return stimulus_src_ip, stimulus_dst_ip, expected_code


def _is_int(value) -> bool:
    return type(value) is int


def _is_fqdn_or_uri_with_fqdn(value) -> bool:
    """Is FQDN or URI with FQDN"""
    if not isinstance(value, str):
        return False
    return is_valid_fqdn(value.rsplit("@", 1)[-1])


def _is_policy_id_valid(policy_enum: dict) -> bool:
    """If policyId is present, it is a string and MUST be provided for OtherRoutePolicy."""
    if "policyId" in policy_enum:
        return isinstance(policy_enum["policyId"], str)
    return policy_enum.get("policyType") != "OtherRoutePolicy"


def _is_policy_queue_name_valid(policy_enum: dict) -> bool:
    """If policyQueueName is present, it is a SIP URI and MUST be provided for NormalNextHopRoutePolicy."""
    if "policyQueueName" in policy_enum:
        queue_name = policy_enum["policyQueueName"]
        return isinstance(queue_name, str) and is_valid_sip_uri(queue_name)
    return policy_enum.get("policyType") != "NormalNextHopRoutePolicy"


def _get_variation_number(variation: RunVariation) -> int:
    variation_number = VARIATIONS.get(variation.name)
    if variation_number is None:
        raise VariationNotFoundError(
            f"Unknown variation name: '{variation.name}'\n"
            f"Expected variation names by Test Case: '{VARIATIONS}'"
        )
    return variation_number


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Optional[Packet] = None
    ps_response: Optional[Packet] = None
    ps_response_code: Optional[str] = None
    expected_code: Optional[str] = None
    has_json_body: bool = False
    count: Any = None
    total_count: Any = None
    policy_enums: Any = None
    policy_enums_len: Optional[int] = None
    is_count_int: bool = False
    is_total_count_valid: bool = False
    is_policy_enums_array: bool = False
    is_policy_enum_objects: bool = False
    is_policy_type_valid: bool = False
    is_policy_owner_valid: bool = False
    is_policy_id_valid: bool = False
    is_policy_queue_name_valid: bool = False
    is_expiration_time_valid: bool = False
    is_last_modification_time_valid: bool = False


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation_number: int,
) -> TestData:
    stimulus_src_ip, stimulus_dst_ip, expected_code = get_filter_parameters(
        lab_config, filtering_options
    )

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_ps", stimulus_src_ip, stimulus_dst_ip)

    data: dict = {"expected_code": expected_code}

    stimulus_message = fetcher.get_first_http("esrp_ps", url_contains=POLICY_ENUMS)
    data["stimulus_message"] = stimulus_message
    if not stimulus_message:
        return TestData(**data)

    # Policy Store response to the stimulus request
    ps_response = fetcher.get_http_response_for("ps_esrp", stimulus_message)
    data["ps_response"] = ps_response
    if not ps_response:
        return TestData(**data)

    ps_msg = HttpMessage.from_packet(ps_response)
    data["ps_response_code"] = str(ps_msg.status_code) if ps_msg else None

    # JSON body is validated only for the variation #1
    if variation_number != 1:
        return TestData(**data)

    json_body = extract_json_data_from_http(ps_response)
    if not isinstance(json_body, dict):
        return TestData(**data)

    data["has_json_body"] = True

    count = data["count"] = json_body.get("count")
    total_count = data["total_count"] = json_body.get("totalCount")
    policy_enums = data["policy_enums"] = json_body.get("policyEnums")

    is_policy_enums_list = isinstance(policy_enums, list)
    enum_objects = policy_enums if is_policy_enums_list else []
    data["policy_enums_len"] = len(policy_enums) if is_policy_enums_list else None

    data["is_count_int"] = _is_int(count)
    # Compared with 'count' only when 'count' is valid
    data["is_total_count_valid"] = _is_int(total_count) and (
        not _is_int(count) or total_count >= count
    )
    data["is_policy_enums_array"] = isinstance(policy_enums, list) and all(
        isinstance(item, dict) for item in policy_enums
    )

    def all_enums(check) -> bool:
        """True if policyEnums is an array of objects and every object passes the check."""
        return data["is_policy_enums_array"] and all(
            check(item) for item in enum_objects
        )

    data["is_policy_enum_objects"] = all_enums(
        lambda item: all(member in item for member in POLICY_ENUM_REQUIRED_MEMBERS)
    )
    data["is_policy_type_valid"] = all_enums(
        lambda item: item.get("policyType") in POLICY_TYPES
    )
    data["is_policy_owner_valid"] = all_enums(
        lambda item: _is_fqdn_or_uri_with_fqdn(item.get("policyOwner"))
    )
    data["is_policy_id_valid"] = all_enums(_is_policy_id_valid)
    data["is_policy_queue_name_valid"] = all_enums(_is_policy_queue_name_valid)
    data["is_expiration_time_valid"] = all_enums(
        lambda item: isinstance(item.get("policyExpirationTime"), str)
        and is_valid_timestamp(item["policyExpirationTime"])
    )
    data["is_last_modification_time_valid"] = all_enums(
        lambda item: isinstance(item.get("policyLastModificationTime"), str)
        and is_valid_timestamp(item["policyLastModificationTime"])
    )

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Verify that Policy Store response is present",
        "Verify that Policy Store responded with 4xx code",
        "Verify that Policy Store responded with 200 code",
        "Verify that mandatory 'count' member is an integer",
        "Verify that mandatory 'totalCount' member is an integer greater than or equal to 'count'",
        "Verify that mandatory 'policyEnums' member is an array of objects",
        "Verify that 'policyEnums' contains 'count' PolicyEnum objects",
        "Verify that each 'policyEnums' item is a PolicyEnum object with all mandatory members",
        "Verify that each PolicyEnum 'policyType' is a value from the Policy Types registry",
        "Verify that each PolicyEnum 'policyOwner' is an FQDN or URI with FQDN",
        "Verify that each PolicyEnum 'policyExpirationTime' has a valid date-time format",
        "Verify that each PolicyEnum 'policyLastModificationTime' has a valid date-time format",
        "Verify that PolicyEnum 'policyId' is a string and present for 'OtherRoutePolicy'",
        "Verify that PolicyEnum 'policyQueueName' is a SIP URI and present for 'NormalNextHopRoutePolicy'",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    variation_number = _get_variation_number(variation)
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation_number
    )

    has_stimulus = bool(test_data.stimulus_message)
    has_response = has_stimulus and bool(test_data.ps_response)
    stimulus_precondition = {
        "precondition": has_stimulus,
        "precondition_error": NOT_RUN,
    }

    # Response code checks: FAILED with reason if there is no response
    response_precondition = {
        "precondition": has_response,
        "precondition_error": NOT_RUN if not has_stimulus else NO_PS_RESPONSE,
    }

    # JSON body checks: FAILED with reason if there is no response or no JSON body
    has_json = has_response and test_data.has_json_body
    if not has_stimulus:
        json_precondition_error = NOT_RUN
    elif not test_data.ps_response:
        json_precondition_error = NO_PS_RESPONSE
    else:
        json_precondition_error = (
            "FAILED -> Policy Store response has no valid JSON body"
        )
    json_check = {
        "test_method": is_data_present,
        "precondition": has_json,
        "precondition_error": json_precondition_error,
    }

    # 'policyEnums' size vs 'count': FAILED with reason if either cannot be compared
    if not has_json:
        count_match_error = json_precondition_error
    elif not test_data.is_count_int:
        count_match_error = (
            "FAILED -> 'count' is not an integer, 'policyEnums' size cannot be compared"
        )
    else:
        count_match_error = "FAILED -> 'policyEnums' is not an array, its size cannot be compared with 'count'"
    count_match_check = {
        "test_method": is_data_present,
        "precondition": has_json
        and test_data.is_count_int
        and test_data.is_policy_enums_array,
        "precondition_error": count_match_error,
    }

    # PolicyEnum object checks: FAILED with reason if there are no objects to verify.
    # An empty 'policyEnums' is valid only when 'count' is 0
    has_enum_objects_to_verify = test_data.is_policy_enums_array and (
        bool(test_data.policy_enums_len) or test_data.count == 0
    )
    if not has_json:
        enum_precondition_error = json_precondition_error
    elif not test_data.is_policy_enums_array:
        enum_precondition_error = "FAILED -> 'policyEnums' is not an array of objects, PolicyEnum members cannot be verified"
    else:
        enum_precondition_error = (
            "FAILED -> 'policyEnums' is empty, no PolicyEnum objects to verify. "
            f"count={test_data.count!r}"
        )
    enum_check = {
        "test_method": is_data_present,
        "precondition": has_json and has_enum_objects_to_verify,
        "precondition_error": enum_precondition_error,
    }

    policy_enums_data = f"policyEnums: {test_data.policy_enums}"

    # Optional PolicyEnum members: checked only when present or mandatory for the policyType
    enum_objects = (
        [item for item in test_data.policy_enums if isinstance(item, dict)]
        if isinstance(test_data.policy_enums, list)
        else []
    )
    has_policy_id_to_check = any(
        "policyId" in item or item.get("policyType") == "OtherRoutePolicy"
        for item in enum_objects
    )
    has_policy_queue_name_to_check = any(
        "policyQueueName" in item
        or item.get("policyType") == "NormalNextHopRoutePolicy"
        for item in enum_objects
    )

    check_list = [
        TestCheck(
            test_name="Verify that Policy Store response is present",
            test_method=is_data_present,
            **stimulus_precondition,
            test_params={
                "test_data": test_data.ps_response,
                "error": NO_PS_RESPONSE,
            },
        ),
    ]

    if variation_number != 1:
        check_list.append(
            TestCheck(
                test_name="Verify that Policy Store responded with 4xx code",
                test_method=validate_response_code_class,
                **response_precondition,
                test_params={
                    "expected_response_code_class": test_data.expected_code,
                    "response_code": test_data.ps_response_code,
                },
            )
        )
        return check_list

    check_list.extend(
        [
            TestCheck(
                test_name="Verify that Policy Store responded with 200 code",
                test_method=is_test_data_the_same,
                **response_precondition,
                test_params={
                    "expected_data": test_data.expected_code,
                    "actual_data": test_data.ps_response_code,
                },
            ),
            TestCheck(
                test_name="Verify that mandatory 'count' member is an integer",
                **json_check,
                test_params={
                    "test_data": test_data.is_count_int,
                    "error": (
                        "FAILED -> 'count' member is not an integer or not present. "
                        f"Actual: {test_data.count!r}"
                    ),
                },
            ),
            TestCheck(
                test_name="Verify that mandatory 'totalCount' member is an integer greater than or equal to 'count'",
                **json_check,
                test_params={
                    "test_data": test_data.is_total_count_valid,
                    "error": (
                        "FAILED -> 'totalCount' member is not an integer, not present or less than 'count'. "
                        f"Actual: totalCount={test_data.total_count!r}, count={test_data.count!r}"
                    ),
                },
            ),
            TestCheck(
                test_name="Verify that mandatory 'policyEnums' member is an array of objects",
                **json_check,
                test_params={
                    "test_data": test_data.is_policy_enums_array,
                    "error": f"FAILED -> 'policyEnums' member is not an array of objects. {policy_enums_data}",
                },
            ),
            TestCheck(
                test_name="Verify that 'policyEnums' contains 'count' PolicyEnum objects",
                **count_match_check,
                test_params={
                    "test_data": test_data.policy_enums_len == test_data.count,
                    "error": (
                        "FAILED -> Number of PolicyEnum objects in 'policyEnums' does not match 'count'. "
                        f"Actual: {test_data.policy_enums_len} objects, count={test_data.count!r}"
                    ),
                },
            ),
            TestCheck(
                test_name="Verify that each 'policyEnums' item is a PolicyEnum object with all mandatory members",
                **enum_check,
                test_params={
                    "test_data": test_data.is_policy_enum_objects,
                    "error": (
                        "FAILED -> 'policyEnums' contains an object without mandatory PolicyEnum members "
                        f"{list(POLICY_ENUM_REQUIRED_MEMBERS)}. {policy_enums_data}"
                    ),
                },
            ),
            TestCheck(
                test_name="Verify that each PolicyEnum 'policyType' is a value from the Policy Types registry",
                **enum_check,
                test_params={
                    "test_data": test_data.is_policy_type_valid,
                    "error": f"FAILED -> 'policyType' is not present or not in the Policy Types registry. {policy_enums_data}",
                },
            ),
            TestCheck(
                test_name="Verify that each PolicyEnum 'policyOwner' is an FQDN or URI with FQDN",
                **enum_check,
                test_params={
                    "test_data": test_data.is_policy_owner_valid,
                    "error": f"FAILED -> 'policyOwner' is not present or not an FQDN or URI with FQDN. {policy_enums_data}",
                },
            ),
            TestCheck(
                test_name="Verify that each PolicyEnum 'policyExpirationTime' has a valid date-time format",
                **enum_check,
                test_params={
                    "test_data": test_data.is_expiration_time_valid,
                    "error": f"FAILED -> 'policyExpirationTime' is not present or has an invalid date-time format. {policy_enums_data}",
                },
            ),
            TestCheck(
                test_name="Verify that each PolicyEnum 'policyLastModificationTime' has a valid date-time format",
                **enum_check,
                test_params={
                    "test_data": test_data.is_last_modification_time_valid,
                    "error": f"FAILED -> 'policyLastModificationTime' is not present or has an invalid date-time format. {policy_enums_data}",
                },
            ),
        ]
    )

    # Optional members: added only when present
    if has_policy_id_to_check:
        check_list.append(
            TestCheck(
                test_name="Verify that PolicyEnum 'policyId' is a string and present for 'OtherRoutePolicy'",
                **enum_check,
                test_params={
                    "test_data": test_data.is_policy_id_valid,
                    "error": f"FAILED -> 'policyId' is not a string or missing for 'OtherRoutePolicy'. {policy_enums_data}",
                },
            )
        )

    if has_policy_queue_name_to_check:
        check_list.append(
            TestCheck(
                test_name="Verify that PolicyEnum 'policyQueueName' is a SIP URI and present for 'NormalNextHopRoutePolicy'",
                **enum_check,
                test_params={
                    "test_data": test_data.is_policy_queue_name_valid,
                    "error": f"FAILED -> 'policyQueueName' is not a SIP URI or missing for 'NormalNextHopRoutePolicy'. {policy_enums_data}",
                },
            )
        )

    return check_list
