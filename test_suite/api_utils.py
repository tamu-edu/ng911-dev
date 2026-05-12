import os
import shutil
import ctypes
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from logger.logger_service import LoggerService, TeeStream
from services.cleanup_registry import register_cleanup
from services.config.config_service import ConfigService
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.launch_config import LaunchTest, LaunchConfig
from services.config.types.forward_conduit_config import ForwardConduit


def running_as_root() -> bool:
    if os.name == "nt":  # Windows
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
        except Exception:
            return False
    else:  # Unix-like
        return os.getuid() == 0


def get_last_commit_hash():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True
    )
    return result.stdout.strip()


def get_last_commit_details():
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=format:%h - %an, %ar : %s"],
        stdout=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def copy_file_to_output_folder(file_path: str, filename: str, output_folder_path: str):
    destination = Path(output_folder_path) / filename
    shutil.copy(str(file_path), str(destination))
    print(f"Moved: {file_path} -> {destination}")


def parse_lab_config(test: LaunchTest, launch_config: LaunchConfig):
    print(f"Validating and parsing LAB CONFIG -> {test.lab_config}")
    if not ConfigService.validate_lab_config(test.lab_config):
        print("❌ LAB CONFIG parsing failed.")
        raise WrongConfigurationError(
            f"Impossible to run {test.iut.name} test due to "
            f"LAB CONFIG -> {test.lab_config} errors"
        )
    print("✅ LAB CONFIG successfully parsed.")

    lab_config = LabConfig.from_dict(ConfigService.parse_config_file(test.lab_config))
    lab_config.validate()
    copy_file_to_output_folder(
        test.lab_config,
        f"{test.iut.name}_lab_config.yaml",
        launch_config.output_folder + "/configs",
    )
    copy_file_to_output_folder(
        launch_config.global_config.lab_info,
        "lab_info.yaml",
        launch_config.output_folder + "/configs",
    )

    return lab_config


def parse_launch_config(launch_config_file: str):
    print(f"Validating and parsing Launch Configuration -> {launch_config_file}")
    if not ConfigService.validate_launch_config(launch_config_file):
        print("❌ Launch Configuration parsing failed.")
        return
    print("✅ Launch Configuration successfully parsed.")
    return LaunchConfig.from_dict(ConfigService.parse_config_file(launch_config_file))


def parse_forward_conduit_config(forward_conduit_config: str):
    print(
        f"Validating and parsing Forward Conduits Configuration -> {forward_conduit_config}"
    )
    if not ConfigService.validate_forward_conduit_config(forward_conduit_config):
        print("❌ Forward Conduits Configuration parsing failed.")
        return
    print("✅ Forward Conduits Configuration successfully parsed.")
    return ForwardConduit.from_dict(
        ConfigService.parse_config_file(forward_conduit_config)
    )


def create_test_id(launch_config: LaunchConfig) -> str:
    test_id = (
        f"{launch_config.global_config.report_files.prefix}_"
        f"{datetime.now().strftime('%Y-%m-%dT%H%M%S')}"
    )
    if launch_config.global_config.report_files.suffix:
        test_id += f"_{launch_config.global_config.report_files.suffix}"
    return test_id


def log_environment_info(output_folder: str):
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    log_path = os.path.join(output_folder, "environment_log.txt")
    log_lines = []

    def run_command(cmd):
        try:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return result.stdout.strip() or result.stderr.strip()
        except Exception as e:
            return f"Error running {' '.join(cmd)}: {e}"

    # Timestamp
    log_lines.append("--- Environment Info Log ---")
    log_lines.append(f"Timestamp: {datetime.now().isoformat()}")
    log_lines.append("")

    log_lines.append(
        f"Launching Test Suite based on {get_last_commit_hash()} commit. "
        f"Details: {get_last_commit_details()}"
    )
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
    logs_folder_suffix = "/logs"

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


def prepare_environment(
    launch_config: LaunchConfig, launch_config_file: str, test_id: str
):
    launch_config.add_test_id_to_output_folder(test_id=test_id)
    launch_config.add_test_id_to_log_output(test_id=test_id)

    os.makedirs(launch_config.output_folder, exist_ok=True)
    os.makedirs(launch_config.output_folder + "/logs", exist_ok=True)
    os.makedirs(launch_config.output_folder + "/pcaps", exist_ok=True)
    os.makedirs(launch_config.output_folder + "/configs", exist_ok=True)
    Path(launch_config.global_config.log.output_file).touch(exist_ok=True)

    log_environment_info(launch_config.output_folder + "/logs")

    register_cleanup(
        "Move root .log files into output/logs",
        lambda: move_all_root_log_to_output_folder(
            launch_config.output_folder + "/logs"
        ),
    )
    register_cleanup(
        "Move output_folder .log files into ./logs",
        lambda: move_all_output_folder_log_to_logs_folder(
            launch_config.output_folder + "/logs"
        ),
    )

    copy_file_to_output_folder(
        launch_config_file,
        "launch_config.yaml",
        launch_config.output_folder + "/configs",
    )


def logger_setup(launch_config: LaunchConfig):
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


def stop_logger(launch_config: LaunchConfig):
    LoggerService.shutdown_logging()
    move_all_root_log_to_output_folder(launch_config.output_folder + "/logs")
    move_all_output_folder_log_to_logs_folder(launch_config.output_folder)
