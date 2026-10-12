import copy
import os
import shutil
from services.report.diagrams import DiagramService

from jinja2 import Environment, FileSystemLoader, select_autoescape


def generate_html_report(
    output_path: str,
    report_data: dict,
    template_path: str,
) -> None:
    """
    Render report_data into an HTML report using the configured Jinja template.

    Static template assets and report artifacts are copied next to the
    generated HTML so the resulting report remains self-contained.
    """

    template_path = os.path.abspath(template_path)
    template_directory = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)

    output_path = os.path.abspath(output_path)
    output_directory = os.path.dirname(output_path)

    os.makedirs(output_directory, exist_ok=True)

    # Copy static template assets used by the HTML report.
    source_assets = os.path.join(template_directory, "assets")
    output_assets = os.path.join(output_directory, "assets")

    if os.path.isdir(source_assets):
        shutil.copytree(
            source_assets,
            output_assets,
            dirs_exist_ok=True,
        )

    # Work with a copy so canonical report_data remains unchanged.
    html_report_data = copy.deepcopy(report_data)

    _copy_report_artifacts(
        report_data=html_report_data,
        output_directory=output_directory,
    )

    environment = Environment(
        loader=FileSystemLoader(template_directory),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = environment.get_template(template_name)

    rendered_html = template.render(**html_report_data)

    with open(output_path, "w", encoding="utf-8") as html_file:
        html_file.write(rendered_html)


def _copy_report_artifacts(
    report_data: dict,
    output_directory: str,
) -> None:
    """
    Copy report artifacts into html_report/assets/diagrams and replace
    their paths in the HTML rendering copy of report_data.

    Observed diagrams are regenerated from stored Mermaid sequence data
    when available. Existing SVG files are used as a backward-compatible
    fallback.

    Expected diagram paths are repository-relative.
    Observed diagram paths are run-output-relative.
    """

    diagrams_directory = os.path.join(
        output_directory,
        "assets",
        "diagrams",
    )

    os.makedirs(
        diagrams_directory,
        exist_ok=True,
    )

    run_output_directory = os.path.dirname(output_directory)

    sequence_data = report_data.get(
        "sequence_diagrams",
        {},
    )

    diagram_service = DiagramService(
        output_directory=output_directory,
    )

    generated_observed = set()

    for test in report_data.get("tests", []):
        for req in test.get("reqs", []):
            for check in req.get("checks", []):
                for variation in check.get("variations", []):
                    for artifact in variation.get("artifacts", []):

                        artifact_path = artifact.get("path")

                        if not artifact_path:
                            continue

                        filename = os.path.basename(artifact_path)

                        destination_path = os.path.join(
                            diagrams_directory,
                            filename,
                        )

                        # ------------------------------------------------
                        # Observed sequence diagram
                        # ------------------------------------------------

                        if artifact.get("role") == "observed":

                            variation_name = variation.get("name")

                            mermaid_str = sequence_data.get(variation_name)

                            if mermaid_str:

                                if variation_name not in generated_observed:

                                    svg_content = diagram_service.render_sequence_svg(
                                        mermaid_str
                                    )

                                    with open(
                                        destination_path,
                                        "w",
                                        encoding="utf-8",
                                    ) as svg_file:
                                        svg_file.write(svg_content)

                                    generated_observed.add(variation_name)

                                artifact["path"] = f"assets/diagrams/{filename}"

                                continue

                            # Backward-compatible fallback for old
                            # report_data without stored Mermaid data.
                            source_path = os.path.join(
                                run_output_directory,
                                artifact_path,
                            )

                        # ------------------------------------------------
                        # Expected sequence diagram
                        # ------------------------------------------------

                        else:
                            source_path = os.path.abspath(artifact_path)

                        if not os.path.isfile(source_path):
                            continue

                        shutil.copy2(
                            source_path,
                            destination_path,
                        )

                        artifact["path"] = f"assets/diagrams/{filename}"
