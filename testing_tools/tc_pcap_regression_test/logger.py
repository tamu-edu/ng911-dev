import os
from datetime import datetime

from test_suite.logger.error_parser_service import ErrorParserService
from test_suite.services.config.errors.wrong_configuration_error import (
    WrongConfigurationError,
)

_TEST_PREP_MESSAGE_PATTERNS = (
    "No pcap files could be matched to any variation",
    "src and dst ip addresses not found",
    "does not contain required parameters for filtering",
)

_CONFIG_PARSING_TRACE_PATTERNS = (
    "YAML parsing error",
    "config_service.py",
)


class PipelineLogWriter:
    """
    Five logs for the pcap pipeline:
      1. general.log          - discovery/matching stats (only when there's an issue) +
                                 final status per test
      2. config_errors.log    - lab_config / test_config validation errors
      3. pcap_errors.log      - pcap parsing errors (tshark/pyshark)
      4. traceback_errors.log - full traceback for unexpected/logic errors
      5. summary.log          - the run's SUMMARY block, on its own so tooling doesn't
                                 have to grep it out of general.log
    """

    def __init__(self, output_dir: str = "testing_tools/logs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.general_path = os.path.join(output_dir, "general.log")
        self.config_errors_path = os.path.join(output_dir, "config_errors.log")
        self.pcap_errors_path = os.path.join(output_dir, "pcap_errors.log")
        self.traceback_path = os.path.join(output_dir, "traceback_errors.log")
        self.summary_path = os.path.join(output_dir, "summary.log")
        for path in (
            self.general_path,
            self.config_errors_path,
            self.pcap_errors_path,
            self.traceback_path,
            self.summary_path,
        ):
            open(path, "w").close()

    @staticmethod
    def _ts() -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _write(self, path: str, text: str) -> None:
        with open(path, "a") as f:
            f.write(text.rstrip("\n") + "\n")

    # ---------------------------------------------------------------- Log 1
    def general(self, text: str) -> None:
        line = f"[{self._ts()}] {text}"
        print(line)
        self._write(self.general_path, line)

    # ---------------------------------------------------------------- Log 5
    def _summary_line(self, text: str) -> None:
        """Same shape as general() (timestamped, echoed to console for
        visibility during a live run) but written to summary.log instead of
        general.log."""
        line = f"[{self._ts()}] {text}"
        print(line)
        self._write(self.summary_path, line)

    def start(self, total_tests: int) -> None:
        self.general(f"=== run_tests started, {total_tests} tests ===")

    def discovery_status(
        self,
        test_id: str,
        has_lab_config: bool,
        has_test_config: bool,
        pcap_count: int,
    ) -> None:
        """Always printed, one block per test, before anything else runs —
        the baseline "is the data even here" check, so general.log reads
        top-to-bottom per test without cross-referencing config_errors.log."""
        self.general(test_id)
        self.general(f"  lab config: {'found' if has_lab_config else 'NOT FOUND'}")
        self.general(f"  test config: {'found' if has_test_config else 'NOT FOUND'}")
        pcap_status = (
            f"found ({pcap_count} file{'s' if pcap_count != 1 else ''})"
            if pcap_count
            else "NOT FOUND"
        )
        self.general(f"  pcap: {pcap_status}")

    def discovery(
        self,
        test_id: str,
        total_pcaps: int,
        excluded_pcaps: int,
        variations_total: int,
        variations_matched: int,
        unmatched: list[str],
    ) -> None:
        """Only log when there's something worth flagging: not all variations
        matched, or non-pass pcaps were found (they get excluded from the file list)."""
        if not unmatched and excluded_pcaps == 0:
            return
        msg = (
            f"{test_id}: found {total_pcaps} pcap(s), "
            f"{variations_matched}/{variations_total} variation(s) matched"
        )
        if excluded_pcaps:
            msg += f", {excluded_pcaps} non-pass pcap(s) skipped"
        if unmatched:
            msg += f", UNMATCHED: {', '.join(unmatched)}"
        self.general(msg)

    def outcome(self, test_id: str, status: str, detail: str = "") -> None:
        line = f"{test_id} - {status}"
        if detail:
            line += f"({detail})"
        self.general(line)

    def verdict_detail(self, test_id: str, test_oracle) -> None:
        """Per-variation / per-check breakdown for a non-PASSED verdict, so
        FAILED tests don't require manual digging into TestOracle by hand."""
        for variation in getattr(test_oracle, "variations", []):
            v_verdict = variation.get_scenario_verdict()
            if v_verdict is None or v_verdict.test_verdict.value == "PASSED":
                continue
            self.general(
                f"  {test_id} / {variation.name}: {v_verdict.test_verdict.value}"
            )
            for check in variation.intermediate_verdicts:
                if check.test_verdict.value == "PASSED":
                    continue
                self.general(
                    f"    - {check.test_name}: {check.error or check.test_verdict.value}"
                )

    def record_exception(self, test_id: str, e: Exception) -> str:
        """Classifies straight into the four pipeline stages (no separate
        post-run analysis step): pcap_parsing / config_parsing / test_prep /
        test_run."""
        if isinstance(e, (WrongConfigurationError, FileNotFoundError)):
            message = f"{type(e).__name__}: {e}"
            if any(p in str(e) for p in _TEST_PREP_MESSAGE_PATTERNS):
                category = "test_prep"
            else:
                category = "config_parsing"
            self.config_error(test_id, message)
        elif type(e).__module__.startswith("pyshark"):
            category = "pcap_parsing"
            self.pcap_error(test_id, f"{type(e).__name__}: {e}")
        else:
            parsed_error = ErrorParserService(
                e, note=f"Method: run_tests (test {test_id})"
            )
            report = parsed_error.get_report()
            if any(p in report for p in _CONFIG_PARSING_TRACE_PATTERNS):
                category = "config_parsing"
            else:
                category = "test_run"
            self.traceback_error(test_id, report)

        self.outcome(test_id, "aborted", f"{category}: {type(e).__name__}")
        return category

    def summary(self, results: list, found_tc: int = 0) -> None:
        from testing_tools.tc_pcap_regression_test.types.test_run_result import (
            RunStatus,
        )

        launched = len(results)
        passed = [
            r
            for r in results
            if r.status == RunStatus.FINISHED and r.verdict == "PASSED"
        ]
        failed = [
            r
            for r in results
            if r.status == RunStatus.FINISHED and r.verdict != "PASSED"
        ]
        missing_lab_config = [
            r for r in results if r.status == RunStatus.MISSING_LAB_CONFIG
        ]
        missing_test_config = [
            r for r in results if r.status == RunStatus.MISSING_TEST_CONFIG
        ]
        missing_pcap = [r for r in results if r.status == RunStatus.MISSING_PCAP]
        aborted = [r for r in results if r.status == RunStatus.ABORTED]

        stage_ids: dict[str, list[str]] = {
            "pcap_parsing": [],
            "config_parsing": [],
            "test_prep": [],
            "test_run": [],
        }
        for r in aborted:
            if r.error_category in stage_ids:
                stage_ids[r.error_category].append(r.test_id)

        def _line(label: str, ids: list[str], indent: str = "  ") -> None:
            self._summary_line(f"{indent}{label}: {len(ids)}")
            if ids:
                self._summary_line(f"{indent}  - {', '.join(ids)}")

        self._summary_line("=== SUMMARY ===")
        self._summary_line(f"Found TC: {found_tc}")
        self._summary_line(f"Launched TC: {launched}")
        _line("TC passed", [r.test_id for r in passed], indent="")
        _line(
            "TC failed (ran, verdict not PASSED)",
            [r.test_id for r in failed],
            indent="",
        )
        _line(
            "TC missing lab config (skipped, not attempted)",
            [r.test_id for r in missing_lab_config],
            indent="",
        )
        _line(
            "TC missing test config (skipped, not attempted)",
            [r.test_id for r in missing_test_config],
            indent="",
        )
        _line(
            "TC missing pcap (skipped, not attempted)",
            [r.test_id for r in missing_pcap],
            indent="",
        )
        self._summary_line("Errors:")
        _line("pcap parsing", stage_ids["pcap_parsing"])
        _line("config parsing", stage_ids["config_parsing"])
        _line("test preparation", stage_ids["test_prep"])
        _line("test run", stage_ids["test_run"])

    # ---------------------------------------------------------------- Log 2
    def config_error(self, test_id: str, message: str) -> None:
        self._write(self.config_errors_path, f"[{self._ts()}] {test_id}: {message}")

    # ---------------------------------------------------------------- Log 3
    def pcap_error(self, test_id: str, message: str) -> None:
        self._write(self.pcap_errors_path, f"[{self._ts()}] {test_id}: {message}")

    # ---------------------------------------------------------------- Log 4
    def traceback_error(self, test_id: str, full_report: str) -> None:
        self._write(
            self.traceback_path,
            f"[{self._ts()}] {test_id}\n{full_report}\n{'-' * 80}",
        )
