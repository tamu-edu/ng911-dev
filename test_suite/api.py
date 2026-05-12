import json

from api_utils import (
    copy_file_to_output_folder,
    parse_lab_config,
    parse_launch_config,
    create_test_id,
    prepare_environment,
    logger_setup,
    stop_logger,
    parse_forward_conduit_config,
)
from services.config.errors.wrong_configuration_error import WrongConfigurationError
from services.config.types.lab_config import LabConfig
from services.config.types.launch_config import LaunchConfig, LaunchTest
from services.test_services.test_oracle import TestOracle
from services.config.run_config_service import RunConfigService
from services.config.config_service import ConfigService
from services.report.report_service import ReportService
from services.aux_services.json_services import generate_jws as gen_jqws
from services.aux_services.json_services import decode_jws as dec_jws


def generate_jws(
    json_source,
    cert_path: str | None = None,
    key_path: str | None = None,
    key_password: str | None = None,
    output_file: str | None = None,
    cert_url: str | None = None,
    disable_cert_url_checks=False,
):
    return gen_jqws(
        json_source=json_source,
        cert_path=cert_path,
        key_path=key_path,
        key_password=key_password,
        output_file=output_file,
        cert_url=cert_url,
        disable_cert_url_checks=disable_cert_url_checks,
    )


def decode_jws(
    jws_source: dict | str, key_path: str | None = None, key_password: str | None = None
):
    return dec_jws(
        jws_source=jws_source,
        key_path=key_path,
        key_password=key_password,
    )


def validate_configs(
    run_config: str | None = None,
    lab_config: str | None = None,
    lab_info: str | None = None,
    test_config: str | None = None,
    test_info: str | None = None,
    launch_config: str | None = None,
    output_path: str | None = None,
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


def generate_report(
    json_file: str,
    report_type: str,
    filename: str,
    output_folder_path: str = "",
    is_detailed: bool = False,
):
    with open(json_file) as json_data:
        data = json.load(json_data)
        data["detailed_view"] = is_detailed

        report_service = ReportService(
            output_directory=output_folder_path, report_data=data
        )

        report_service.generate_report(report_type, filename)


def _gen_rc(
    launch_config: LaunchConfig, test: LaunchTest, lab_config: LabConfig, gen_rc: str
):
    print(f"Generating RUN CONFIG -> {gen_rc}")
    try:
        _, _format = gen_rc.split(".")
        run_config_service = RunConfigService.from_launch_config(
            launch_config, test, lab_config
        )
        run_config_service.generate_run_config_file(
            file_format=_format.lower(), path=gen_rc
        )
        print("✅ RUN CONFIG generated successfully.")
    except Exception:
        print("❌ RUN CONFIG generation failed -> {e}")


def _use_rc(
    use_rc: str,
    launch_config: LaunchConfig,
    lab_config_interfaces: dict,
    test: LaunchTest,
):
    print(f"Validating and parsing RUN CONFIG -> {use_rc}")
    if not ConfigService.validate_run_config(use_rc):
        print("❌ RUN CONFIG parsing failed.")
        raise WrongConfigurationError(
            f"Impossible to run {test.iut.name} test due to "
            f"RUN CONFIG -> {use_rc} errors"
        )
    print("✅ RUN CONFIG successfully parsed.")

    run_config_service = RunConfigService.from_dict(
        ConfigService.parse_config_file(use_rc)
    )
    run_config_service.get_run_config().output_folder = launch_config.output_folder

    is_all_data_present, comment = run_config_service.verify_interface_data_presence(
        lab_config_interfaces
    )
    if not is_all_data_present:
        print(f"❌{comment}")
        return

    copy_file_to_output_folder(
        use_rc, "run_config.yaml", launch_config.output_folder + "/configs"
    )

    return run_config_service


def create_rc(launch_config: LaunchConfig, test: LaunchTest, lab_config: LabConfig):
    run_config_service = RunConfigService.from_launch_config(
        launch_config, test, lab_config
    )

    _path = f"{launch_config.output_folder}"
    if _path[-1] == "/":
        _path += "run_config.yaml"
    else:
        _path += "/run_config.yaml"
    run_config_service.generate_run_config_file(file_format="yaml", path=_path)
    return run_config_service


def run(launch_config_file: str, use_rc: str | None = None, gen_rc: str | None = None):

    launch_config = parse_launch_config(launch_config_file)

    test_id = create_test_id(launch_config)

    prepare_environment(launch_config, launch_config_file, test_id)

    logger_setup(launch_config)

    for test in launch_config.tests:

        lab_config = parse_lab_config(test, launch_config)
        lab_config_interfaces = lab_config.get_interfaces_data()

        if gen_rc:
            _gen_rc(launch_config, test, lab_config, gen_rc)
            return

        if use_rc:
            run_config_service = _use_rc(
                use_rc, launch_config, lab_config_interfaces, test
            )
        else:
            run_config_service = create_rc(launch_config, test, lab_config)

        forward_conduit_config = None
        if (
            hasattr(test, "forward_conduit_config")
            and launch_config.global_config.type == "interoperability"
        ):
            forward_conduit_config = parse_forward_conduit_config(
                test.forward_conduit_config
            )

        test_oracle = TestOracle(
            lab_config=lab_config,
            run_config=run_config_service.get_run_config(),
            test_id=test_id,
            fwd_conduit_config=forward_conduit_config,
        )
        test_oracle.prepare_variation_results()
        test_oracle.asses_var_results()

        # Verdict generating.
        test_oracle.calculate_general_verdict()

        report_service = ReportService(
            output_directory=(
                launch_config.global_config.report_files.output_folder_path
                or launch_config.output_folder
                or None
            ),
            test_oracle=test_oracle,
        )

        for report_type in launch_config.global_config.report_files.types:
            print(f"Generating report file -> Report_{test_id}.{report_type}")
            report_service.generate_report(report_type, f"Report_{test_id}")

        stop_logger(launch_config)
        report_service.print_report()
