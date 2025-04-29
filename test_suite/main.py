import argparse

from logger.logger_service import LoggerService
from services.config.types.run_config import RunConfig
from services.pcap_service import PcapCaptureService
from services.config.config_service import ConfigService
from services.config.types.test_config import TestConfig
from services.config.types.lab_config import LabConfig
from services.reciever_services.http_reciever_service import HttpReceiverService
from services.reciever_services.sip_reciever_service import SipReceiverService
from services.sender_services.https_sender_service import HttpRequestService
from services.sender_services.sip_sender_service import SipSenderService
from services.test_services.test_oracle import TestOracle
from services.report.report_service import ReportService
from test_mapping import TEST_MAPPING
from services.aux.json_services import generate_jws, decrypt_jws


def get_pc_service_from_pcap(pcap_file: str):
    print(f"Running with PCAP file: {pcap_file}")
    pcap_service = PcapCaptureService(pcap_file=pcap_file)
    return pcap_service


def get_pc_service_from_local_monitoring_capture(interface: str):
    pass
    # pcap_service = PcapCaptureService(interface=interface)
    # return pcap_service


def run_test(test_name: str, capture: PcapCaptureService):
    print(f"Running test: {test_name}")
    print("-" * 50)

    test_function = TEST_MAPPING.get(test_name)
    if test_function:
        test_function(capture)
        capture.close_capture()
    else:
        print(f"Test '{test_name}' not found.")


def validate_configs(config_file_path: str, output_file_path: str | None):
    ConfigService.validate(config_file_path, output_file_path)


def generate_run_config(config_file_path: str, run_config_format: str | None, run_config_path: str | None):
    is_config_file_validated = ConfigService.validate(config_file_path)
    if is_config_file_validated:
        print(f"Generating run_config file")
        if run_config_format and run_config_path:
            ConfigService.generate_run_config_file(config_file_path, run_config_format, run_config_path)
        elif run_config_format:
            ConfigService.generate_run_config_file(config_file_path, run_config_format,
                                                   "run_config." + run_config_format)
        elif run_config_path:
            run_config_format = run_config_path.split('.')[-1]
            ConfigService.generate_run_config_file(config_file_path, run_config_format, run_config_path)

        print(f"Run_config file successfully generated.")


def run_test_with_config(config_file_path: str):
    print(f"Validating the Configuration files from {config_file_path}...")
    print("-" * 50)
    is_config_file_validated = ConfigService.validate(config_file_path)
    if is_config_file_validated:
        print(f"Parsing the Configuration files from {config_file_path}...")
        config_service = ConfigService(config_file_path)

        test_config = TestConfig.from_dict(config_service.get_test_config())
        test_config.validate()

        run_config = RunConfig.from_dict(config_service.get_run_config())
        run_config.validate()

        LoggerService(**run_config.get_log_config().get_values())

        lab_config = LabConfig.from_dict(config_service.get_lab_config())
        lab_config.validate()

        test_oracle = TestOracle(
            test_config=test_config,
            lab_config=lab_config,
            run_config=run_config
        )
        test_oracle.run_scenarios()

        # Report generating.
        test_oracle.calculate_general_verdict()

        report_service = ReportService(test_oracle)
        for report in run_config.global_config.report_files:
            print(f"Generating {report.path} report file")
            report_service.generate_report(report.type, report.path)

        test_oracle.print_general_verdict()


def main():
    """
    examples:
    python3 -m main validate test_files/configs/base_config.yaml --output_file_path output.txt

    python3 -m main generate_rc test_files/configs/base_config.yaml --rc_f json --rc_p run_config.json

    python3 -m main run test_files/configs/base_config.yaml


    python3 -m main generate_jws /path/to/file.json --cert /path/to/certificate.pem --key /path/to/key.pem
    --pass 'optional_key_file_password'

    python3 -m main decrypt_jws /path/to/jws_file.txt --key /path/to/key.pem --pass 'optional_key_file_password'
    """
    parser = argparse.ArgumentParser(description="Run testing scenarios")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command for `validate`
    config_validator = subparsers.add_parser("validate", help="Run with a PCAP file")
    config_validator.add_argument("config_file_path", type=str, help="Path to the Config file")
    config_validator.add_argument("--output_file_path", type=str, default=None, help="Path to the Config file")

    # Command for `generate run config`
    generator = subparsers.add_parser("generate_rc", help="Gen run_config")
    generator.add_argument("config_file_path", type=str, help="Path to the Config file")
    generator.add_argument("--rc_f", type=str, default=None, help="Format for the run config")
    generator.add_argument("--rc_p", type=str, default=None, help="Path for the run config")

    # Command for `run`
    test_runner = subparsers.add_parser("run", help="Run live capture")
    test_runner.add_argument("config_file_path", type=str, help="Path to the Config file")

    # Command for `run_test` TODO delete
    test_t_runner = subparsers.add_parser("run_test", help="Run live capture")
    test_t_runner.add_argument("test_name", type=str, help="TEst Name")
    test_t_runner.add_argument("pcap_path", type=str, help="TEst Name")

    # Command for 'generate_jws'
    jws_generator = subparsers.add_parser("generate_jws", help="Run with path to JSON file")
    jws_generator.add_argument("json_file_path", type=str, help="Path to JSON file")
    jws_generator.add_argument("--cert", required=True, type=str, help="Path to certificate file")
    jws_generator.add_argument("--key", required=True, type=str, help="Path to private key file")
    jws_generator.add_argument(
        "--password",
        type=str,
        default=None,
        help="Password for private key file (optional)"
    )

    # Command for 'decrypt_jws'
    jws_decrypter = subparsers.add_parser("decrypt_jws", help="Run with path to file containing JWS")
    jws_decrypter.add_argument("jws_file_path", type=str, help="Path to JWS file")
    jws_decrypter.add_argument("--key", required=True, type=str, help="Path to private key file")
    jws_decrypter.add_argument(
        "--password",
        type=str,
        default=None,
        help="Password for private key file (optional)"
    )

    # Parse the arguments
    args = parser.parse_args()

    # Dispatch to the appropriate function
    if args.command == "validate":
        validate_configs(args.config_file_path, args.output_file_path)
    elif args.command == "generate_rc":
        generate_run_config(args.config_file_path, args.rc_f, args.rc_p)
    elif args.command == "run":
        run_test_with_config(args.config_file_path)
    elif args.command == "run_test":
        run_test(args.test_name, PcapCaptureService(pcap_file=args.pcap_path))
    elif args.command == "generate_jws":
        print(generate_jws(args.json_file_path, args.cert, args.key, args.password))
    elif args.command == "decrypt_jws":
        print(decrypt_jws(args.jws_file_path, args.key, args.password))
    else:
        parser.print_help()


# TODO delete further 4 methods

def send_sip():
    with SipSenderService("0.0.0.0", 5061, "UDP") as sip_sender:
        sip_sender.send_sip_message("REGISTER sip:example.com SIP/2.0")


def send_http():
    # API_URL = "https://jsonplaceholder.typicode.com"
    API_URL = "http://localhost:8080"

    with HttpRequestService(API_URL, verify_ssl=True) as http_service:
        # Example: GET request
        response = http_service.get("/posts/1")
        if response:
            print("GET Response:", response.json())

        # Example: POST request
        new_post = {"title": "Foo", "body": "Bar", "userId": 1}
        response = http_service.post("/posts", json=new_post)
        if response:
            print("POST Response:", response.json())

        # Example: PUT request
        updated_post = {"id": 1, "title": "Updated", "body": "New Content", "userId": 1}
        response = http_service.put("/posts/1", json=updated_post)
        if response:
            print("PUT Response:", response.json())

        # Example: DELETE request
        response = http_service.delete("/posts/1")
        if response:
            print("DELETE Response:", response.status_code)


def r_sip():
    sip_receiver = SipReceiverService("0.0.0.0", 5061, "UDP")

    # Start the receiver in a new thread
    sip_receiver_thread = sip_receiver.start_in_thread()

    # Continue executing other commands
    print("SIP Receiver is running in the background...")
    return sip_receiver, sip_receiver_thread


def r_sip_stop(sr):
    sr.stop()


def r_http():
    http_receiver = HttpReceiverService("0.0.0.0", 8080)
    http_receiver.start()
    return http_receiver

    # Start HTTPS Receiver (with SSL)
    # https_receiver = HttpReceiverService("0.0.0.0", 8443, use_ssl=True, cert_file="cert.pem", key_file="key.pem")
    # https_receiver.start()


if __name__ == "__main__":
    # LoggerService(level=LogLevel.INFO)
    #
    # # sip_receiver, sip_receiver_thread = r_sip()
    # http_receiver = r_http()
    #
    # import time
    # #
    # time.sleep(1)  # Simulate work
    # print("Main thread still working...")
    # send_http()
    # # send_sip()
    # time.sleep(2)
    # http_receiver.stop()
    # # r_sip_stop(sip_receiver)

    main()

