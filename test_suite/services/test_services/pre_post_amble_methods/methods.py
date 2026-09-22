# from services.stub_server.sip_service.extra_logic import utils as ss_utils
# from services.stub_server.sip_service.extra_logic import methods as ss_methods
# from services import prep_services
import json
import os
import ssl
import copy
import psutil
import ipaddress
import subprocess

import requests
from requests.adapters import HTTPAdapter

from ..errors.wrong_pre_amble_response_error import WrongPreambleResponseError
from ...aux_services.aux_services import get_sudo
from ...aux_services.json_services import (
    generate_jws,
    iso_to_timestamp,
    float_timestamp_to_iso,
)

from ...config.types.lab_config import LabConfig
from ...prep_services import extract_from_config
from ...stub_server.enums import StubServerRole
from ...stub_server.stub_server_service import StubServerService

# SOME REQUIREMENTS
"""
Method should be explicit and do NOT return anything
Each method is pre- or post- amble integral step so everything relate to it should be encapsulated in it
feel free to reuse methods from sip_service.extra_logic utils, methods and prep_services 
as they are imported here accordingly

all configs would be passed to the methods as config: dict
"""


def example_method(**kwargs):
    print(kwargs)


class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, **kwargs):
        self.source_ip = source_ip
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        pool_kwargs["source_address"] = (self.source_ip, 0)
        return super().init_poolmanager(connections, maxsize, block, **pool_kwargs)


def _check_iface_by_target_ip(target_ip):
    target_ip = ipaddress.IPv4Address(target_ip)
    for iface_name, iface_addresses in psutil.net_if_addrs().items():
        for addr in iface_addresses:
            if addr.family.name == "AF_INET":
                try:
                    iface_net = ipaddress.IPv4Network(
                        f"{addr.address}/{addr.netmask}", strict=False
                    )
                    if target_ip in iface_net:
                        return iface_name
                except Exception:
                    continue


def _mask_to_prefix(mask: str) -> int:
    parts = mask.split(".")
    if len(parts) != 4:
        raise ValueError("Invalid mask")

    prefix = 0
    for p in parts:
        n = int(p)
        if n < 0 or n > 255:
            raise ValueError("Invalid mask value")

        prefix += bin(n).count("1")

    return prefix


def _check_if_ip_alias_exists(ip, mask, interface):
    cmd = ["ip", "-o", "-f", "inet", "addr", "show", "dev", interface]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return False

    target = f"{ip}/{_mask_to_prefix(mask)}"

    for line in result.stdout.splitlines():
        parts = line.split()
        for part in parts:
            if part == target:
                return True
    return False


def _add_ip_alias_safely(ip, mask, interface):
    sudo = get_sudo()
    try:
        prefix = ipaddress.IPv4Network((ip, mask), strict=False).prefixlen
    except Exception:
        try:
            prefix = int(str(mask))
        except Exception:
            prefix = 24

    existing = subprocess.check_output(
        ["ip", "addr", "show", "dev", interface],
        text=True,
    )

    needle = f"{ip}/{prefix}"

    if needle not in existing:

        cmd = ["ip", "addr", "add", f"{ip}/{prefix}", "dev", interface]

        if sudo:
            cmd.insert(0, "sudo")

        subprocess.run(cmd, check=True, shell=False)

        print(f"Alias created -> {ip}/{prefix} dev {interface}")
    else:
        print(f"⚠️ IP alias {ip}/{prefix} already exists on {interface}")


def _remove_ip_alias(ip, mask, iface="enp0s8"):
    sudo = get_sudo()
    try:
        subprocess.run(
            [f"{sudo}", "ip", "addr", "del", f"{ip}/{mask}", "dev", iface],
            check=False,
            shell=False,
        )
        print(f"✔️ Removed IP alias: {ip} from {iface}")
    except Exception as e:
        print(f"⚠️ Failed to remove IP alias {ip}: {e}")


def prepare_jws_procedures(**kwargs):
    print("[PREAMBLE]: STARTING prepare_jws_procedures")

    list_of_procedures = kwargs.get("list_of_procedures")
    config_vars = kwargs.get("config_vars")
    url = kwargs.get("url")
    expected_response_code = kwargs.get("expected_response_code")

    execute_multiple = kwargs.get("execute_multiple", {})
    delay_between_messages = kwargs.get("delay_between_messages", False)

    if_name = kwargs.get("if_name")
    target_entity_name = source_entity_name = ""
    if if_name and if_name.startswith("IF_"):
        try:
            target_entity_name = if_name.removeprefix("IF_").split("_")[1]
            source_entity_name = if_name.removeprefix("IF_").split("_")[0]
        except IndexError:
            pass
    if not target_entity_name or not source_entity_name:
        print(
            f"[PREAMBLE]: prepare_jws_procedures failed, source and target entity names not found in "
            f"if_name:'{if_name}'"
        )
        return

    lab_config_entities = kwargs.get("configs").get("lab_config")["lab_config"][
        "entities"
    ]

    cert_path = extract_from_config(
        lab_config_entities, "certificate_file", "name", source_entity_name
    )

    key_path = extract_from_config(
        lab_config_entities, "certificate_key", "name", source_entity_name
    )

    target_interfaces = extract_from_config(
        lab_config_entities, "interfaces", "name", target_entity_name
    )

    target_if_name = f"IF_{target_entity_name}_{source_entity_name}"
    ip = fqdn = protocol = port = None
    for interface in target_interfaces:
        if interface.get("name", "") == target_if_name:
            ip = interface.get("ip", None)
            fqdn = interface.get("fqdn", None)
            interface_port = None
            for p in interface.get("port_mapping", []):
                if p.get("protocol", "") == "HTTPS":
                    interface_port = p
            if not interface_port:
                for p in interface.get("port_mapping", []):
                    if p.get("protocol", "") == "HTTP":
                        interface_port = p
            if interface_port:
                port = interface_port.get("port", None)
                protocol = interface_port.get("protocol", None)
                protocol = protocol.lower() if protocol else None
            else:
                port = protocol = None
    if not ip or not port or not protocol:
        print(
            f"[PREAMBLE]: Failed to get IP, FQDN, port, protocol for {target_if_name}"
        )
        return

    source_interfaces = extract_from_config(
        lab_config_entities, "interfaces", "name", source_entity_name
    )

    for interface in source_interfaces:
        if interface.get("name", "") == if_name:
            source_ip = interface.get("ip", None)
            source_mask = interface.get("mask", None)

    if not source_ip or not source_mask:
        print(f"[PREAMBLE]: Failed to get IP, mask for {if_name}")
        return

    local_interface_name = _check_iface_by_target_ip(source_ip)
    ip_alias_exists = _check_if_ip_alias_exists(
        source_ip, source_mask, local_interface_name
    )
    if local_interface_name:
        if not ip_alias_exists:
            _add_ip_alias_safely(source_ip, source_mask, local_interface_name)
    else:
        source_ip = kwargs.get("configs").get("lab_config")["lab_config"][
            "test_suite_host_ip"
        ]

    api_http_url_prefix = extract_from_config(
        lab_config_entities, "api_http_url_prefix", "name", target_entity_name
    )

    full_url = f"{protocol}://"
    full_url += fqdn if fqdn else ip
    full_url += f":{port}" if port else ""
    full_url += (
        f"/{api_http_url_prefix.removeprefix('/').removesuffix('/')}"
        if api_http_url_prefix
        else ""
    )
    full_url += f"/{url.removeprefix('/')}" if url else ""

    # Modify procedures files, replacing input information
    # Get file data
    for procedure_name in list_of_procedures:
        raw_procedure_data = None

        # 1. Find and load the file once per procedure name
        for root, _, files in os.walk("test_suite/test_files"):
            if procedure_name in files:
                procedure_filepath = os.path.join(root, procedure_name)
                with open(procedure_filepath, "r") as f:
                    raw_procedure_data = json.load(f)
                break

        if not raw_procedure_data:
            raise WrongPreambleResponseError(
                f"Cannot find procedure file: {procedure_name}"
            )

        # 2. Determine execution count
        # Default to 1 if not found in execute_multiple
        iterations = execute_multiple.get(procedure_name, 1)
        print(f"[PREAMBLE]: Processing {procedure_name} (Total runs: {iterations})")

        # 3. Execution Loop
        for i in range(iterations):
            # Deep copy data so modifications in one iteration don't corrupt the next
            current_data = copy.deepcopy(raw_procedure_data)

            # Replace vars
            for var, value in config_vars.items():
                if var in current_data:
                    # Logic for handling dynamic timestamps if needed
                    if var == "timestamp" and delay_between_messages:
                        float_timestamp = iso_to_timestamp(value) + float(
                            delay_between_messages
                        )
                        current_data[var] = float_timestamp_to_iso(float_timestamp)
                    else:
                        current_data[var] = value

            # Prepare JWS
            print("[PREAMBLE]: GENERATING JWS")
            body = generate_jws(current_data, cert_path, key_path)
            if body:
                print("[PREAMBLE]: GENERATED JWS SUCCESSFULLY")

            # Setup request
            ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

            # Server verification
            # if args.ca:
            #     ssl_ctx.load_verify_locations(cafile=args.ca)

            # Client certificate (mTLS)
            cert_tuple = (cert_path, key_path) if (cert_path, key_path) else None

            session = requests.Session()
            adapter = SourceIPAdapter(source_ip)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            request_args = {
                "url": full_url,
                "headers": {"Content-Type": "application/json"},
                "cert": cert_tuple,
                "timeout": (5, 15),
                "data": (body or "").encode(),
            }

            print(
                f"[PREAMBLE] POST to {full_url} from {source_ip} "
                f"(TLS {getattr(ssl_ctx, 'minimum_version', None)}..{getattr(ssl_ctx, 'maximum_version', None)})"
            )

            try:
                resp = session.request("POST", **request_args)
                if str(resp.status_code) != expected_response_code:

                    raise WrongPreambleResponseError(
                        f"[PREAMBLE] FAILED: Response: {resp.status_code}  "
                        f"| Reason: {resp.reason}| Text: {resp.text}"
                    )
                else:
                    print("[PREAMBLE] SUCCESSFUL")
            except Exception as e:
                print(f"[PREAMBLE] Request failed: {e}")
    if not ip_alias_exists:
        _remove_ip_alias(source_ip, source_mask, local_interface_name)


def prepare_rtt_conversation(**kwargs):
    """
    Combined preamble helper for RTT scenarios.

    1. Generates LogEvent objects (including text events) via `prepare_jws_procedures`.
    2. Issues HTTP GET to the `/Conversations` endpoint passing the provided NENA Call Identifier.

    Expected kwargs (superset of `prepare_jws_procedures`):
        list_of_procedures: list[str]          # JSON procedure filenames used to build LogEvents
        config_vars: dict                      # Variables to replace inside JSONs (must contain "callId")
        url: str                               # Path for POSTing LogEvents (e.g. "/LogEvents")
        expected_response_code: str            # Expected HTTP status from LogEvent POST (default "201")
        conversation_url: str                  # Path template for GET (default "/Conversations?callId={callId}")
        expected_get_response_code: str        # Expected HTTP status from GET (default "200")
        execute_multiple / delay_between_messages
        configs: dict                          # Passed automatically by PrePostAmbleService
    """

    print("[PREAMBLE]: STARTING prepare_rtt_conversation → generating LogEvents …")

    # STEP 1 – POST LogEvents (reuse existing helper)
    #   Strip GET-specific kwargs so `prepare_jws_procedures` receives only what it knows.
    post_kwargs = copy.deepcopy(kwargs)
    post_kwargs.pop("conversation_url", None)
    post_kwargs.pop("expected_get_response_code", None)

    prepare_jws_procedures(**post_kwargs)

    print(
        "[PREAMBLE]: LogEvents generated successfully, proceeding with /Conversations GET …"
    )

    # Fetch required params
    configs = kwargs.get("configs", {})
    lab_config_entities = (
        configs.get("lab_config", {}).get("lab_config", {}).get("entities", [])
    )

    if_name = kwargs.get("if_name")
    target_entity_name = source_entity_name = ""
    if if_name and if_name.startswith("IF_"):
        try:
            target_entity_name = if_name.removeprefix("IF_").split("_")[1]
            source_entity_name = if_name.removeprefix("IF_").split("_")[0]
        except IndexError:
            pass
    if not target_entity_name or not source_entity_name:
        print(
            f"[PREAMBLE]: prepare_jws_procedures failed, source and target entity names not found in "
            f"if_name:'{if_name}'"
        )
        return

    cert_path = extract_from_config(
        lab_config_entities, "certificate_file", "name", source_entity_name
    )

    key_path = extract_from_config(
        lab_config_entities, "certificate_key", "name", source_entity_name
    )

    target_interfaces = extract_from_config(
        lab_config_entities, "interfaces", "name", target_entity_name
    )

    target_if_name = f"IF_{target_entity_name}_{source_entity_name}"
    ip = fqdn = protocol = port = None
    for interface in target_interfaces:
        if interface.get("name", "") == target_if_name:
            ip = interface.get("ip", None)
            fqdn = interface.get("fqdn", None)
            interface_port = None
            for p in interface.get("port_mapping", []):
                if p.get("protocol", "") == "HTTPS":
                    interface_port = p
            if not interface_port:
                for p in interface.get("port_mapping", []):
                    if p.get("protocol", "") == "HTTP":
                        interface_port = p
            if interface_port:
                port = interface_port.get("port", None)
                protocol = interface_port.get("protocol", None)
                protocol = protocol.lower() if protocol else None
            else:
                port = protocol = None
    if not ip or not port or not protocol:
        print(
            f"[PREAMBLE]: Failed to get IP, FQDN, port, protocol for {target_if_name}"
        )
        return

    source_interfaces = extract_from_config(
        lab_config_entities, "interfaces", "name", source_entity_name
    )
    source_ip = source_mask = None
    for interface in source_interfaces:
        if interface.get("name", "") == if_name:
            source_ip = interface.get("ip", None)
            source_mask = interface.get("mask", None)

    if not source_ip or not source_mask:
        print(f"[PREAMBLE]: Failed to get IP, mask for {if_name}")
        return

    local_interface_name = _check_iface_by_target_ip(source_ip)
    ip_alias_exists = _check_if_ip_alias_exists(
        source_ip, source_mask, local_interface_name
    )
    if local_interface_name:
        if not ip_alias_exists:
            _add_ip_alias_safely(source_ip, source_mask, local_interface_name)
    else:
        source_ip = kwargs.get("configs").get("lab_config")["lab_config"][
            "test_suite_host_ip"
        ]

    api_http_url_prefix = extract_from_config(
        lab_config_entities, "api_http_url_prefix", "name", target_entity_name
    )

    # Prepare GET URL
    call_id = kwargs.get("config_vars", {}).get("callId")
    conv_url_template = kwargs.get("conversation_url", "/Conversations?callId={callId}")
    conv_path = conv_url_template.format(callId=call_id)

    conv_path = "/" + conv_path if not conv_path.startswith("/") else conv_path
    api_http_url_prefix = (
        "/" + api_http_url_prefix
        if (api_http_url_prefix and not api_http_url_prefix.startswith("/"))
        else api_http_url_prefix
    )

    full_url = f"{protocol}://"
    full_url += fqdn if fqdn else ip
    full_url += f":{port}" if port else ""
    full_url += (
        f"/{api_http_url_prefix.removeprefix('/').removesuffix('/')}"
        if api_http_url_prefix
        else ""
    )
    full_url += f"/{conv_path.removeprefix('/')}" if conv_path else ""
    print(f"[PREAMBLE]: GET {full_url}")

    # TLS / mTLS setup (same as POST helper)

    # TODO SEBASTIAN - need to check what you needed here - either use ssl_ctx via SSLContextAdapter
    # TODO and session.mount("https://", SSLContextAdapter(ssl_ctx)) or remove it

    # ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    cert_tuple = (cert_path, key_path) if (cert_path and key_path) else None

    session = requests.Session()
    adapter = SourceIPAdapter(source_ip)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    request_args = {
        "url": full_url,
        "headers": {"Accept": "application/json"},
        "cert": cert_tuple,
        "timeout": (5, 15),
    }

    exp_get_code = kwargs.get("expected_get_response_code", "200")

    try:
        resp = session.request("GET", **request_args)
        if str(resp.status_code) != str(exp_get_code):
            raise WrongPreambleResponseError(
                f"[PREAMBLE] GET FAILED: expected {exp_get_code}, got {resp.status_code} | Reason: {resp.reason} | "
                f"Text: {resp.text}"
            )
        print(
            "[PREAMBLE]: /Conversations response OK – conversation fetched successfully"
        )
    except Exception as e:
        print(f"[PREAMBLE] GET request failed: {e}")
        raise
    if not ip_alias_exists:
        _remove_ip_alias(source_ip, source_mask, local_interface_name)


def run_stub_service(**kwargs):
    print("[PREAMBLE]: STARTING run_sip_service")

    scenario_file_path = kwargs.get("scenario_file_path").removeprefix("file.")
    if_name = kwargs.get("if_name")

    if if_name and if_name.startswith("IF_"):
        entity_name = if_name.removeprefix("IF_").split("_")[0]
    else:
        print(
            f"[PREAMBLE]: run_sip_service failed, entity name not found in if_name:'{if_name}'"
        )
        return
    entity = interface = port = None
    lab_config = LabConfig.from_dict(kwargs.get("configs").get("lab_config"))
    if lab_config.entities:
        for e in lab_config.entities:
            if e.name == entity_name:
                entity = e
    if entity:
        for i in entity.interfaces:
            if i.name == if_name:
                interface = i
    if interface:
        for p in interface.port_mapping:
            if p.protocol == "SIP":
                port = p
    if not entity or not interface or not port:
        print("[PREAMBLE]: run_sip_service - failed to get params from lab_config")
        return
    try:
        stub_server = StubServerService(
            entity_name=entity_name,
            lab_config=lab_config,
            current_entity=entity,
            port=port,
            current_if=interface,
            ss_role=StubServerRole.SENDER,
            docker_service=None,
            sipp_kwargs=kwargs.get("sip_service_kwargs"),
            scenario_file=scenario_file_path,
        )
        stub_server.launch_stub_server()
    except Exception as e:
        print(e)
        print(
            f"[PREAMBLE]: run_sip_service - failed to run stub server for {entity_name} -> {port.protocol}: {e}, "
            f"Skipping this part"
        )
        return
