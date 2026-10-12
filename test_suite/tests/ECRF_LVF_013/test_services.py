from typing import Optional

from checks.general.checks import (
    check_each_element,
    is_data_present,
    is_test_data_the_same,
    is_data_absent,
)
from checks.http.checks import validate_response_code

from services.aux_services.message_services import (
    extract_all_contents_from_message_body,
)
from services.aux_services.xml_services import EasyXML, is_valid_xml
from services.config.types.run_config import MessageFilter, RunVariation
from services.config.config_enum import EntityFunction
from services.pcap_service import PcapCaptureService
from services.config.types.lab_config import LabConfig
from services.messages.packet_fetcher import PacketFetcher
from services.stub_server.enums import StubServerRole
from services.test_services.errors.var_not_found_error import VariationNotFoundError
from services.test_services.test_assessment_service import TestCheck
from tests.ECRF_LVF_013.checks import (
    extract_path_block,
    extract_via_sources,
    validate_via_source_format,
)
from tests.ECRF_LVF_013.constants import (
    VARIATION_AUTHORITATIVE_VIA,
    VARIATION_LOOP_NEXT_HOP_VIA,
    VARIATION_LOOP_OWN_VIA,
    VARIATION_RECURSIVE_VIA,
)
from tests.ECRF_LVF_013.variations.param_filter_authoritative import (
    get_filter_parameters_authoritative,
)
from tests.ECRF_LVF_013.variations.param_filter_loop import (
    get_filter_parameters_loop,
)


def get_entity_fqdns(lab_config: LabConfig):
    """
    Method to retrieve FQDNs of the ECRF-LVF (IUT) and of the Test System ECRF-LVF
    acting as a downstream authoritative LoST server
    :param lab_config: LabConfig instance
    :return: Tuple (ecrf_fqdn, ts_ecrf_fqdn)
    """
    ecrf_fqdn = None
    ts_ecrf_fqdn = None

    for entity in lab_config.entities:
        if entity.function != EntityFunction.ECRF_LVF:
            continue
        if StubServerRole.IUT in (entity.role or []):
            ecrf_fqdn = entity.get_first_available_fqdn()
        elif StubServerRole.RECEIVER in (entity.role or []):
            ts_ecrf_fqdn = entity.get_first_available_fqdn()

    return ecrf_fqdn, ts_ecrf_fqdn


def get_expected_response_code(variation: RunVariation) -> Optional[str]:
    """
    Method to retrieve the expected HTTP response code configured for the variation
    :param variation: RunVariation instance
    :return: expected response code as a string or None if not configured
    """
    expected_response_code = None

    if "messages" in getattr(variation, "params", []):
        for message_data in variation.params.values():
            for record in message_data:
                config_response_code = record.get("response_code", None)
                if config_response_code and not expected_response_code:
                    expected_response_code = (
                        config_response_code[0]
                        if isinstance(config_response_code, list)
                        else config_response_code
                    )

    return expected_response_code


def get_filter_parameters(
    lab_config: LabConfig, filtering_options: list[MessageFilter], variation
):
    """
    Method to retrieve all required filtering params to work with the pcap file.
    Dispatches to the per-variation filter module: variations with a configured
    'output' filtering option (authoritative/recursive) use one IP-lookup shape,
    while loop detection variations - which have none - use another.
    :param filtering_options: list of MessageFilter
    :param variation: RunVariation
    :param lab_config: LabConfig instance
    :return: Tuple (stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip, expected_response_code)
    """
    if variation.name in (VARIATION_AUTHORITATIVE_VIA, VARIATION_RECURSIVE_VIA):
        stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip = (
            get_filter_parameters_authoritative(lab_config, filtering_options)
        )
    elif variation.name in (VARIATION_LOOP_OWN_VIA, VARIATION_LOOP_NEXT_HOP_VIA):
        stimulus_src_ip, stimulus_dst_ip, output_src_ip, output_dst_ip = (
            get_filter_parameters_loop(lab_config, filtering_options)
        )
    else:
        raise VariationNotFoundError(f"Unknown variation name: '{variation.name}'")

    return (
        stimulus_src_ip,
        stimulus_dst_ip,
        output_src_ip,
        output_dst_ip,
        get_expected_response_code(variation),
    )


def get_message_body(message) -> Optional[str]:
    """
    Extracts XML body from an HTTP message. Falls back to the raw 'file_data'
    payload when the body cannot be split by the Content-Type header.
    :param message: HTTP message
    :return: message body as a string or None if not found
    """
    if not message or not getattr(getattr(message, "http", None), "file_data", None):
        return None

    message_content = extract_all_contents_from_message_body(message)
    if message_content:
        return message_content[0].get("body", "")

    raw_data = message.http.file_data
    if raw_data.strip().startswith("<"):
        return raw_data
    try:
        return bytes.fromhex(raw_data.replace(":", "")).decode("utf-8")
    except ValueError:
        return None


def get_test_parameters(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
):
    """
    Extract every field a TestCheck may need from the pcap.

    Returns a namespaced tuple - each caller kwarg lines up with exactly one
    named local so ``get_test_list`` can hand each TestCheck only the values
    it validates.
    """
    (
        stimulus_src_ip,
        stimulus_dst_ip,
        output_src_ip,
        output_dst_ip,
        expected_response_code,
    ) = get_filter_parameters(lab_config, filtering_options, variation)

    ecrf_fqdn, ts_ecrf_fqdn = get_entity_fqdns(lab_config)

    stimulus_via_sources = []
    response_message = None
    response_code = None
    response_xml = None
    response_find_service_response = False
    response_errors_node = False
    response_errors_source = None
    response_loop_node = False
    response_path_block = ""
    response_via_sources = []
    forwarded_request_message = None
    forwarded_path_block = ""
    forwarded_via_sources = []
    downstream_path_block = ""

    fetcher = PacketFetcher(pcap_service)

    fetcher.add_route("esrp_ecrf-lvf", stimulus_src_ip, stimulus_dst_ip)

    # 1) Stimulus: ESRP -> ECRF-LVF findService HTTP POST
    stimulus_message, stimulus_timestamp = fetcher.get_first_http_post(
        "esrp_ecrf-lvf", return_timestamp=True
    )

    if stimulus_message:
        stimulus_via_sources = extract_via_sources(get_message_body(stimulus_message))

        # 2) Response: ECRF-LVF -> ESRP findServiceResponse or errors
        response_message = fetcher.get_first_http(
            "ecrf-lvf_esrp", after_timestamp=stimulus_timestamp
        )
        if response_message and hasattr(response_message, "http"):
            response_code = getattr(response_message.http, "response_code", None)
            response_xml = get_message_body(response_message)

        if isinstance(response_xml, str):
            xml_resp = EasyXML(response_xml)
            response_find_service_response = bool(xml_resp.findServiceResponse)
            response_errors_node = xml_resp.errors_node
            response_errors_source = xml_resp.source or None
            response_loop_node = xml_resp.loop_node
            response_path_block = extract_path_block(response_xml)
            response_via_sources = extract_via_sources(response_xml)

        # 3) Recursive query: ECRF-LVF -> Test System ECRF-LVF and its response back
        if output_src_ip and output_dst_ip:
            fetcher.add_route("ecrf-lvf_ts-ecrf-lvf", output_src_ip, output_dst_ip)

            forwarded_request_message, forwarded_request_ts = (
                fetcher.get_first_http_post(
                    "ecrf-lvf_ts-ecrf-lvf",
                    after_timestamp=stimulus_timestamp,
                    return_timestamp=True,
                )
            )
            if forwarded_request_message:
                forwarded_request_xml = get_message_body(forwarded_request_message)
                forwarded_path_block = extract_path_block(forwarded_request_xml)
                forwarded_via_sources = extract_via_sources(forwarded_request_xml)

                downstream_response_message = fetcher.get_first_http(
                    "ts-ecrf-lvf_ecrf-lvf", after_timestamp=forwarded_request_ts
                )
                downstream_path_block = extract_path_block(
                    get_message_body(downstream_response_message)
                )

    return (
        stimulus_message,
        stimulus_via_sources,
        expected_response_code,
        response_message,
        response_code,
        response_xml,
        response_find_service_response,
        response_errors_node,
        response_errors_source,
        response_loop_node,
        response_path_block,
        response_via_sources,
        forwarded_request_message,
        forwarded_path_block,
        forwarded_via_sources,
        downstream_path_block,
        ecrf_fqdn,
        ts_ecrf_fqdn,
    )


def get_test_names() -> list:
    return [
        # Checks shared by all variations - the response and its HTTP response code
        "Validate ECRF-LVF response is received by ESRP",
        "Validate ECRF-LVF to ESRP response code",
        # Variations 1 and 2 - <path>/<via> elements of the <findServiceResponse>
        "Validate 'findServiceResponse' element is present in the ECRF-LVF response",
        "Validate no 'errors' element in the ECRF-LVF 'findServiceResponse'",
        "Validate 'path' element is present in the ECRF-LVF 'findServiceResponse'",
        "Validate 'path' element of the ECRF-LVF 'findServiceResponse' contains expected number of 'via' elements",
        "Validate 'via' sources of the ECRF-LVF 'findServiceResponse' 'path' element match expected FQDNs in expected order",
        "Validate 'via' sources of the ECRF-LVF 'findServiceResponse' conform to the 'appUniqueString' pattern",
        # Variation 2
        "Validate recursive 'findService' request is forwarded to Test System ECRF-LVF",
        "Validate 'path' element is present in the forwarded recursive 'findService' request",
        "Validate 'via' source of the forwarded recursive 'findService' request equals the ECRF-LVF FQDN",
        "Validate 'path' element is present in the Test System ECRF-LVF 'findServiceResponse'",
        "Validate 'path' element returned to the ESRP is 'byte-for-byte' identical to the 'path' element received from Test System ECRF-LVF",
        # Variations 3 and 4
        "Validate no 'findServiceResponse' element in the ECRF-LVF response",
        "Validate 'errors' element is present in the ECRF-LVF response",
        "Validate 'loop' element is present in the ECRF-LVF 'errors' response",
        "Validate 'source' of the 'errors' response equals the ECRF-LVF FQDN",
        "Validate 'findService' request is NOT forwarded to Test System ECRF-LVF",
    ]


def get_test_list(
    pcap_service: PcapCaptureService,
    lab_config: LabConfig,
    filtering_options: list[MessageFilter],
    variation: RunVariation,
) -> list:
    variations = [
        VARIATION_AUTHORITATIVE_VIA,
        VARIATION_RECURSIVE_VIA,
        VARIATION_LOOP_OWN_VIA,
        VARIATION_LOOP_NEXT_HOP_VIA,
    ]
    if variation.name not in variations:
        raise VariationNotFoundError(
            f"Unknown variation name: '{variation.name}'\n"
            f"Expected variation names by Test Case: '{variations}'"
        )

    (
        stimulus_message,
        stimulus_via_sources,
        expected_response_code,
        response_message,
        response_code,
        response_xml,
        response_find_service_response,
        response_errors_node,
        response_errors_source,
        response_loop_node,
        response_path_block,
        response_via_sources,
        forwarded_request_message,
        forwarded_path_block,
        forwarded_via_sources,
        downstream_path_block,
        ecrf_fqdn,
        ts_ecrf_fqdn,
    ) = get_test_parameters(pcap_service, lab_config, filtering_options, variation)

    is_loop_variation = variation.name in (
        VARIATION_LOOP_OWN_VIA,
        VARIATION_LOOP_NEXT_HOP_VIA,
    )

    # An authoritative response carries the ECRF-LVF own 'via' only, while a recursive
    # one carries the 'via' of the downstream Test System ECRF-LVF as well. Expected
    # 'via' sources define both the number of the expected 'via' elements and their order
    expected_via_sources = (
        [ecrf_fqdn]
        if variation.name == VARIATION_AUTHORITATIVE_VIA
        else [ecrf_fqdn, ts_ecrf_fqdn]
    )

    # Checks shared by all variations - the response and its HTTP response code
    checks = [
        TestCheck(
            test_name="Validate ECRF-LVF response is received by ESRP",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus 'findService' request found",
            test_method=is_data_present,
            test_params={
                "test_data": response_message,
                "error": "FAILED -> No ECRF-LVF to ESRP response found.",
            },
        ),
        TestCheck(
            test_name="Validate ECRF-LVF to ESRP response code",
            precondition=all([stimulus_message, response_message]),
            precondition_error="NOT RUN -> No ECRF-LVF to ESRP response found",
            test_method=validate_response_code,
            test_params={
                "expected_response_code": expected_response_code,
                "response_code": response_code,
            },
        ),
    ]

    if is_loop_variation:
        # Variations 3 and 4 - an <errors> response with a <loop> element is expected
        # instead of a <findServiceResponse> and no recursive query is allowed
        checks += [
            TestCheck(
                test_name="Validate no 'findServiceResponse' element in the ECRF-LVF response",
                precondition=all(
                    [stimulus_message, stimulus_via_sources, response_xml]
                ),
                precondition_error=(
                    "NOT RUN -> No stimulus 'findService' request found"
                    if not stimulus_message
                    else (
                        "NOT RUN -> Stimulus 'findService' request doesn't contain a 'path' element with 'via' elements"
                        if not stimulus_via_sources
                        else "NOT RUN -> No XML body in the ECRF-LVF to ESRP response"
                    )
                ),
                test_method=is_data_absent,
                test_params={
                    "test_data": response_find_service_response,
                    "error": (
                        "FAILED -> ECRF-LVF returned a 'findServiceResponse' instead "
                        f"of an 'errors' response.\n{response_xml}"
                    ),
                },
            ),
            TestCheck(
                test_name="Validate 'errors' element is present in the ECRF-LVF response",
                precondition=stimulus_message and stimulus_via_sources and response_xml,
                precondition_error=(
                    "NOT RUN -> No stimulus 'findService' request found"
                    if not stimulus_message
                    else (
                        "NOT RUN -> Stimulus 'findService' request doesn't contain a 'path' element with 'via' elements"
                        if not stimulus_via_sources
                        else "NOT RUN -> No XML body in the ECRF-LVF to ESRP response"
                    )
                ),
                test_method=is_data_present,
                test_params={
                    "test_data": response_errors_node,
                    "error": (
                        "FAILED -> No 'errors' element in the ECRF-LVF response.\n"
                        f"{response_xml}"
                    ),
                },
            ),
            TestCheck(
                test_name="Validate 'loop' element is present in the ECRF-LVF 'errors' response",
                precondition=stimulus_message,
                precondition_error="NOT RUN -> No stimulus 'findService' request found",
                test_method=is_data_present,
                test_params={
                    "test_data": response_loop_node,
                    "error": (
                        "FAILED -> No 'loop' element in the ECRF-LVF 'errors' "
                        f"response.\n{response_errors_node}"
                    ),
                },
            ),
            TestCheck(
                test_name="Validate 'source' of the 'errors' response equals the ECRF-LVF FQDN",
                precondition=stimulus_message,
                precondition_error="NOT RUN -> No stimulus 'findService' request found",
                test_method=is_test_data_the_same,
                test_params={
                    "expected_data": ecrf_fqdn,
                    "actual_data": response_errors_source,
                    "error": (
                        "'source' of the 'errors' response doesn't match "
                        "the ECRF-LVF FQDN"
                    ),
                },
            ),
            TestCheck(
                test_name="Validate 'findService' request is NOT forwarded to Test System ECRF-LVF",
                precondition=all(
                    [stimulus_message, stimulus_via_sources, response_message]
                ),
                precondition_error=(
                    "NOT RUN -> No stimulus 'findService' request found"
                    if not stimulus_message
                    else (
                        "NOT RUN -> Stimulus 'findService' request doesn't contain a 'path' element with 'via' elements"
                        if not stimulus_via_sources
                        else "NOT RUN -> No ECRF-LVF to ESRP response found"
                    )
                ),
                test_method=is_data_absent,
                test_params={
                    "test_data": forwarded_request_message,
                    "error": (
                        "FAILED -> ECRF-LVF forwarded the 'findService' request to "
                        "Test System ECRF-LVF instead of reporting a loop."
                    ),
                },
            ),
        ]

        return checks

    # Variations 1 and 2 - <path>/<via> elements of the <findServiceResponse>
    checks += [
        TestCheck(
            test_name="Validate 'findServiceResponse' element is present in the ECRF-LVF response",
            precondition=stimulus_message,
            precondition_error="NOT RUN -> No stimulus 'findService' request found",
            test_method=is_data_present,
            test_params={
                "test_data": response_find_service_response,
                "error": (
                    "FAILED -> No 'findServiceResponse' element in the ECRF-LVF "
                    f"response.\n{response_xml}"
                ),
            },
        ),
        TestCheck(
            test_name="Validate no 'errors' element in the ECRF-LVF 'findServiceResponse'",
            precondition=stimulus_message
            and response_xml
            and is_valid_xml(response_xml),
            precondition_error=(
                "NOT RUN -> No stimulus 'findService' request found"
                if not stimulus_message
                else "NOT RUN -> XML body should be present and have valid structure in the ECRF-LVF to ESRP response"
            ),
            test_method=is_data_absent,
            test_params={
                "test_data": response_errors_node,
                "error": "FAILED -> ECRF-LVF response contains an 'errors' element.",
            },
        ),
        TestCheck(
            test_name="Validate 'path' element is present in the ECRF-LVF 'findServiceResponse'",
            precondition=stimulus_message
            and response_xml
            and is_valid_xml(response_xml),
            precondition_error=(
                "NOT RUN -> No stimulus 'findService' request found"
                if not stimulus_message
                else "NOT RUN -> No XML body in the ECRF-LVF to ESRP response"
            ),
            test_method=is_data_present,
            test_params={
                "test_data": response_path_block,
                "error": (
                    "FAILED -> No 'path' element in the ECRF-LVF to ESRP response.\n"
                    f"{response_xml}"
                ),
            },
        ),
        TestCheck(
            test_name=(
                "Validate 'path' element of the ECRF-LVF 'findServiceResponse' contains expected number of 'via' elements"
            ),
            precondition=stimulus_message
            and expected_via_sources
            and all(expected_via_sources),
            precondition_error=(
                "NOT RUN -> No stimulus 'findService' request found"
                if not stimulus_message
                else "NOT RUN -> FQDN must be populated in lab_config"
            ),
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": len(expected_via_sources),
                "actual_data": len(response_via_sources),
                "error": (
                    "Number of the 'via' elements in the ECRF-LVF response 'path' "
                    f"element doesn't match the expected one. "
                    f"Actual: {response_via_sources}"
                ),
            },
        ),
        TestCheck(
            test_name=(
                "Validate 'via' sources of the ECRF-LVF 'findServiceResponse' 'path' element match expected FQDNs in expected order"
            ),
            precondition=stimulus_message
            and expected_via_sources
            and all(expected_via_sources),
            precondition_error=(
                "NOT RUN -> No stimulus 'findService' request found"
                if not stimulus_message
                else "NOT RUN -> FQDN must be populated in lab_config"
            ),
            test_method=is_test_data_the_same,
            test_params={
                "expected_data": expected_via_sources,
                "actual_data": response_via_sources,
                "error": (
                    "'via' sources of the ECRF-LVF response 'path' element don't match "
                    "the expected FQDNs or their order"
                ),
            },
        ),
        TestCheck(
            test_name=(
                "Validate 'via' sources of the ECRF-LVF 'findServiceResponse' conform to the 'appUniqueString' pattern"
            ),
            precondition=stimulus_message
            and expected_via_sources
            and all(expected_via_sources),
            precondition_error=(
                "NOT RUN -> No stimulus 'findService' request found"
                if not stimulus_message
                else "NOT RUN -> FQDN must be populated in lab_config"
            ),
            test_method=check_each_element,
            test_params={
                "check_method": validate_via_source_format,
                "collection": response_via_sources,
            },
        ),
    ]

    if variation.name == VARIATION_RECURSIVE_VIA:
        # Variation 2 - the recursive query towards the Test System ECRF-LVF and
        # the verbatim propagation of its <path> element back to the ESRP
        checks += [
            TestCheck(
                test_name="Validate recursive 'findService' request is forwarded to Test System ECRF-LVF",
                precondition=stimulus_message,
                precondition_error="NOT RUN -> No stimulus 'findService' request found",
                test_method=is_data_present,
                test_params={
                    "test_data": forwarded_request_message,
                    "error": (
                        "FAILED -> No recursive 'findService' request forwarded by "
                        "ECRF-LVF to Test System ECRF-LVF found."
                    ),
                },
            ),
            TestCheck(
                test_name="Validate 'path' element is present in the forwarded recursive 'findService' request",
                precondition=stimulus_message and forwarded_request_message,
                precondition_error=(
                    "NOT RUN -> No stimulus 'findService' request found"
                    if not stimulus_message
                    else "NOT RUN -> No recursive 'findService' request forwarded to Test System ECRF-LVF"
                ),
                test_method=is_data_present,
                test_params={
                    "test_data": forwarded_path_block,
                    "error": (
                        "FAILED -> No 'path' element in the recursive 'findService' "
                        "request forwarded to Test System ECRF-LVF."
                    ),
                },
            ),
            TestCheck(
                test_name=(
                    "Validate 'via' source of the forwarded recursive 'findService' request equals the ECRF-LVF FQDN"
                ),
                precondition=stimulus_message and forwarded_path_block and ecrf_fqdn,
                precondition_error=(
                    "NOT RUN -> No stimulus 'findService' request found"
                    if not stimulus_message
                    else (
                        "NOT RUN -> No 'path' element in the forwarded recursive 'findService' request"
                        if not forwarded_path_block
                        else "NOT RUN -> FQDN must be populated in lab_config"
                    )
                ),
                test_method=is_test_data_the_same,
                test_params={
                    "expected_data": [ecrf_fqdn],
                    "actual_data": forwarded_via_sources,
                    "error": (
                        "'via' sources of the forwarded recursive 'findService' request "
                        "don't match the ECRF-LVF FQDN"
                    ),
                },
            ),
            TestCheck(
                test_name="Validate 'path' element is present in the Test System ECRF-LVF 'findServiceResponse'",
                precondition=stimulus_message and forwarded_request_message,
                precondition_error=(
                    "NOT RUN -> No stimulus 'findService' request found"
                    if not stimulus_message
                    else "NOT RUN -> No recursive 'findService' request forwarded to Test System ECRF-LVF"
                ),
                test_method=is_data_present,
                test_params={
                    "test_data": downstream_path_block,
                    "error": (
                        "FAILED -> No 'path' element in the 'findServiceResponse' "
                        "received from Test System ECRF-LVF."
                    ),
                },
            ),
            TestCheck(
                test_name=(
                    "Validate 'path' element returned to the ESRP is 'byte-for-byte' identical to the 'path' element received from Test System ECRF-LVF"
                ),
                precondition=bool(stimulus_message) and downstream_path_block != "",
                precondition_error=(
                    "NOT RUN -> No stimulus 'findService' request found"
                    if not stimulus_message
                    else "NOT RUN -> No 'path' element in the Test System ECRF-LVF response"
                ),
                test_method=is_test_data_the_same,
                test_params={
                    "expected_data": downstream_path_block,
                    "actual_data": response_path_block,
                    "error": (
                        "'path' element returned to the ESRP is not 'byte-for-byte' identical to the "
                        "'path' element received from Test System ECRF-LVF"
                    ),
                },
            ),
        ]

    return checks
