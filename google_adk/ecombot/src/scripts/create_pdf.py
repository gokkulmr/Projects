"""Generate ecom_faq.pdf from faq.json for Day 06 PDF ingestion tests."""

import json
import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    faq_path = os.path.join(data_dir, "faq.json")
    pdf_path = os.path.join(data_dir, "ecom_faq.pdf")

    with open(faq_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []

    # Title
    Story.append(Paragraph("E-Commerce Support FAQ", styles["Title"]))
    Story.append(Spacer(1, 12))

    # Add each FAQ
    for faq in faqs:
        question = faq.get("question", "")
        answer = faq.get("answer", "")
        category = faq.get("category", "General").title()

        Story.append(Paragraph(f"<b>Category: {category}</b>", styles["Heading3"]))
        Story.append(Paragraph(f"<b>Q: {question}</b>", styles["Heading4"]))
        Story.append(Paragraph(answer, styles["Normal"]))
        Story.append(Spacer(1, 12))

    doc.build(Story)
    print(f"Created {pdf_path}")

if __name__ == "__main__":
    create_pdf()
