from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

L = R = 0.5 * inch
PAGE_WIDTH = A4[0] - L - R


def soften_long_tokens(s: str) -> str:
    """Let filenames/identifiers wrap at _, -, and ."""
    return s.replace("_", "_\u200b").replace("-", "-\u200b").replace(".", ".\u200b")


def generate_pdf_with_reportlab(output_path, report_data):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    cell_style = ParagraphStyle(
        "cell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        spaceBefore=0, spaceAfter=0,
        wordWrap="CJK",  # wrap even when there are no spaces
        splitLongWords=True,  # allow breaking very long words
        hyphenationLang="en"  # optional
    )

    # ==============================
    # 1. Identification Summary
    # ==============================
    elements.append(Paragraph("NG9-1-1 Conformance Test Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("1. Identification Summary", styles["Heading1"]))
    elements.append(Paragraph(f"Conformance Test Report ID: {report_data['info']['id']}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {report_data['info']['date']}", styles["Normal"]))
    elements.append(Spacer(1, 6))

    # 1.2 Test Laboratory
    lab = report_data["info"]["lab"]
    elements.append(Paragraph("1.2 Test Laboratory", styles["Heading2"]))
    for k, v in lab.items():
        elements.append(Paragraph(f"{k.capitalize()}: {v}", styles["Normal"]))
    elements.append(Spacer(1, 6))

    # 1.3 Supplier
    supplier = report_data["info"]["supplier"]
    elements.append(Paragraph("1.3 Supplier", styles["Heading2"]))
    for k, v in supplier.items():
        elements.append(Paragraph(f"{k.capitalize()}: {v}", styles["Normal"]))
    elements.append(Spacer(1, 6))

    # 1.4 Implementation Under Test
    iut = report_data["info"]["iut"]
    elements.append(Paragraph("1.4 Implementation Under Test", styles["Heading2"]))
    for k, v in iut.items():
        elements.append(Paragraph(f"{k.replace('_', ' ').capitalize()}: {v}", styles["Normal"]))
    elements.append(Spacer(1, 6))

    # 1.5 Test Environment
    test_env = report_data["info"]["test_env"]
    elements.append(Paragraph("1.5 Testing Environment", styles["Heading2"]))
    for k, v in test_env.items():
        elements.append(Paragraph(f"{k.replace('_', ' ').capitalize()}: {v}", styles["Normal"]))
    elements.append(Spacer(1, 6))

    # 1.10 Comments
    if report_data["info"]["comments"]:
        elements.append(Paragraph("1.10 Comments", styles["Heading2"]))
        for c in report_data["info"]["comments"]:
            elements.append(Paragraph(f"{c['author']} – {c['comment']}", styles["Normal"]))

    # ==============================
    # 2. IUT Conformance Status Summary
    # ==============================
    status = report_data["status"]
    elements.append(Paragraph("2. IUT Conformance Status Summary", styles["Heading1"]))
    general_verdict = "PASSED" if status["general_verdict"] else "FAILED"
    elements.append(Paragraph(f"General Verdict: {general_verdict}", styles["Normal"]))
    elements.append(Spacer(1, 6))

    data = [
        ["Req Number", "Passed", "Failed", "Inconclusive"],
        [status["req_number"], status["req_passed"], status["req_failed"], status["req_inconclusive"]],
    ]
    table = Table(
        data,
        colWidths=[PAGE_WIDTH * 0.25, PAGE_WIDTH * 0.25, PAGE_WIDTH * 0.25, PAGE_WIDTH * 0.20],
        hAlign="LEFT",
        repeatRows=1,
        splitByRow=1
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    # ==============================
    # 3. IUT Conformance Testing Results
    # ==============================
    elements.append(Paragraph("3. IUT Conformance Testing Results", styles["Heading1"]))

    for test in report_data["tests"]:
        elements.append(Paragraph(f"Test Case: {test['name']}", styles["Heading2"]))
        for req in test["reqs"]:
            elements.append(Paragraph(f"Requirement: {req['name']}", styles["Heading3"]))
            elements.append(Paragraph(f"Description: {req['description']}", cell_style))
            elements.append(Paragraph(f"Text: {req['req_text']}", cell_style))
            elements.append(Paragraph(f"Section: {req['section']}", cell_style))
            elements.append(Paragraph(f"Verdict: {req['verdict']}", cell_style))
            elements.append(Spacer(1, 6))

            # Detailed View
            if report_data.get("detailed_view", False):
                for check in req.get("checks", []):
                    elements.append(Paragraph(f"Check: {check['name']} – {check['verdict']}", styles["Heading4"]))
                    data = [["Variation", "Description", "Verdict"]]
                    for v in check.get("variations", []):
                        data.append([
                            Paragraph(v["name"], cell_style),
                            Paragraph(v["description"], cell_style),
                            Paragraph(v["verdict"], cell_style),
                        ])
                    table = Table(
                        data,
                        colWidths=[PAGE_WIDTH * 0.25, PAGE_WIDTH * 0.5, PAGE_WIDTH * 0.20],
                        hAlign="LEFT",
                        repeatRows=1,
                        splitByRow=1
                    )
                    table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 12))

    doc.build(elements)
