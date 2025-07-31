from pyfiglet import Figlet
import xml.etree.ElementTree as ET
import json
import csv
import os
from datetime import datetime

from docxtpl import DocxTemplate, RichText

from .format_types.reportlab_pdf import generate_pdf_with_reportlab
from .report_enums import ReportType

from services.test_services.types.test_verdict import VerdictType
from services.config.schemas.requirements_schema import REQUIREMENTS_SCHEMA

DOCX_TEMPLATE = "test_suite/services/report/templates/doc_template.docx"
PDF_TEMPLATE = "test_suite/services/report/templates/pdf_template.html"


def add_run_style(verdict: str) -> RichText:
    rt = RichText()
    if verdict == "PASSED":
        rt.add(verdict, color="008000")  # зелений
    elif verdict == "FAILED":
        rt.add(verdict, color="FF0000")  # червоний
    else:
        rt.add(verdict)
    return rt


class ReportService:
    report_data: dict = {}
    output_directory: str = ""
    test_oracle = None

    def __init__(self, output_directory: str = "", test_oracle=None, report_data: dict = None):

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
        self.test_oracle = test_oracle
        self._generate_report_data()

    def from_json_data(self, json_data: dict):
        """Initialize with a json data."""
        self.report_data = json_data

    def generate_report(self, report_format: str, filename: str):
        """Generate a report in the specified format."""
        if report_format.lower() == ReportType.PDF.value:
            self._generate_pdf(self.output_directory + filename + "." + report_format.lower())
        elif report_format.lower() == ReportType.DOCUMENT.value:
            self._generate_docx(self.output_directory + filename + "." + report_format.lower())
        elif report_format.lower() == ReportType.XML.value:
            self._generate_xml(self.output_directory + filename + "." + report_format.lower())
        elif report_format.lower() == ReportType.CSV.value:
            self._generate_csv(self.output_directory + filename + "." + report_format.lower())
        else:
            raise ValueError(f"Unsupported report format. Use one of {ReportType.list()}")

    def __get_var_description(self, var_name: str) -> str:
        run_config = self.test_oracle.get_run_config()
        for test in run_config.tests:
            for var in test.variations:
                if var.name == var_name:
                    return var.description

    def _get_all_variations_names(self, variations: list):

        return {
            "names": [var.name for var in variations],
            "descriptions": {
                var.name: self.__get_var_description(var.name) for var in variations
            }
        }

    def _generate_req_vars_results(self, variation_names: list, req, var_descriptions):
        req_dict = {}
        req_schema = REQUIREMENTS_SCHEMA.get(req.name)
        req_dict["name"] = req.name
        req_dict["req_text"] = req_schema["requirement_text"]
        req_dict["section"] = req_schema["document_section"]
        req_dict["description"] = req_schema["description"]
        req_dict["variations"] = []
        for var_name in variation_names:
            variation_dict = {
                "name": var_name,
                "description": var_descriptions[var_name]
            }

            for scenario in self.test_oracle.scenarios:
                if var_name == scenario.name:
                    subtests = req_schema.get("subtests", [])
                    variation_dict["verdict"] = scenario.get_scenario_verdict().test_verdict.value
                    variation_dict["checks"] = []

                    for verdict in scenario.intermediate_verdicts:
                        if verdict.test_name in subtests or len(subtests) == 0:
                            variation_dict["checks"].append(
                                {
                                    "name": verdict.test_name,
                                    "verdict": verdict.test_verdict.value,
                                    "error": verdict.error
                                }
                            )

            req_dict["variations"].append(variation_dict)

        req_dict["verdict"] = self._calculate_req_verdict(req_dict)

        return req_dict

    def get_rd_status_block(self, req_number: int, req_passed: int, req_failed: int, req_inconclusive: int) -> dict:
        status = {
            "general_verdict": True if self.test_oracle.get_general_verdict() == VerdictType.PASSED.value else False,
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
                    ts_version:
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
                        variations: [
                            {
                                name:
                                verdict:
                                description:
                                checks: [
                                    {
                                        name:
                                        verdict:
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
        """
        run_config = self.test_oracle.get_run_config()

        self.report_data = {
            "detailed_view": run_config.global_config.report_files.detailed_view,
            "info": {
                "id": str(self.test_oracle.get_test_id()),
                "date": datetime.now().strftime("%d %B %Y %H:%M:%S"),
                "lab": run_config.global_config.id_summary.lab.to_dict(),
                "supplier": run_config.global_config.id_summary.supplier.to_dict(),
                "iut": run_config.global_config.id_summary.iut.to_dict(),
                "test_env": run_config.global_config.id_summary.test_env.to_dict(),
                "comments": [
                    {
                        "author": c.author,
                        "comment": c.comment
                    } for c in run_config.global_config.comments
                ]
            },
            "tests": []
        }

        results = {
            "req_number": 0,
            "req_passed": 0,
            "req_failed": 0,
            "req_inconclusive": 0,
        }

        for test in run_config.tests:
            reqs_list = []
            all_variations_names = self._get_all_variations_names(test.variations)
            print(all_variations_names)

            for req in test.requirements:
                if "all" in req.variations:
                    reqs_list.append(
                        self._generate_req_vars_results(
                            all_variations_names.get("names"), req, all_variations_names.get("descriptions")
                        )
                    )
                else:
                    reqs_list.append(
                        self._generate_req_vars_results(
                            req.variations, req, all_variations_names.get("descriptions")
                        )
                    )

            self.report_data["tests"].append(
                {
                    "name": test.name,
                    "reqs": reqs_list
                }
            )

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
        tpl.render({
            "add_run_style": add_run_style,
            **self.report_data
        })
        tpl.save(output_path)

    def _generate_xml(self, output_path):
        """Generate an XML (JUnitXML) report."""
        testsuites = ET.Element("testsuites")

        for test in self.report_data["tests"]:
            testsuite = ET.SubElement(testsuites, "testsuite", name=test["name"])

            for req in test["reqs"]:
                for variation in req.get("variations", []):
                    testcase = ET.SubElement(
                        testsuite,
                        "testcase",
                        classname=req["name"],
                        name=variation["name"]
                    )

                    for check in variation.get("checks", []):
                        if check["verdict"].upper() != "PASSED":
                            failure = ET.SubElement(
                                testcase,
                                "failure",
                                message=f"{check['name']}: {check['verdict']}"
                            )
                            failure.text = f"{check['name']} - {check['verdict']}"

        tree = ET.ElementTree(testsuites)
        ET.indent(tree, space="  ", level=0)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    def _generate_json(self, output_path):
        """Generate a JSON report."""
        with open(output_path, "w") as json_file:
            json.dump(self.report_data, json_file, indent=4)

    def _generate_csv(self, output_path):
        """Generate a CSV report."""
        with open(output_path, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "Test Case", "Requirement", "Requirement Description", "Requirement Text", "Section",
                "Requirement Verdict", "Variation", "Variation Description", "Variation Verdict",
                "Check", "Check Verdict"
            ])

            for test in self.report_data["tests"]:
                for req in test["reqs"]:
                    for variation in req.get("variations", []):
                        for check in variation.get("checks", []):
                            writer.writerow([
                                test["name"],
                                req["name"],
                                req["description"],
                                req["req_text"],
                                req["section"],
                                req["verdict"],
                                variation["name"],
                                variation["description"],
                                variation["verdict"],
                                check["name"],
                                check["verdict"]
                            ])

    @staticmethod
    def _calculate_req_verdict(req_dict) -> str:
        for var in req_dict.get("variations"):
            if var.get("verdict") == VerdictType.FAILED.value:
                return VerdictType.FAILED.value
        return VerdictType.PASSED.value

    @staticmethod
    def _get_status_summary(general_verdict: VerdictType) -> str:
        if general_verdict == VerdictType.PASSED.value:
            return "has not"
        return "has"

    @staticmethod
    def print_logo():
        figlet = Figlet(font='doom', justify='center', width=120)
        print(figlet.renderText("Texas A & M Center"))
        print("FOR APPLIED COMMUNICATIONS and NETWORKS".center(120, "-"))

    def print_report(self):
        self.print_logo()
        print("NG9-1-1 Conformance Test Report".center(120, "-"))
        print(f"Conformance Test Report ID: {self.report_data['info']['id']}")
        print(f"Date: {self.report_data['info']['date']}")
        print("IUT Conformance Status Summary".center(120, "-"))
        print(f"This Implementation Under Test "
              f"{self._get_status_summary(self.report_data['status']['general_verdict'])} "
              f"been shown by conformance assessment to be non-conforming to the referenced base specification(s).")
        print("Static Conformance Summary".center(120, "-"))
        print(f"[Reserved for future use]")
        print("Dynamic Conformance Summary".center(120, "-"))
        print(f"Reqs Tested: {self.report_data['status']['req_number']}")
        print(f"Passed: {self.report_data['status']['req_passed']}")
        print(f"Failed: {self.report_data['status']['req_failed']}")
        print(f"Inconclusive: {self.report_data['status']['req_inconclusive']}")
        print("IUT Conformance Testing Results".center(120, "-"))
        print("Static Conformance Review Issues".center(120, "-"))
        print(f"[Reserved for future use]")
        print("Dynamic Conformance Test Campaign Results".center(120, "-"))
        for test in self.report_data['tests']:
            for r in test['reqs']:
                print(f"Requirement - {r['name']} -> Verdict - {r['verdict']}")
                print(f"Description - {r['description']}")
                print("------------------------------------------------------")

                #TODO for dev - delete

                for v in r['variations']:
                    for c in v['checks']:
                        print(f"Check - {c['name']} -> Verdict - {c['verdict']}")
                        print(f"Error - {c['error']}")
                        print(f"+++++++")
                print("=====================================================")
