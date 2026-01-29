import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
import signal
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Tuple

sys.path.append(os.path.abspath("test_suite"))

from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.lab_info import LabInfo
from services.config.types.launch_config import LaunchConfig
from services.config.types.run_config import RunConfig
from services.config.types.test_info import TestInfo
from services.test_services.test_oracle import TestOracle
from logger.logger_service import LoggerService, TeeStream
from services.config.run_config_service import RunConfigService
from services.config.config_service import ConfigService
from services.report.report_service import ReportService
from test_suite.services.aux_services.json_services import generate_jws, decode_jws
from services.cleanup_registry import run_cleanup, register_cleanup
from services.stub_server.stub_server_service import StubServerService
from services.stub_server.sip_service.rtp_registry import stop_all_rtp_senders

register_cleanup(
    "Stop all RTP audio/text senders",
    stop_all_rtp_senders
)

register_cleanup(
    "Stop all StubServerService instances",
    StubServerService.stop_all
)

_SHUTDOWN_ALREADY_RUN = False

def running_as_root() -> bool:
    if os.name == "nt":  # Windows
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:  # Unix-like
        return os.getuid() == 0


def get_last_commit_hash():
    result = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def get_last_commit_details():
    result = subprocess.run(["git", "log", "-1", "--pretty=format:%h - %an, %ar : %s"], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def log_environment_info(output_folder: str):
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    log_path = os.path.join(output_folder, "environment_log.txt")
    log_lines = []

    def run_command(cmd):
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip() or result.stderr.strip()
        except Exception as e:
            return f"Error running {' '.join(cmd)}: {e}"

    # Timestamp
    log_lines.append(f"--- Environment Info Log ---")
    log_lines.append(f"Timestamp: {datetime.now().isoformat()}")
    log_lines.append("")

    log_lines.append(f"Launching Test Suite based on {get_last_commit_hash()} commit. "
                     f"Details: {get_last_commit_details()}")
    log_lines.append("")

    # Python version
    log_lines.append("Python Version:")
    log_lines.append(sys.version)
    log_lines.append("")

    # tshark version
    log_lines.append("TShark Version:")
    log_lines.append(run_command(["tshark", "-v"]))
    log_lines.append("")

    # SIPp version
    log_lines.append("SIPp Version:")
    log_lines.append(run_command(["sipp", "-v"]))
    log_lines.append("")

    # pip freeze
    log_lines.append("Pip3 Freeze Output:")
    log_lines.append(run_command(["pip3", "freeze"]))
    log_lines.append("")

    # Write to file
    with open(log_path, "w") as log_file:
        log_file.write("\n".join(log_lines))

    print(f"[+] Environment info saved to {log_path}")


def validate_configs(
        run_config: str = None,
        lab_config: str = None,
        lab_info: str = None,
        test_config: str = None,
        test_info: str = None,
        launch_config: str = None,
        output_path: str = None
):
    """
    python3 -m main validate \
    --run_config /path/run_config.yaml \
    --lab_config
    --lab_info
    --test_config
    --test_info
    --launch_config /path/launch_config.yaml
    --output_path /path/errors_file.log
    """
    if launch_config:
        print(f"Validating Launch Configuration -> {launch_config}")
        ConfigService.validate_launch_config(launch_config, output_path)
    if run_config:
        print(f"Validating Run Configuration -> {run_config}")
        ConfigService.validate_run_config(run_config, output_path)
    if lab_config:
        print(f"Validating Lab Configuration -> {lab_config}")
        ConfigService.validate_lab_config(lab_config, output_path)
    if lab_info:
        print(f"Validating Lab Info -> {lab_info}")
        ConfigService.validate_lab_info(lab_info, output_path)
    if test_config:
        print(f"Validating Test Configuration -> {test_config}")
        ConfigService.validate_test_config(test_config, output_path)
    if test_info:
        print(f"Validating Test Info -> {test_info}")
        ConfigService.validate_test_info(test_info, output_path)


def generate_report(json_file: str, report_type: str, filename: str,
                    output_folder_path: str = "", is_detailed: bool = False):
    with open(json_file) as json_data:
        data = json.load(json_data)
        data["detailed_view"] = is_detailed

        report_service = ReportService(
            output_directory=output_folder_path,
            report_data=data
        )

        report_service.generate_report(report_type, filename)


def copy_file_to_output_folder(file_path: str, filename: str, output_folder_path: str):
    destination = Path(output_folder_path) / filename
    shutil.copy(str(file_path), str(destination))
    print(f"Moved: {file_path} -> {destination}")


def move_all_root_log_to_output_folder(output_folder_path: str):
    current_dir = Path.cwd()

    # Find all .log files in the current directory
    log_files = list(current_dir.glob("*.log"))

    if not log_files:
        print("No log files found.")
        return

    for log_file in log_files:
        destination = Path(output_folder_path) / log_file.name
        shutil.move(str(log_file), str(destination))
        print(f"Moved: {log_file} -> {destination}")


def move_all_output_folder_log_to_logs_folder(output_folder_path: str):
    logs_folder_suffix = '/logs'

    output_dir = Path(output_folder_path)
    logs_dir = Path(str(output_folder_path) + logs_folder_suffix)

    logs_dir.mkdir(parents=True, exist_ok=True)

    moved_any = False

    for log_file in output_dir.glob("*.log"):
        destination = logs_dir / log_file.name
        try:
            shutil.move(str(log_file), str(destination))
            print(f"Moved: {log_file} -> {destination}")
            moved_any = True
        except Exception as e:
            print(f"⚠️ Failed to move {log_file}: {e}")

    if not moved_any:
        print("No output-level log files found.")


def run(launch_config_file: str, use_rc: str = None, gen_rc: str = None):
    print(f"Validating and parsing Launch Configuration -> {launch_config_file}")
    if not ConfigService.validate_launch_config(launch_config_file):
        print(f"❌ Launch Configuration parsing failed.")
        return
    print(f"✅ Launch Configuration successfully parsed.")
    launch_config = LaunchConfig.from_dict(
        ConfigService.parse_config_file(launch_config_file)
    )

    test_id = (f"{launch_config.global_config.report_files.prefix}_"
               f"{datetime.now().strftime('%Y-%m-%dT%H%M%S')}")
    if launch_config.global_config.report_files.suffix:
        test_id += f"_{launch_config.global_config.report_files.suffix}"

    launch_config.add_test_id_to_output_folder(test_id=test_id)
    launch_config.add_test_id_to_log_output(test_id=test_id)

    os.makedirs(launch_config.output_folder, exist_ok=True)
    os.makedirs(launch_config.output_folder+"/logs", exist_ok=True)
    os.makedirs(launch_config.output_folder+"/pcaps", exist_ok=True)
    os.makedirs(launch_config.output_folder+"/configs", exist_ok=True)
    Path(launch_config.global_config.log.output_file).touch(exist_ok=True)

    log_environment_info(launch_config.output_folder + "/logs")

    register_cleanup(
        "Move root .log files into output/logs",
        lambda: move_all_root_log_to_output_folder(launch_config.output_folder + "/logs"),
    )
    register_cleanup(
        "Move output_folder .log files into ./logs",
        lambda: move_all_output_folder_log_to_logs_folder(launch_config.output_folder + "/logs"),
    )

    copy_file_to_output_folder(launch_config_file, "launch_config.yaml", launch_config.output_folder+"/configs")
    LoggerService(**launch_config.get_log_config().get_values())

    console_log_path = os.path.join(
        launch_config.output_folder, "logs", "console_output.log"
    )

    console_file = open(console_log_path, "a", buffering=1, encoding="utf-8")

    # Preserve originals
    _real_stdout = sys.stdout
    _real_stderr = sys.stderr

    sys.stdout = TeeStream(_real_stdout, console_file)
    sys.stderr = TeeStream(_real_stderr, console_file)

    register_cleanup("Close console output log", lambda: console_file.close())

    print(f"✅ Console output captured in {console_log_path}")

    if launch_config.global_config.type == "conformance":
        for test in launch_config.tests:

            print(f"Validating and parsing LAB CONFIG -> {test.lab_config}")
            if not ConfigService.validate_lab_config(test.lab_config):
                print(f"❌ LAB CONFIG parsing failed.")
                raise WrongConfigurationError(f"Impossible to run {test.iut.name} test due to "
                                              f"LAB CONFIG -> {test.lab_config} errors")
            print(f"✅ LAB CONFIG successfully parsed.")

            lab_config = LabConfig.from_dict(
                ConfigService.parse_config_file(test.lab_config)
            )
            lab_config.validate()
            lab_config_interfaces = lab_config.get_interfaces_data()
            copy_file_to_output_folder(test.lab_config, f"{test.iut.name}_lab_config.yaml",
                                       launch_config.output_folder+"/configs")
            copy_file_to_output_folder(launch_config.global_config.lab_info, "lab_info.yaml",
                                       launch_config.output_folder+"/configs")

            if gen_rc:
                print(f"Generating RUN CONFIG -> {gen_rc}")
                try:
                    _, _format = gen_rc.split(".")
                    run_config_service = RunConfigService.from_launch_config(launch_config, test, lab_config)
                    run_config_service.generate_run_config_file(file_format=_format.lower(), path=gen_rc)
                    print(f"✅ RUN CONFIG generated successfully.")
                except Exception as e:
                    print(f"❌ RUN CONFIG generation failed -> {e}")
                return

            if use_rc:
                print(f"Validating and parsing RUN CONFIG -> {use_rc}")
                if not ConfigService.validate_run_config(use_rc):
                    print(f"❌ RUN CONFIG parsing failed.")
                    raise WrongConfigurationError(f"Impossible to run {test.iut.name} test due to "
                                                  f"RUN CONFIG -> {use_rc} errors")
                print(f"✅ RUN CONFIG successfully parsed.")

                run_config_service = RunConfigService.from_dict(
                    ConfigService.parse_config_file(use_rc)
                )
                run_config_service.get_run_config().output_folder = launch_config.output_folder

                is_all_data_present, comment = run_config_service.verify_interface_data_presence(lab_config_interfaces)
                if not is_all_data_present:
                    print(f'❌{comment}')
                    return

                copy_file_to_output_folder(use_rc, f"run_config.yaml",
                                           launch_config.output_folder+"/configs")
            else:
                run_config_service = RunConfigService.from_launch_config(launch_config, test, lab_config)

                _path = f"{launch_config.output_folder}"
                if _path[-1] == "/":
                    _path += f"run_config.yaml"
                else:
                    _path += f"/run_config.yaml"
                run_config_service.generate_run_config_file(file_format="yaml", path=_path)

            test_oracle = TestOracle(
                lab_config=lab_config,
                run_config=run_config_service.get_run_config(),
                test_id=test_id
            )
            test_oracle.asses_var_results()

            # Verdict generating.
            test_oracle.calculate_general_verdict()

            report_service = ReportService(
                output_directory=(launch_config.global_config.report_files.output_folder_path or
                                  launch_config.output_folder or None),
                test_oracle=test_oracle
            )

            for report_type in launch_config.global_config.report_files.types:
                print(f"Generating report file -> Report_{test_id}.{report_type}")
                report_service.generate_report(report_type, f"Report_{test_id}")

            LoggerService.shutdown_logging()
            move_all_root_log_to_output_folder(launch_config.output_folder+"/logs")
            move_all_output_folder_log_to_logs_folder(launch_config.output_folder)
            report_service.print_report()

    elif launch_config.global_config.type == "interoperability":
        print("We are sorry, but the interoperability mode is in the development right now and we cannot use it")
        return
    else:
        print("Unknown mode")
        return


def main():
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

    # TODO refactor
    # Command for `validate`
    config_validator = subparsers.add_parser("validate", help="Run with a PCAP file")
    config_validator.add_argument("--run_config", type=str, default=None, help="Path to the Config file")
    config_validator.add_argument("--lab_config", type=str, default=None, help="Path to the Config file")
    config_validator.add_argument("--lab_info", type=str, default=None, help="Path to the Config file")
    config_validator.add_argument("--test_config", type=str, default=None, help="Path to the Config file")
    config_validator.add_argument("--test_info", type=str, default=None, help="Path to the Config file")
    config_validator.add_argument("--launch_config", type=str, default=None, help="Path to the Config file")
    config_validator.add_argument("--output_path", type=str, default=None,
                                  help="Path to the Errors output file")

    # TODO refactor
    # Command for `generate report`
    generator = subparsers.add_parser("gen_report", help="Gen run_config")
    generator.add_argument("--json_file", type=str, help="Path to the json report file from initial TS run")
    generator.add_argument("--filename", type=str, help="Name of the report file without format")
    generator.add_argument("--report_type", type=str, help="Type/Format of the report file")
    generator.add_argument("--folder", type=str, default=None, help="Output folder for the report file")
    generator.add_argument("--detailed", action="store_true", help="Should it be the detailed report")

    # Command for `run`
    test_runner = subparsers.add_parser("run", help="Run live capture")
    test_runner.add_argument("--launch", type=str, help="Path to the Launch config file")
    test_runner.add_argument("--use_rc", type=str, default=None, help="Path to the Existing run_config file")
    test_runner.add_argument("--gen_rc", type=str, default=None, help="Path where to generate run_config file")

    # Command for 'generate_jws'
    jws_generator = subparsers.add_parser("generate_jws", help="Run with path to JSON file")
    jws_generator.add_argument("json_file_path", type=str, help="Path to JSON file")
    jws_generator.add_argument("--cert", required=True, type=str, help="Path to certificate file")
    jws_generator.add_argument("--key", required=True, type=str, help="Path to private key file")
    jws_generator.add_argument("--password", type=str, default=None,
                               help="Password for private key file (optional)"
                               )
    jws_generator.add_argument("--output_file", type=str, default=None,
                               help="Output file path (optional)"
                               )
    jws_generator.add_argument("--cert_url", type=str, default=None,
                               help="URL for certificate reference (optional)"
                               )
    jws_generator.add_argument("--disable_cert_url_checks", action="store_true",
                               help="Disables verification of URL for certificate reference (optional)"
                               )

    # Command for 'decode_jws'
    jws_decoder = subparsers.add_parser("decode_jws", help="Run with path to file containing JWS")
    jws_decoder.add_argument("jws_file_path", type=str, help="Path to JWS file")
    jws_decoder.add_argument("--key", required=True, type=str, help="Path to private key file")
    jws_decoder.add_argument(
        "--password",
        type=str,
        default=None,
        help="Password for private key file (optional)"
    )

    # Parse the arguments
    args = parser.parse_args()

    print(f"Launching Test Suite based on {get_last_commit_hash()} commit. Details: {get_last_commit_details()}")

    if not running_as_root():
        print(f"⚠️ Test Suite have to be run as a root. ⚠️ Exiting...")
        return

    # Dispatch to the appropriate function
    if args.command == "validate":
        validate_configs(args.run_config, args.lab_config, args.lab_info,
                         args.test_config, args.test_info, args.launch_config)
    elif args.command == "gen_report":
        generate_report(args.json_file, args.report_type, args.filename, args.folder, args.detailed)
    elif args.command == "run":
        run(args.launch, args.use_rc, args.gen_rc)
    elif args.command == "generate_jws":
        print(generate_jws(json_source=args.json_file_path, cert_path=args.cert, key_path=args.key,
                           key_password=args.password, output_file=args.output_file, cert_url=args.cert_url,
                           disable_cert_url_checks=args.disable_cert_url_checks)
              )
    elif args.command == "decode_jws":
        print(decode_jws(args.jws_file_path, args.key, args.password))
    else:
        parser.print_help()


def graceful_shutdown(reason: str = "", exc: Exception | None = None) -> None:
    """
    Gracefully shuts down Test Suite execution.
    This function is safe to call multiple times; cleanup hooks run only once.
    """
    global _SHUTDOWN_ALREADY_RUN
    if _SHUTDOWN_ALREADY_RUN:
        return
    _SHUTDOWN_ALREADY_RUN = True

    try:
        print("\n[!] Graceful shutdown initiated")
        if reason:
            print(f"[!] Reason: {reason}")

        if exc is not None:
            print("[!] Unhandled exception (traceback):")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

        # Execute registered cleanup hooks
        run_cleanup()

        print("[+] Cleanup completed")

        if reason:
            print(f"[!] Reason: {reason}")

        print("[!] Please Contact Dev team in cause of Error")

    except Exception as cleanup_exc:
        # Must never raise from shutdown
        print("[!] ERROR during graceful shutdown (ignored):", cleanup_exc)


# def _signal_handler(signum, frame):
#     graceful_shutdown(f"Received signal {signum}")
#     raise SystemExit(130)
#
#
# signal.signal(signal.SIGINT, _signal_handler)   # Ctrl+C
# signal.signal(signal.SIGTERM, _signal_handler)  # kill / docker stop


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        graceful_shutdown("KeyboardInterrupt (Ctrl+C)")

    except Exception as e:
        graceful_shutdown("Unhandled exception", e)
