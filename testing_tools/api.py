import json
import os

from test_suite.services.config.errors.wrong_configuration_error import (
    WrongConfigurationError,
)
from test_suite.services.test_services.test_oracle import TestOracle

from testing_tools.tc_pcap_regression_test.logger import PipelineLogWriter
from testing_tools.tc_pcap_regression_test.pcap_run_config_manager import (
    PcapRunConfigManager,
)
from testing_tools.tc_pcap_regression_test.test_discovery_service import (
    TestDiscoveryService,
)
from testing_tools.tc_pcap_regression_test.types.test_run_result import (
    RunStatus,
    TCPRResult,
)


def run_single_test_pcap(test_id: str, log: PipelineLogWriter | None = None):
    lab_config_path = TestDiscoveryService.get_lab_config_path(test_id)
    if lab_config_path is None:
        raise WrongConfigurationError(f"No lab_config found for test '{test_id}'")
    lab_config = PcapRunConfigManager.load_lab_config(lab_config_path)

    pcap_dir = os.path.join(TestDiscoveryService.PCAPS_DIR, test_id)
    all_pcap_files = TestDiscoveryService.get_pcap_files(test_id)
    usable_pcap_files, excluded_pcap_files = PcapRunConfigManager.filter_to_pass_pcaps(
        all_pcap_files
    )

    result = PcapRunConfigManager.build_run_config(
        test_id=test_id,
        lab_config=lab_config,
        pcap_dir=pcap_dir,
        pcap_files=usable_pcap_files,
    )

    if log:
        matched = len(result.run_config.tests[0].variations)
        log.discovery(
            test_id,
            total_pcaps=len(all_pcap_files),
            excluded_pcaps=len(excluded_pcap_files),
            variations_total=matched + len(result.unmatched_variations),
            variations_matched=matched,
            unmatched=result.unmatched_variations,
        )

    run_config = result.run_config
    os.makedirs(os.path.join(run_config.output_folder, "pcaps"), exist_ok=True)

    TestOracle.variations = []
    test_oracle = TestOracle(
        lab_config=lab_config, run_config=run_config, test_id=test_id
    )
    test_oracle.prepare_variation_results()
    test_oracle.asses_var_results()
    test_oracle.calculate_general_verdict()

    return test_oracle, result.unmatched_variations


def run_tests(
    tests: list[str] | None = None, report_file: str | None = None
) -> list[TCPRResult]:
    test_ids = tests or TestDiscoveryService.discover_all_test_ids()
    results: list[TCPRResult] = []
    log = PipelineLogWriter()
    log.start(len(test_ids))

    for test_id in test_ids:
        has_lab_config = bool(TestDiscoveryService.get_lab_config_path(test_id))
        has_test_config = bool(TestDiscoveryService.get_test_config_path(test_id))
        pcap_files = TestDiscoveryService.get_pcap_files(test_id)
        log.discovery_status(test_id, has_lab_config, has_test_config, len(pcap_files))

        if not pcap_files:
            log.outcome(test_id, RunStatus.MISSING_PCAP.value)
            results.append(TCPRResult(test_id=test_id, status=RunStatus.MISSING_PCAP))
            continue
        if not has_lab_config:
            log.outcome(test_id, RunStatus.MISSING_LAB_CONFIG.value)
            results.append(
                TCPRResult(test_id=test_id, status=RunStatus.MISSING_LAB_CONFIG)
            )
            continue
        if not has_test_config:
            log.outcome(test_id, RunStatus.MISSING_TEST_CONFIG.value)
            results.append(
                TCPRResult(test_id=test_id, status=RunStatus.MISSING_TEST_CONFIG)
            )
            continue

        try:
            test_oracle, unmatched_variations = run_single_test_pcap(test_id, log=log)
            verdict = test_oracle.get_general_verdict()
            log.outcome(test_id, RunStatus.FINISHED.value, verdict)
            if verdict != "PASSED":
                log.verdict_detail(test_id, test_oracle)
            results.append(
                TCPRResult(
                    test_id=test_id,
                    status=RunStatus.FINISHED,
                    verdict=verdict,
                    warnings=unmatched_variations or None,
                )
            )
        except Exception as e:
            category = log.record_exception(test_id, e)
            results.append(
                TCPRResult(
                    test_id=test_id,
                    status=RunStatus.ABORTED,
                    error=f"{type(e).__name__}: {e}",
                    error_category=category,
                )
            )
            continue

    log.summary(results, found_tc=len(test_ids))

    if report_file:
        with open(report_file, "w") as f:
            json.dump(
                [
                    {
                        "test_id": r.test_id,
                        "status": r.status.value,
                        "verdict": r.verdict,
                        "error": r.error,
                        "error_category": r.error_category,
                        "warnings": r.warnings,
                    }
                    for r in results
                ],
                f,
                indent=2,
            )

    return results
