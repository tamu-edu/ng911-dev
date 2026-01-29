from services.stub_server.sip_service.extra_logic import utils as ss_utils
from services.stub_server.sip_service.extra_logic import methods as ss_methods
from services import prep_services
import json
import os
import ssl
import copy

import requests

from ..errors.wrong_pre_amble_response_error import WrongPreambleResponseError
from ...aux_services.json_services import generate_jws, iso_to_timestamp, float_timestamp_to_iso
from typing import Any, Dict

from ...prep_services import extract_from_config

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


def prepare_jws_procedures(**kwargs):
    print("[PREAMBLE]: STARTING prepare_jws_procedures")

    list_of_procedures = kwargs.get('list_of_procedures')
    config_vars = kwargs.get('config_vars')
    url = kwargs.get('url')
    expected_response_code = kwargs.get('expected_response_code')

    execute_multiple = kwargs.get('execute_multiple', {})
    delay_between_messages = kwargs.get('delay_between_messages', False)

    lab_config_entities = kwargs.get('configs').get('lab_config')['lab_config']['entities']

    cert_path = extract_from_config(lab_config_entities,
                                    'certificate_file',
                                    "name",
                                    "ESRP")

    key_path = extract_from_config(lab_config_entities,
                                   'certificate_key',
                                   "name",
                                   "ESRP")

    interfaces = extract_from_config(lab_config_entities,
                                     'interfaces',
                                     "name",
                                     "LOG")

    api_http_url_prefix = extract_from_config(lab_config_entities,
                                              'api_http_url_prefix',
                                              "name",
                                              "LOG")

    ip = interfaces[0].get('ip', None)
    fqdn = interfaces[0].get('fqdn', None)
    port = interfaces[0].get('port_mapping', None)[0].get('port', None)
    protocol = interfaces[0].get('port_mapping', None)[0].get('protocol', None)

    url = "/" + url if not url.startswith('/') else url
    api_http_url_prefix = "/" + url if not api_http_url_prefix.startswith('/') else api_http_url_prefix

    if fqdn:
        full_url = f"{protocol}://{fqdn}{api_http_url_prefix}{url}"
    else:
        if port:
            full_url = f"{protocol}://{ip}:{port}{api_http_url_prefix}{url}"
        else:
            full_url = f"{protocol}://{ip}{api_http_url_prefix}{url}"

    # Modify procedures files, replacing input information
    # Get file data
    for procedure_name in list_of_procedures:
        raw_procedure_data = None

        # 1. Find and load the file once per procedure name
        for root, _, files in os.walk('test_suite/test_files'):
            if procedure_name in files:
                procedure_filepath = os.path.join(root, procedure_name)
                with open(procedure_filepath, 'r') as f:
                    raw_procedure_data = json.load(f)
                break

        if not raw_procedure_data:
            raise WrongPreambleResponseError(f"Cannot find procedure file: {procedure_name}")

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
                        float_timestamp = iso_to_timestamp(value) + float(delay_between_messages)
                        current_data[var] = float_timestamp_to_iso(float_timestamp)
                    else:
                        current_data[var] = value

            # Prepare JWS
            print("[PREAMBLE]: GENERATING JWS")
            body = generate_jws(current_data, cert_path, key_path)
            if body:
                print("[PREAMBLE]: GENERATED JWS SUCCESSFULLY")

            # Setup request
            ssl_ctx = ssl.create_default_context(
                purpose=ssl.Purpose.SERVER_AUTH
            )

            # Server verification
            # if args.ca:
            #     ssl_ctx.load_verify_locations(cafile=args.ca)

            # Client certificate (mTLS)
            cert_tuple = (cert_path, key_path) if (cert_path, key_path) else None

            session = requests.Session()

            request_args = {"url": full_url, "headers": {"Content-Type": "application/json"}, "cert": cert_tuple,
                            "timeout": (5, 15), "data": (body or "").encode()}

            print(f"[PREAMBLE] POST to {full_url} "
                  f"(TLS {getattr(ssl_ctx, 'minimum_version', None)}..{getattr(ssl_ctx, 'maximum_version', None)})")

            try:
                resp = session.request('POST', **request_args)
                if str(resp.status_code) != expected_response_code:

                    raise WrongPreambleResponseError(f"[PREAMBLE] FAILED: Response: {resp.status_code}  "
                                                     f"| Reason: {resp.reason}| Text: {resp.text}")
                else:
                    print(f"[PREAMBLE] SUCCESSFUL")
            except Exception as e:
                print(f"[PREAMBLE] Request failed: {e}")
