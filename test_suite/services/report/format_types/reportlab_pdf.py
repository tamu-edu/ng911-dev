from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf_with_reportlab(output_path, report_data):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    for test in report_data["tests"]:
        elements.append(Paragraph(f"Test Case: {test['name']}", styles['Heading2']))
        elements.append(Spacer(1, 12))

        for req in test["reqs"]:
            elements.append(Paragraph(f"Requirement: {req['name']}", styles['Heading3']))
            elements.append(Paragraph(f"Description: {req['description']}", styles['BodyText']))
            elements.append(Paragraph(f"Text: {req['req_text']}", styles['BodyText']))
            elements.append(Paragraph(f"Section: {req['section']}", styles['BodyText']))
            elements.append(Paragraph(f"Verdict: {req['verdict']}", styles['BodyText']))
            elements.append(Spacer(1, 8))

            for check in req["checks"]:
                elements.append(Paragraph(f"Check: {check['name']}", styles['Heading4']))
                elements.append(Paragraph(f"Verdict: {check['verdict']}", styles['BodyText']))

                data = [["Variation", "Description", "Verdict"]]
                for _var in check.get("variations", []):
                    data.append([_var["name"], _var["description"], _var["verdict"]])

                table = Table(data, hAlign='LEFT')
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ]))

                elements.append(table)
                elements.append(Spacer(1, 12))

            elements.append(Spacer(1, 16))

    doc.build(elements)
