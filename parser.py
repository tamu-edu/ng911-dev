import argparse


def get_command_parser():
    """
        examples:
        python3 -m main run \
        --launch path/launch_config_example.yaml \
        [ --use_rc /path/existing_run_config.yaml ] \
        [ --gen_rc /path/where/save/run_config.yaml]

        python3 -m main validate \
        --run_config /path/run_config.yaml \
        --lab_config
        --lab_info
        --test_config
        --test_info
        --launch_config /path/launch_config.yaml \
        --output_path /path/errors_file.log

        python3 -m main gen_report \
        --report_file path/report_file.json \
        --filename new_report \
        --format json \
        --detailed \
        --folder /tmp/output/folder/path

        python3 -m main generate_jws json_file_path \
        --cert path/cert.crt \
        --key path/cert.key \
        [ --password pass123 ] \
        [ --cert_url http://reference.fqdn:8080/certificate.pem ] \
        [ --disable_cert_url_checks]

        python3 -m main decode_jws jws_file_path \
        --key path/cert.key \
        [ --password pass123 ]
        """
    parser = argparse.ArgumentParser(description="Run testing scenarios")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    config_validator = subparsers.add_parser("validate", help="Run with a PCAP file")
    config_validator.add_argument(
        "--run_config", type=str, default=None, help="Path to the Config file"
    )
    config_validator.add_argument(
        "--lab_config", type=str, default=None, help="Path to the Config file"
    )
    config_validator.add_argument(
        "--lab_info", type=str, default=None, help="Path to the Config file"
    )
    config_validator.add_argument(
        "--test_config", type=str, default=None, help="Path to the Config file"
    )
    config_validator.add_argument(
        "--test_info", type=str, default=None, help="Path to the Config file"
    )
    config_validator.add_argument(
        "--launch_config", type=str, default=None, help="Path to the Config file"
    )
    config_validator.add_argument(
        "--output_path", type=str, default=None, help="Path to the Errors output file"
    )

    generator = subparsers.add_parser("gen_report", help="Gen run_config")
    generator.add_argument(
        "--json_file", type=str, help="Path to the json report file from initial TS run"
    )
    generator.add_argument(
        "--filename", type=str, help="Name of the report file without format"
    )
    generator.add_argument(
        "--report_type", type=str, help="Type/Format of the report file"
    )
    generator.add_argument(
        "--folder", type=str, default=None, help="Output folder for the report file"
    )
    generator.add_argument(
        "--detailed", action="store_true", help="Should it be the detailed report"
    )

    # Command for `run`
    test_runner = subparsers.add_parser("run", help="Run live capture")
    test_runner.add_argument(
        "--launch", type=str, help="Path to the Launch config file"
    )
    test_runner.add_argument(
        "--use_rc", type=str, default=None, help="Path to the Existing run_config file"
    )
    test_runner.add_argument(
        "--gen_rc",
        type=str,
        default=None,
        help="Path where to generate run_config file",
    )

    # Command for 'generate_jws'
    jws_generator = subparsers.add_parser(
        "generate_jws", help="Run with path to JSON file"
    )
    jws_generator.add_argument("json_file_path", type=str, help="Path to JSON file")
    jws_generator.add_argument(
        "--cert", required=True, type=str, help="Path to certificate file"
    )
    jws_generator.add_argument(
        "--key", required=True, type=str, help="Path to private key file"
    )
    jws_generator.add_argument(
        "--password",
        type=str,
        default=None,
        help="Password for private key file (optional)",
    )
    jws_generator.add_argument(
        "--output_file", type=str, default=None, help="Output file path (optional)"
    )
    jws_generator.add_argument(
        "--cert_url",
        type=str,
        default=None,
        help="URL for certificate reference (optional)",
    )
    jws_generator.add_argument(
        "--disable_cert_url_checks",
        action="store_true",
        help="Disables verification of URL for certificate reference (optional)",
    )

    # Command for 'decode_jws'
    jws_decoder = subparsers.add_parser(
        "decode_jws", help="Run with path to file containing JWS"
    )
    jws_decoder.add_argument("jws_file_path", type=str, help="Path to JWS file")
    jws_decoder.add_argument(
        "--key", required=True, type=str, help="Path to private key file"
    )
    jws_decoder.add_argument(
        "--password",
        type=str,
        default=None,
        help="Password for private key file (optional)",
    )

    # Command for `management server`
    ms_runner = subparsers.add_parser("ms", help="Run Management server")
    ms_runner.add_argument(
        "--host", type=str, default=None, help="host for management server (optional)"
    )
    ms_runner.add_argument(
        "--port", type=str, default=None, help="port for management server (optional)"
    )

    return parser
