import shutil
import sys
import os
import importlib
from pathlib import Path
from typing import List, Optional, Any

from services.aux_services.test_list_services import generate_test_list_for_variation
from services.config.config_enum import ScenarioMode
from services.config.types.lab_config import LabConfig
from services.pcap_service import PcapCaptureService
from services.config.types.run_config import RunConfig, RunVariation, RunTest
from logger.logger_service import LoggingMeta
from services.test_services.live_variation_service import LiveVariationService
from services.test_services.test_assessment_service import TestAssessmentService
from services.test_services.types.test_types import OracleTestVariation
from services.test_services.types.test_verdict import VerdictType
from services.test_services.pre_post_amble_service import PrePostAmbleService
from services.cleanup_registry import register_cleanup

# Including our tests modules which are in a folder named "tests" to sys.path
module_directory = os.path.abspath("test_suite/tests")
if module_directory not in sys.path:
    sys.path.append(module_directory)


class TestOracle(metaclass=LoggingMeta):
    """
    TestOracle service is a class to conduct tests using provided configs
    """

    _test_id: str
    _lab_config: LabConfig
    variations: List[OracleTestVariation] = []
    general_verdict: Optional[VerdictType]

    def __init__(self, lab_config: LabConfig, run_config: RunConfig, test_id: str):
        self._test_id = test_id
        self._lab_config = lab_config
        self._run_config = run_config
        self.tests: List[Any] = []
        self._prepare_variation_results()
        self.general_verdict = None

    def __create_test_assessment_service_list(
        self, test_list: list, pcap_service: PcapCaptureService, variation: RunVariation
    ) -> list:
        """
        Wraps test_list in TestConductionService
        """
        return [
            TestAssessmentService(
                name=f"{variation.name}_{test.get('test_id').split('_', 1)[0]}",
                tests_list=importlib.import_module(test.get("test_id")).get_test_list(
                    pcap_service,
                    self._lab_config,
                    variation.filtering_options,
                    variation,
                ),
                subtests_list=test.get("subtests"),
            )
            for test in test_list
        ]

    def _prepare_oracle_test_var_results(
        self,
        run_test: RunTest,
        variation: RunVariation,
        capture=None,
        pcap_file: str | None = None,
        ssl_keys_file_path: str | None = None,
    ):

        if capture:
            variation_pcap_service = PcapCaptureService(capture=capture)
        elif pcap_file:
            variation_pcap_service = PcapCaptureService(
                pcap_file=pcap_file, ssl_keys_file_path=ssl_keys_file_path
            )
        else:
            raise ValueError(
                "Cannot prepare oracle test scen -> capture or pcap_file is missing"
            )

        print(
            f"🧪 Loaded capture contains {variation_pcap_service.get_capture_len()} packets."
        )

        test_list = generate_test_list_for_variation(
            run_test.requirements, variation.name
        )

        return (
            OracleTestVariation(
                name=variation.name,
                description=variation.description,
                tests=self.__create_test_assessment_service_list(
                    test_list, variation_pcap_service, variation
                ),
            ),
            variation_pcap_service,
        )

    def __copy_pcap_to_output_folder(self, file_path: str, filename: str):
        try:
            destination = Path(self._run_config.output_folder + "/pcaps") / filename
            shutil.copy(str(file_path), str(destination))
            print(f"Moved: {file_path} -> {destination}")
        except Exception:
            print(f"Moved: {file_path} failed")

    def __copy_ssl_keys_file_path_to_output_folder(self, file_path: str, filename: str):
        try:
            destination = Path(self._run_config.output_folder) / filename
            shutil.copy(str(file_path), str(destination))
            print(f"Moved: {file_path} -> {destination}")
        except Exception:
            print(f"Moved: {file_path} failed")

    def _make_variation_not_run(self, run_variation):
        self.variations.append(
            OracleTestVariation.from_not_run_var(
                name=run_variation.name, description=run_variation.description
            )
        )

    def _prepare_variation_results(self):
        # TODO add test name to distinct in outprint

        for run_test in self._run_config.tests:
            print(f"📋 Preparing tests for {run_test.name}...")
            pcap_path = None
            pcap_ssl_keys_file_path = None

            # Firstly we need to check if there are any preamble
            _not_run_variations: List[Any] = []
            print("[DEBUG] Starting preamble")
            print(f"[DEBUG] run_test.preamble_list = {str(run_test.preamble_list)}")
            for _preamble in run_test.preamble_list:
                _preamble_service = PrePostAmbleService(**_preamble.to_dict())
                try:
                    _preamble_service.run_method(
                        {
                            "lab_config": self._lab_config.to_dict(),
                            "run_config": self._run_config.to_dict(),
                        }
                    )
                except Exception:
                    _not_run_variations.extend(_preamble_service.required_for)

            for run_variation in run_test.variations:
                if run_variation.name in _not_run_variations:
                    self._make_variation_not_run(run_variation)
                    continue

                _var_not_run = False
                # TODO start GG API impl here

                if run_variation.mode.lower() == ScenarioMode.PCAP.value:
                    print(
                        f"🤓 Analyzing PCAP file of {run_variation.name} variation..."
                    )
                    pcap_path = run_variation.pcap_file
                    pcap_ssl_keys_file_path = run_variation.ssl_keys_file_path
                    self.__copy_pcap_to_output_folder(
                        pcap_path, pcap_path.split("/")[-1]
                    )
                    if pcap_ssl_keys_file_path:
                        self.__copy_ssl_keys_file_path_to_output_folder(
                            pcap_ssl_keys_file_path,
                            pcap_ssl_keys_file_path.split("/")[-1],
                        )

                elif run_variation.mode.lower() == ScenarioMode.CAPTURE.value:
                    live_var_service = LiveVariationService(
                        output_folder=self._run_config.output_folder,
                        lab_config=self._lab_config,
                        run_variation=run_variation,
                        test_id=self._test_id,
                    )
                    register_cleanup(
                        f"Cleanup LiveVariationService {run_variation.name}",
                        live_var_service.cleanup,
                    )
                    live_var_service.run()
                    pcap_path = live_var_service.get_pcap_path()
                    _var_not_run = live_var_service.get_variation_not_run_flag()

                if pcap_path:
                    _var, variation_pcap_service = (
                        self._prepare_oracle_test_var_results(
                            pcap_file=pcap_path,
                            ssl_keys_file_path=pcap_ssl_keys_file_path,
                            run_test=run_test,
                            variation=run_variation,
                        )
                    )
                    self.variations.append(_var)
                    variation_pcap_service.close_capture()
                else:
                    if _var_not_run:
                        self._make_variation_not_run(run_variation)

            # Firstly we need to check if there are any postamble
            for _postamble in run_test.postamble_list:
                _postamble_service = PrePostAmbleService(**_postamble.to_dict())
                _postamble_service.run_method(
                    {
                        "lab_config": self._lab_config.to_dict(),
                        "run_config": self._run_config.to_dict(),
                    }
                )

        print(f"📦 Total tests prepared prepared: {len(self.variations)}")

    def asses_var_results(self):
        for scenario in self.variations:
            print(f"Testing {scenario.name} variation...")
            for test in scenario.tests:
                test.prepare_intermediate_verdicts()
                scenario.add_intermediate_verdicts(test.get_intermediate_verdicts())
            scenario.calculate_scenario_verdict()

    def calculate_general_verdict(self):
        # Firstly we need to check if there are any FAILED
        for scenario in self.variations:
            if scenario.get_scenario_verdict().test_verdict == VerdictType.FAILED:
                self.general_verdict = VerdictType.FAILED
                return
            # Then we can check on other variants
            if scenario.get_scenario_verdict().test_verdict in [
                VerdictType.NOT_RUN,
                VerdictType.INC,
            ]:
                self.general_verdict = VerdictType.INC

        # if nothing is Failed or INC|NOT_RUN  => Passed
        if self.general_verdict is None:
            self.general_verdict = VerdictType.PASSED

    # def get_test_config(self) -> TestConfig:
    #     return self._test_config

    def get_run_config(self) -> RunConfig:
        return self._run_config

    def get_test_id(self) -> str:
        return self._test_id

    def get_general_verdict(self):
        if self.general_verdict is None:
            self.calculate_general_verdict()
        return self.general_verdict.value
