import contextlib
import copy
import io
import os
import re
from dataclasses import dataclass

from test_suite.services.config.config_enum import ScenarioMode
from test_suite.services.config.config_service import ConfigService
from test_suite.services.config.errors.wrong_configuration_error import (
    WrongConfigurationError,
)
from test_suite.services.config.run_config_service import (
    TEST_CONF_FOLDER,
    RunConfigService,
)
from test_suite.services.config.types.lab_config import LabConfig
from test_suite.services.config.types.run_config import (
    GlobalConfig,
    IdSummary,
    IUTSummary,
    LabSummary,
    LogConfig,
    MessageFilter,
    ReportFile,
    RunConfig,
    RunRequirement,
    RunTest,
    RunVariation,
    SupplierSummary,
    TestEnvSummary,
)
from test_suite.services.config.types.test_config import TestConfig


@dataclass
class PcapRunConfigResult:
    run_config: RunConfig
    unmatched_variations: list[str]


class PcapRunConfigManager:
    _PCAP_NAME_PATTERN = re.compile(r"var_?(?P<idx>\d+)_pass[_.]", re.IGNORECASE)
    _PASS_MARKER = re.compile(r"(_pass[_.]|\bpass-)", re.IGNORECASE)

    @classmethod
    def resolve_pcap_to_variation_index(cls, pcap_filename: str) -> int | None:
        m = cls._PCAP_NAME_PATTERN.search(pcap_filename)
        return int(m.group("idx")) if m else None

    @classmethod
    def resolve_pcaps_for_test(
        cls, pcap_files: list[str], variations: list
    ) -> dict[int, str]:
        result: dict[int, str] = {}
        for f in pcap_files:
            idx = cls.resolve_pcap_to_variation_index(f)
            if idx is None or not (0 < idx <= len(variations)):
                continue
            result.setdefault(idx - 1, f)
        return result

    @classmethod
    def filter_to_pass_pcaps(cls, pcap_files: list[str]) -> tuple[list[str], list[str]]:
        keep, excluded = [], []
        for f in pcap_files:
            if cls._PASS_MARKER.search(f):
                keep.append(f)
            else:
                excluded.append(f)
        return keep, excluded

    @staticmethod
    def get_iut_type(test_id: str) -> str:
        m = re.match(r"^(.+)_(\d+)$", test_id)
        return m.group(1) if m else test_id

    @classmethod
    def load_lab_config(cls, lab_config_path: str) -> LabConfig:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            is_valid = ConfigService.validate_lab_config(lab_config_path)

        if not is_valid:
            hard_errors = [
                line
                for line in buf.getvalue().splitlines()
                if line.strip().startswith("Error in")
            ]
            for line in hard_errors:
                print(line)
            raise WrongConfigurationError(
                f"Impossible to run test due to LAB CONFIG -> {lab_config_path} errors"
            )

        lab_config = LabConfig.from_dict(
            ConfigService.parse_config_file(lab_config_path)
        )
        lab_config.validate()
        return lab_config

    @classmethod
    def _build_global_config(cls, test_id: str, iut_type: str) -> GlobalConfig:
        return GlobalConfig(
            type="conformance",
            report_files=ReportFile(
                output_folder_path="",
                prefix=iut_type,
                suffix=f"{test_id}_AUTO",
                detailed_view=True,
                types=[],
            ),
            log=LogConfig(level="DEBUG", output_file=f"{test_id}_DEBUG.log"),
            comments=[],
            id_summary=IdSummary(
                lab=LabSummary(
                    name="AUTO",
                    accred_status="",
                    accred_ref="",
                    accred_auth="",
                    addr_line_1="",
                    addr_line_2="",
                    city="",
                    state="",
                    country="",
                    zip="",
                    url="",
                    eng_name="AUTO",
                ),
                supplier=SupplierSummary(
                    name="AUTO",
                    addr_line_1="",
                    addr_line_2="",
                    city="",
                    state="",
                    country="",
                    zip="",
                    url="",
                ),
                iut=IUTSummary(
                    type=iut_type,
                    name=f"IUT_{iut_type}",
                    version="AUTO",
                    date_of_receipt="",
                    location="",
                    cs_id=test_id,
                ),
                test_env=TestEnvSummary(
                    ixit_id="",
                    test_method="",
                    spec_name="",
                    spec_version="",
                    test_period_start="",
                    test_period_end="",
                ),
            ),
        )

    @classmethod
    def _build_run_variation(
        cls,
        variation,
        mode: ScenarioMode,
        lab_config: LabConfig,
        pcap_file: str | None = None,
    ) -> RunVariation:
        return RunVariation(
            name=variation.name,
            mode=mode,
            description=variation.description,
            interfaces=variation.interfaces,
            pcap_file=pcap_file,
            params=copy.deepcopy(variation.params),
            filtering_options=(
                [
                    MessageFilter(**f) if isinstance(f, dict) else f
                    for f in variation.filtering_options
                ]
                if variation.filtering_options
                else RunConfigService.get_filtering_options(
                    variation.params, lab_config
                )
            ),
        )

    @classmethod
    def build_run_config(
        cls,
        test_id: str,
        lab_config: LabConfig,
        pcap_dir: str,
        pcap_files: list[str],
    ) -> PcapRunConfigResult:
        test_config_path = f"{TEST_CONF_FOLDER}/test_config_{test_id.lower()}.yaml"

        if not ConfigService.validate_test_config(test_config_path):
            raise WrongConfigurationError(
                f"Impossible to run test due to TEST CONFIG -> {test_config_path} errors"
            )

        test_config = TestConfig.from_dict(
            ConfigService.parse_config_file(test_config_path)
        )

        if not test_config.conformance.tests:
            raise WrongConfigurationError(
                f"test_config for '{test_id}' has no tests defined"
            )

        _test = test_config.conformance.tests[0]
        variations = _test.variations

        resolved = cls.resolve_pcaps_for_test(pcap_files, variations)
        unmatched_variations = [
            v.name for i, v in enumerate(variations) if i not in resolved
        ]

        run_variations = []
        for idx, _variation in enumerate(variations):
            pcap_filename = resolved.get(idx)
            if pcap_filename is None:
                continue

            full_pcap_path = os.path.join(pcap_dir, pcap_filename)
            if not os.path.exists(full_pcap_path):
                raise WrongConfigurationError(
                    f"Resolved pcap file for variation '{_variation.name}' does not exist on disk: {full_pcap_path}"
                )

            run_variations.append(
                cls._build_run_variation(
                    _variation,
                    ScenarioMode.PCAP,
                    lab_config,
                    pcap_file=full_pcap_path,
                )
            )

        if not run_variations:
            raise WrongConfigurationError(
                f"No pcap files could be matched to any variation for '{test_id}' — "
                f"check filenames follow the 'var_N_pass_' naming convention. "
                f"Expected variations: {', '.join(unmatched_variations)}"
            )

        iut_type = cls.get_iut_type(test_id)

        run_config = RunConfig(
            output_folder=f"test_suite/pcaps/{test_id}/results",
            global_config=cls._build_global_config(test_id, iut_type),
            tests=[
                RunTest(
                    name=f"{iut_type}_{test_id}",
                    requirements=[
                        RunRequirement(name=r.name, variations=r.variations)
                        for r in _test.requirements
                    ],
                    variations=run_variations,
                    preamble_list=_test.preamble_list,
                    postamble_list=_test.postamble_list,
                )
            ],
        )

        return PcapRunConfigResult(
            run_config=run_config, unmatched_variations=unmatched_variations
        )
