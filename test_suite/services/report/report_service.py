import importlib
import sys
from typing import List, Any

from pyfiglet import Figlet
import xml.etree.ElementTree as ElTree
import json
import csv
import os
from datetime import datetime

from docxtpl import DocxTemplate, RichText

from .format_types.reportlab_pdf import generate_pdf_with_reportlab
from .report_enums import ReportType

from services.test_services.types.test_verdict import VerdictType
from services.config.schemas.requirements_schema import REQUIREMENTS_SCHEMA
from test_suite import _TS_VERSION
from ..config.types.run_config import RunConfig
from ..test_services.test_oracle import TestOracle

module_directory = os.path.abspath("test_suite/tests")
if module_directory not in sys.path:
    sys.path.append(module_directory)

DOCX_TEMPLATE = "test_suite/services/report/templates/doc_template.docx"
PDF_TEMPLATE = "test_suite/services/report/templates/pdf_template.html"


def add_run_style(verdict: str) -> RichText:
    rt = RichText()
    if verdict == "PASSED":
        rt.add(verdict, color="008000")  # green
    elif verdict == "FAILED":
        rt.add(verdict, color="FF0000")  # red
    else:
        rt.add(verdict)
    return rt


class ReportService:
    report_data: dict = {}
    output_directory: str = ""
    test_oracle = None

    def __init__(
        self,
        output_directory: str = "",
        test_oracle: TestOracle | None = None,
        report_data: dict | None = None,
    ):

        if test_oracle:
            self.from_test_oracle(test_oracle)

        if report_data:
            self.from_json_data(report_data)

        if not test_oracle and not report_data:
            raise ValueError("test_oracle or report_data is missing")

        if output_directory:
            if output_directory[-1] == "/":
                self.output_directory = output_directory
            else:
                self.output_directory = output_directory + "/"
            os.makedirs(output_directory, exist_ok=True)

        self._generate_json(self.output_directory + "report_data.json")

    def from_test_oracle(self, test_oracle):
        """Initialize with a TestOracle object."""
        self.test_oracle: TestOracle = test_oracle
        self._generate_report_data()

    def from_json_data(self, json_data: dict):
        """Initialize with a json data."""
        self.report_data = json_data

    def generate_report(self, report_format: str, filename: str):
        """Generate a report in the specified format."""
        if report_format.lower() == ReportType.PDF.value:
            self._generate_pdf(
                self.output_directory + filename + "." + report_format.lower()
            )
        elif report_format.lower() == ReportType.DOCUMENT.value:
            self._generate_docx(
                self.output_directory + filename + "." + report_format.lower()
            )
        elif report_format.lower() == ReportType.XML.value:
            self._generate_xml(
                self.output_directory + filename + "." + report_format.lower()
            )
        elif report_format.lower() == ReportType.CSV.value:
            self._generate_csv(
                self.output_directory + filename + "." + report_format.lower()
            )
        else:
            raise ValueError(
                f"Unsupported report format. Use one of {ReportType.list()}"
            )

    def __get_var_description(self, var_name: str) -> str:
        if self.test_oracle:
            run_config: RunConfig = self.test_oracle.get_run_config()
            for test in run_config.tests:
                for var in test.variations:
                    if var.name == var_name:
                        return var.description
        return ""

    def _get_all_variations_names(self, variations):

        return {
            "names": [var.name for var in variations],
            "descriptions": {
                var.name: self.__get_var_description(var.name) for var in variations
            },
        }

    @staticmethod
    def _calculate_check_verdict(variations):
        _final_check_verdict = VerdictType.PASSED.value

        for var in variations:
            if var.get("verdict") == VerdictType.FAILED.value:
                return VerdictType.FAILED.value

            if var.get("verdict") == VerdictType.INC.value:
                _final_check_verdict = VerdictType.INC.value
            if (
                var.get("verdict") == VerdictType.NOT_RUN.value
                and _final_check_verdict != VerdictType.INC.value
            ):
                return VerdictType.NOT_RUN.value

        if len(variations) == 0:
            return VerdictType.NOT_RUN.value

        return _final_check_verdict

    def _generate_req_vars_results(self, variation_names, req, var_descriptions):
        req_dict = {}
        req_schema = REQUIREMENTS_SCHEMA.get(req.name, {})
        req_dict["name"] = req.name
        req_dict["req_text"] = req_schema.get("requirement_text") or ""
        req_dict["section"] = req_schema.get("document_section") or ""
        req_dict["description"] = req_schema.get("description") or ""
        req_dict["checks"] = []

        subtests = req_schema.get("subtests", [])
        if req_schema.get("test_id"):
            check_names = importlib.import_module(
                req_schema.get("test_id")
            ).get_test_names()

            for check_name in check_names:
                if check_name in subtests or len(subtests) == 0:
                    check_dict = {"name": check_name, "variations": []}

                    for var_name in variation_names:
                        variation_dict = {
                            "name": var_name,
                            "description": var_descriptions[var_name],
                        }

                        for scenario in self.test_oracle.variations:
                            if var_name == scenario.name:
                                for verdict in scenario.intermediate_verdicts:
                                    if verdict.test_name == check_name:
                                        variation_dict["verdict"] = (
                                            verdict.test_verdict.value
                                        )
                                        variation_dict["error"] = verdict.error
                                        check_dict["variations"].append(variation_dict)
                    check_dict["verdict"] = self._calculate_check_verdict(
                        check_dict.get("variations")
                    )
                    if (
                        check_dict["verdict"]
                        and len(check_dict.get("variations", [])) > 0
                    ):
                        req_dict["checks"].append(check_dict)

        req_dict["verdict"] = self._calculate_req_verdict(req_dict)

        return req_dict

    def get_rd_status_block(
        self, req_number: int, req_passed: int, req_failed: int, req_inconclusive: int
    ) -> dict:
        if self.test_oracle:
            _gen_verd = (
                True
                if self.test_oracle.get_general_verdict() == VerdictType.PASSED.value
                else False
            )
        else:
            _gen_verd = False
        status = {
            "general_verdict": _gen_verd,
            "static_verdict": True,
            "req_number": req_number,
            "req_passed": req_passed,
            "req_failed": req_failed,
            "req_inconclusive": req_inconclusive,
        }
        return status

    def _generate_report_data(self):
        """
        {
            info: {
                id:
                date:
                ts_version:
                lab: {
                    name:
                    accred_status:
                    accred_ref:
                    accred_auth:
                    addr_line_1:
                    addr_line_2:
                    city:
                    state:
                    country:
                    zip:
                    url:
                    eng_name:
                },
                supplier:{
                    name:
                    addr_line_1:
                    addr_line_2:
                    city:
                    state:
                    country:
                    zip:
                    url:
                },
                iut: {
                    type:
                    name:
                    version:
                    test_period:
                    date_of_receipt:
                    location:
                    cs_id:
                },
                test_env: {
                    ixit_id:
                    spec_name:
                    spec_version:
                    test_period_start:
                    test_period_end:
                    log_ref:
                    log_ret_date:
                },
                profile: {
                },
                comments:[
                {
                    author:
                    comment:
                },
                {}...
                ]
            },
            status: {
                general_verdict:
                static_verdict:
                req_number:
                req_passed:
                req_failed:
                req_inconclusive:
            },
            tests: {
                name:
                reqs: [
                    {
                        name:
                        req_text:
                        section:
                        description:
                        verdict:
                        checks: [
                            {
                                name:
                                verdict:
                                variations: [
                                    {
                                        name:
                                        description:
                                        verdict:
                                        error:
                                    },
                                    {}
                                ]
                            },
                            {}
                        ]
                    },
                    {},
                ]
        }
        TODO to add ixit - add to the template
        IXIT ID:				{{ info.test_env.ixit_id }}

        """
        run_config = self.test_oracle.get_run_config()
        self.report_data = {
            "detailed_view": run_config.global_config.report_files.detailed_view,
            "info": {
                "id": str(self.test_oracle.get_test_id()),
                "ts_version": str(_TS_VERSION),
                "date": datetime.now().strftime("%d %B %Y %H:%M:%S"),
                "lab": run_config.global_config.id_summary.lab.to_dict(),
                "supplier": run_config.global_config.id_summary.supplier.to_dict(),
                "iut": run_config.global_config.id_summary.iut.to_dict(),
                "test_env": run_config.global_config.id_summary.test_env.to_dict(),
                "comments": [
                    {"author": c.author, "comment": c.comment}
                    for c in run_config.global_config.comments
                ],
            },
            "tests": [],
        }

        results = {
            "req_number": 0,
            "req_passed": 0,
            "req_failed": 0,
            "req_inconclusive": 0,
        }

        for test in run_config.tests:
            reqs_list: List[Any] = []
            all_variations_names = self._get_all_variations_names(test.variations)

            for req in test.requirements:
                if "all" in req.variations:
                    reqs_list.append(
                        self._generate_req_vars_results(
                            all_variations_names.get("names"),
                            req,
                            all_variations_names.get("descriptions"),
                        )
                    )
                else:
                    reqs_list.append(
                        self._generate_req_vars_results(
                            req.variations,
                            req,
                            all_variations_names.get("descriptions"),
                        )
                    )

            self.report_data["tests"].append({"name": test.name, "reqs": reqs_list})

            results["req_number"] += len(reqs_list)
            for req in reqs_list:
                if req.get("verdict") == VerdictType.PASSED.value:
                    results["req_passed"] += 1
                elif req.get("verdict") == VerdictType.FAILED.value:
                    results["req_failed"] += 1
                elif req.get("verdict") == VerdictType.INC.value:
                    results["req_inconclusive"] += 1

        self.report_data["status"] = self.get_rd_status_block(**results)

    def _generate_pdf(self, output_path):
        """Generate a high-quality PDF report."""
        generate_pdf_with_reportlab(output_path, self.report_data)

    def _generate_docx(self, output_path):
        """Generate a DOCX report with one table per test case."""
        tpl = DocxTemplate(DOCX_TEMPLATE)
        tpl.render({"add_run_style": add_run_style, **self.report_data})
        tpl.save(output_path)

    def _generate_xml(self, output_path):
        """Generate an XML report (JUnit-compatible) that reflects CTR structure."""
        rd = self.report_data
        testsuites_el = ElTree.Element("testsuites")

        # ----- Root-level properties (CTR Identification Summary) -----
        props_el = ElTree.SubElement(testsuites_el, "properties")

        def add_prop(name, value):
            ElTree.SubElement(
                props_el,
                "property",
                name=name,
                value=str(value if value is not None else ""),
            )

        info = rd.get("info", {})
        lab = info.get("lab", {})
        supplier = info.get("supplier", {})
        iut = info.get("iut", {})
        test_env = info.get("test_env", {})
        status = rd.get("status", {})

        # Basic CTR metadata
        add_prop("ctr.id", info.get("id", ""))
        add_prop("ctr.date", info.get("date", ""))
        add_prop(
            "ctr.general_verdict",
            "PASSED" if status.get("general_verdict") else "FAILED",
        )
        add_prop("ctr.req_number", status.get("req_number", 0))
        add_prop("ctr.req_passed", status.get("req_passed", 0))
        add_prop("ctr.req_failed", status.get("req_failed", 0))
        add_prop("ctr.req_inconclusive", status.get("req_inconclusive", 0))

        # Lab
        for k, v in lab.items():
            add_prop(f"lab.{k}", v)

        # Supplier
        for k, v in supplier.items():
            add_prop(f"supplier.{k}", v)

        # IUT
        for k, v in iut.items():
            add_prop(f"iut.{k}", v)

        # Test environment
        for k, v in test_env.items():
            add_prop(f"test_env.{k}", v)

        # Comments
        for idx, c in enumerate(info.get("comments", []), start=1):
            add_prop(f"comment.{idx}.author", c.get("author", ""))
            add_prop(f"comment.{idx}.text", c.get("comment", ""))

        # ----- Build suites & cases -----
        total_tests = 0
        total_failures = 0
        total_skipped = 0

        for test in rd.get("tests", []):
            suite_tests = 0
            suite_failures = 0
            suite_skipped = 0

            suite_el = ElTree.SubElement(
                testsuites_el, "testsuite", name=str(test.get("name", ""))
            )

            # Optional: suite-level properties (could include test-level metadata)
            suite_props = ElTree.SubElement(suite_el, "properties")
            ElTree.SubElement(
                suite_props,
                "property",
                name="ctr.section",
                value="Dynamic Conformance Test Campaign Results",
            )

            for req in test.get("reqs", []):
                req_name = str(req.get("name", ""))
                req_desc = str(req.get("description", ""))
                req_text = str(req.get("req_text", ""))
                req_section = str(req.get("section", ""))

                # If no checks (edge case), still create a testcase summarizing the requirement verdict
                checks = req.get("checks", [])
                if not checks:
                    tc = ElTree.SubElement(
                        suite_el, "testcase", classname=req_name, name=f"{req_name}"
                    )
                    # Put requirement context in system-out
                    so = ElTree.SubElement(tc, "system-out")
                    so.text = f"Requirement only (no checks). Section: {req_section}\n{req_desc}\nText: {req_text}"
                    # Verdict on requirement level
                    rver = str(req.get("verdict", ""))
                    suite_tests += 1
                    if rver.upper() == "FAILED":
                        suite_failures += 1
                        fail = ElTree.SubElement(
                            tc, "failure", message=f"Requirement verdict: {rver}"
                        )
                        fail.text = "Requirement failed."
                    elif rver.upper() in {"INC", "INCONCLUSIVE"}:
                        suite_skipped += 1
                        sk = ElTree.SubElement(tc, "skipped", message="Inconclusive")
                        sk.text = "Requirement inconclusive."
                    continue

                for check in checks:
                    check_name = str(check.get("name", ""))
                    for variation in check.get("variations", []):
                        var_name = str(variation.get("name", ""))
                        var_desc = str(variation.get("description", ""))
                        var_ver = str(variation.get("verdict", "")).upper()
                        var_err = variation.get("error")

                        # testcase name encodes req, check, variation
                        tc = ElTree.SubElement(
                            suite_el,
                            "testcase",
                            classname=req_name,  # groups by requirement in many viewers
                            name=f"{req_name} :: {check_name} :: {var_name}",
                        )

                        # Put CTR context into system-out for visibility
                        so = ElTree.SubElement(tc, "system-out")
                        so_lines = [
                            f"Requirement: {req_name}",
                            f"Section: {req_section}",
                            f"Description: {req_desc}",
                            f"Text: {req_text}",
                            f"Check: {check_name}",
                            f"Variation: {var_name}",
                            f"Variation description: {var_desc}",
                            f"Verdict: {var_ver}",
                        ]
                        if var_err:
                            so_lines.append(f"Error: {var_err}")
                        so.text = "\n".join(so_lines)

                        suite_tests += 1
                        if var_ver == "FAILED":
                            suite_failures += 1
                            fail = ElTree.SubElement(
                                tc, "failure", message=f"{var_name}: FAILED"
                            )
                            fail.text = var_err or "Variation failed."
                        elif var_ver in {"INC", "INCONCLUSIVE"}:
                            suite_skipped += 1
                            sk = ElTree.SubElement(
                                tc, "skipped", message="Inconclusive"
                            )
                            sk.text = var_err or "Variation inconclusive."

            # set suite counters
            suite_el.set("tests", str(suite_tests))
            suite_el.set("failures", str(suite_failures))
            suite_el.set("skipped", str(suite_skipped))
            # (errors=0; we don’t use 'error' distinct from failure here)
            suite_el.set("errors", "0")

            total_tests += suite_tests
            total_failures += suite_failures
            total_skipped += suite_skipped

        # Optional roll-up on testsuites root (helpful for some parsers)
        testsuites_el.set("tests", str(total_tests))
        testsuites_el.set("failures", str(total_failures))
        testsuites_el.set("skipped", str(total_skipped))
        testsuites_el.set("errors", "0")

        # Pretty print and write
        tree = ElTree.ElementTree(testsuites_el)
        ElTree.indent(tree, space="  ", level=0)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    def _generate_json(self, output_path):
        """Generate a JSON report."""
        with open(output_path, "w") as json_file:
            json.dump(self.report_data, json_file, indent=4)

    def _generate_csv(self, output_path):
        """Generate a CSV report."""
        with open(output_path, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "Test Case",
                    "Requirement",
                    "Requirement Description",
                    "Requirement Text",
                    "Section",
                    "Requirement Verdict",
                    "Check",
                    "Check Verdict",
                    "Variation",
                    "Variation Description",
                    "Variation Verdict",
                ]
            )

            for test in self.report_data["tests"]:
                for req in test["reqs"]:
                    for check in req.get("checks", []):
                        for variation in check.get("variations", []):
                            writer.writerow(
                                [
                                    test["name"],
                                    req["name"],
                                    req["description"],
                                    req["req_text"],
                                    req["section"],
                                    req["verdict"],
                                    check["name"],
                                    check["verdict"],
                                    variation["name"],
                                    variation["description"],
                                    variation["verdict"],
                                ]
                            )

    @staticmethod
    def _calculate_req_verdict(req_dict) -> str:
        _final_req_verdict = VerdictType.PASSED.value

        if len(req_dict.get("checks")) == 0:
            return VerdictType.NOT_RUN.value

        for check in req_dict.get("checks"):
            if check.get("verdict") == VerdictType.FAILED.value:
                return VerdictType.FAILED.value

            if check.get("verdict") == VerdictType.INC.value:
                _final_req_verdict = VerdictType.INC.value
            elif (
                check.get("verdict") == VerdictType.NOT_RUN.value
                and _final_req_verdict != VerdictType.INC.value
            ):
                _final_req_verdict = VerdictType.NOT_RUN.value

        return _final_req_verdict

    @staticmethod
    def _get_status_summary(general_verdict: VerdictType) -> str:
        if general_verdict == VerdictType.PASSED.value:
            return "has not"
        return "has"

    @staticmethod
    def print_logo():
        figlet = Figlet(font="doom", justify="center", width=120)
        print(figlet.renderText("Texas A & M Center"))
        print("FOR APPLIED COMMUNICATIONS and NETWORKS".center(120, "-"))

    def print_report(self):
        self.print_logo()
        print("NG9-1-1 Conformance Test Report".center(120, "-"))
        print(f"Conformance Test Report ID: {self.report_data['info']['id']}")
        print(f"Date: {self.report_data['info']['date']}")
        print("IUT Conformance Status Summary".center(120, "-"))
        print(
            f"This Implementation Under Test "
            f"{self._get_status_summary(self.report_data['status']['general_verdict'])} "
            f"been shown by conformance assessment to be non-conforming to the referenced base specification(s)."
        )
        print("Static Conformance Summary".center(120, "-"))
        print("[Reserved for future use]")
        print("Dynamic Conformance Summary".center(120, "-"))
        print(f"Reqs Tested: {self.report_data['status']['req_number']}")
        print(f"Passed: {self.report_data['status']['req_passed']}")
        print(f"Failed: {self.report_data['status']['req_failed']}")
        print(f"Inconclusive: {self.report_data['status']['req_inconclusive']}")
        print("IUT Conformance Testing Results".center(120, "-"))
        print("Static Conformance Review Issues".center(120, "-"))
        print("[Reserved for future use]")
        print("Dynamic Conformance Test Campaign Results".center(120, "-"))
        for test in self.report_data["tests"]:
            for r in test["reqs"]:
                print(f"Requirement - {r['name']} -> Verdict - {r['verdict']}")
                print(f"Description - {r['description']}")
                print("------------------------------------------------------")

                #  TODO for dev - delete

                for c in r["checks"]:
                    print(f"Check - {c['name']} -> Verdict - {c['verdict']}")
                    print("------------------------------------------------------")
                    for v in c["variations"]:
                        print(f"Variation - {v['name']} -> Verdict - {v['verdict']}")
                        print(f"Error - {v['error']}")
                        print("+++++++")
                print("=====================================================")
