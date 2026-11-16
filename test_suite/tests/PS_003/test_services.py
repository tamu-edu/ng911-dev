from dataclasses import dataclass
from typing import Any

from pyshark.packet.packet import Packet

from checks.general.checks import is_data_present
from services.config.config_enum import FilterMessageType
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.run_config import RunVariation, MessageFilter
from services.messages.packet_fetcher import PacketFetcher
from services.pcap_service import PcapCaptureService

from services.aux_services.message_services import (
    extract_json_data_from_http,
)
from services.test_services.test_assessment_service import TestCheck
from checks.http.checks import is_type
from tests.PS_003.constants import NOT_RUN


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple of filtering parameters (stimulus_src_ip, stimulus_dst_ip)
    """
    messages_by_type = {m.message_type: m for m in filtering_options}
    stimulus = messages_by_type.get(FilterMessageType.STIMULUS)

    if not stimulus:
        raise WrongConfigurationError(
            "It seems that the Run Config does not contain required "
            "parameters for filtering"
        )

    stimulus_endpoint = stimulus.header_contains or ""

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

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        stimulus_endpoint,
    )


def _has_major_minor(version) -> bool:
    return (
        isinstance(version, dict)
        and type(version.get("major")) is int
        and type(version.get("minor")) is int
    )


def _has_service_info(version) -> bool:
    service_info = version.get("serviceInfo") if isinstance(version, dict) else None
    algorithms = (
        service_info.get("requiredAlgorithms")
        if isinstance(service_info, dict)
        else None
    )
    return isinstance(algorithms, list) and all(isinstance(a, str) for a in algorithms)


@dataclass
class TestData:
    """
    Holds all data gathered from the pcap that is needed to run
    the test checks.
    """

    stimulus_message: Packet | None = None
    is_ps_200_response: bool = False
    has_json_body: bool = False
    has_fingerprint: bool = False
    fingerprint: Any = None
    versions: Any = None
    is_versions_non_empty_array: bool = False
    is_major_minor_valid: bool = False
    is_service_info_valid: bool = False
    has_vendor: bool = False
    is_vendor_valid: bool = False


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation,
):
    stimulus_src_ip, stimulus_dst_ip, stimulus_endpoint = get_filter_parameters(
        lab_config, filtering_options, variation
    )

    fetcher = PacketFetcher(pcap_service)
    fetcher.add_route("esrp_ps", stimulus_src_ip, stimulus_dst_ip)

    data: dict = {}

    # Get stimulus message and time stamp
    stimulus_message, stimulus_ts = fetcher.get_first_http_get(
        "esrp_ps", return_timestamp=True, url_contains=stimulus_endpoint
    )

    data["stimulus_message"] = stimulus_message
    if not stimulus_message:
        return TestData(**data)

    # Get first Policy Store response after the stimulus and extract data
    ps_response = fetcher.get_first_http_200("ps_esrp", after_timestamp=stimulus_ts)
    data["is_ps_200_response"] = bool(ps_response)
    if not ps_response:
        return TestData(**data)

    json_body = extract_json_data_from_http(ps_response)
    if not isinstance(json_body, dict):
        return TestData(**data)

    data["has_json_body"] = True
    data["has_fingerprint"] = "fingerprint" in json_body
    data["fingerprint"] = json_body.get("fingerprint")

    versions = json_body.get("versions")
    version_objects = versions if isinstance(versions, list) else []

    data["versions"] = versions
    data["is_versions_non_empty_array"] = bool(version_objects)
    data["is_major_minor_valid"] = bool(version_objects) and all(
        _has_major_minor(v) for v in version_objects
    )
    data["is_service_info_valid"] = bool(version_objects) and all(
        _has_service_info(v) for v in version_objects
    )
    versions_with_vendor = [
        v for v in version_objects if isinstance(v, dict) and "vendor" in v
    ]
    data["has_vendor"] = bool(versions_with_vendor)
    data["is_vendor_valid"] = all(
        isinstance(v["vendor"], str) for v in versions_with_vendor
    )

    return TestData(**data)


def get_test_names() -> list:
    return [
        "Verify that Policy Store responded with 200 code",
        "Verify that mandatory 'fingerprint' member is present",
        "Verify that mandatory 'fingerprint' member is a string value",
        "Verify that mandatory 'versions' member is non-empty array",
        "Verify that version objects contain integer 'major' and 'minor' members",
        "Verify that each version contains 'serviceInfo' with a 'requiredAlgorithms' string array",
        "Verify that optional 'vendor' member is a string value",
    ]


def _body_error(test_data: TestData, field_error: str) -> str:
    """Returns the reason of failure for body field checks."""
    if not test_data.is_ps_200_response:
        return "FAILED -> No Policy Store 200 OK response found"
    if not test_data.has_json_body:
        return "FAILED -> Policy Store response has no valid JSON body"
    return field_error


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    test_data = get_test_parameters(
        pcap_service, lab_config, filtering_options, variation
    )

    has_stimulus = bool(test_data.stimulus_message)

    check_list = [
        TestCheck(
            test_name="Verify that Policy Store responded with 200 code",
            test_method=is_data_present,
            precondition=has_stimulus,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_ps_200_response,
                "error": "FAILED -> No Policy Store 200 OK response found",
            },
        ),
        TestCheck(
            test_name="Verify that mandatory 'fingerprint' member is present",
            test_method=is_data_present,
            precondition=has_stimulus,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.has_fingerprint,
                "error": _body_error(
                    test_data, "FAILED -> No 'fingerprint' member found"
                ),
            },
        ),
        TestCheck(
            test_name="Verify that mandatory 'fingerprint' member is a string value",
            test_method=is_type,
            precondition=has_stimulus,
            precondition_error=NOT_RUN,
            test_params={
                "param": test_data.fingerprint,
                "param_name": "fingerprint",
                "expected_type": str,
            },
        ),
        TestCheck(
            test_name="Verify that mandatory 'versions' member is non-empty array",
            test_method=is_data_present,
            precondition=has_stimulus,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_versions_non_empty_array,
                "error": _body_error(
                    test_data,
                    f"FAILED -> 'versions' member is not a non-empty array. Found: {test_data.versions}",
                ),
            },
        ),
        TestCheck(
            test_name="Verify that version objects contain integer 'major' and 'minor' members",
            test_method=is_data_present,
            precondition=has_stimulus,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_major_minor_valid,
                "error": _body_error(
                    test_data,
                    f"FAILED -> 'major' or 'minor' members are not int or not present. Versions data: {test_data.versions}",
                ),
            },
        ),
        TestCheck(
            test_name="Verify that each version contains 'serviceInfo' with a 'requiredAlgorithms' string array",
            test_method=is_data_present,
            precondition=has_stimulus,
            precondition_error=NOT_RUN,
            test_params={
                "test_data": test_data.is_service_info_valid,
                "error": _body_error(
                    test_data,
                    f"FAILED -> 'serviceInfo' object or its 'requiredAlgorithms' string array is not present or invalid. Versions data: {test_data.versions}",
                ),
            },
        ),
    ]

    if test_data.has_vendor:
        check_list.append(
            TestCheck(
                test_name="Verify that optional 'vendor' member is a string value",
                test_method=is_data_present,
                precondition=has_stimulus,
                precondition_error=NOT_RUN,
                test_params={
                    "test_data": test_data.is_vendor_valid,
                    "error": f"FAILED -> 'vendor' member is present but is not a string. Versions data: {test_data.versions}",
                },
            )
        )

    return check_list
