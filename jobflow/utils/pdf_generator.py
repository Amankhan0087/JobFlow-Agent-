"""
JobFlow PDF Generator
Generates professional resume PDFs using reportlab.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Generates professional resume PDFs using reportlab.
    Supports sections: Summary, Experience, Skills, Education, Certifications.
    """

    # Design constants
    PRIMARY_COLOR = (0.18, 0.83, 0.75)  # #2DD4BF teal
    TEXT_COLOR = (0.05, 0.05, 0.05)
    HEADING_COLOR = (0.10, 0.10, 0.30)
    LINE_COLOR = (0.80, 0.80, 0.80)

    def generate_resume_pdf(
        self,
        resume_data: Dict,
        output_path: str,
        template: str = "default",
    ) -> str:
        """
        Generate a professional resume PDF.

        Args:
            resume_data: Resume dict with name, email, phone, summary, skills, experience, education
            output_path: Full path for output PDF file
            template: Template name (currently only 'default' supported)

        Returns:
            Path to generated PDF file
        """
        try:
            from reportlab.lib.pagesizes import A4, letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
                Table, TableStyle, ListFlowable, ListItem
            )
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
        except ImportError as e:
            logger.error(f"reportlab not installed: {e}")
            raise

        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
            leftMargin=0.8 * inch,
            rightMargin=0.8 * inch,
        )

        # Define colors
        teal = colors.Color(*self.PRIMARY_COLOR)
        dark = colors.Color(0.10, 0.10, 0.25)
        gray = colors.Color(0.45, 0.45, 0.45)
        light_gray = colors.Color(*self.LINE_COLOR)

        # Styles
        styles = getSampleStyleSheet()

        name_style = ParagraphStyle(
            "Name",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=dark,
            spaceAfter=2,
            alignment=TA_CENTER,
        )
        contact_style = ParagraphStyle(
            "Contact",
            fontName="Helvetica",
            fontSize=9,
            textColor=gray,
            spaceAfter=8,
            alignment=TA_CENTER,
        )
        section_heading_style = ParagraphStyle(
            "SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=teal,
            spaceBefore=10,
            spaceAfter=3,
            alignment=TA_LEFT,
        )
        body_style = ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=colors.Color(*self.TEXT_COLOR),
            spaceAfter=4,
            leading=14,
        )
        bold_style = ParagraphStyle(
            "Bold",
            fontName="Helvetica-Bold",
            fontSize=9.5,
            textColor=dark,
            spaceAfter=2,
        )
        italic_style = ParagraphStyle(
            "Italic",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=gray,
            spaceAfter=4,
        )
        bullet_style = ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.Color(*self.TEXT_COLOR),
            leftIndent=12,
            spaceAfter=2,
            leading=13,
        )

        story = []

        # ---- Header ----
        name = resume_data.get("name", "Your Name")
        story.append(Paragraph(name, name_style))

        contact_parts = []
        for field in ("email", "phone", "location", "linkedin"):
            val = resume_data.get(field)
            if val:
                contact_parts.append(str(val))
        story.append(Paragraph("  |  ".join(contact_parts), contact_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=teal, spaceAfter=8))

        def add_section_heading(title: str) -> None:
            story.append(Paragraph(title.upper(), section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=light_gray, spaceAfter=4))

        # ---- Summary ----
        summary = resume_data.get("summary", "")
        if summary:
            add_section_heading("Professional Summary")
            story.append(Paragraph(summary, body_style))

        # ---- Skills ----
        skills = resume_data.get("skills", [])
        if skills:
            add_section_heading("Skills")
            skills_text = "  •  ".join(skills)
            story.append(Paragraph(skills_text, body_style))

        # ---- Experience ----
        experience = resume_data.get("experience", [])
        if experience:
            add_section_heading("Experience")
            for exp in experience:
                title = exp.get("title", "")
                company = exp.get("company", "")
                start = exp.get("start_date", "")
                end = exp.get("end_date", "Present")
                location = exp.get("location", "")

                header_text = f"<b>{title}</b> — {company}"
                story.append(Paragraph(header_text, bold_style))

                date_loc = f"{start} – {end}"
                if location:
                    date_loc += f"  |  {location}"
                story.append(Paragraph(date_loc, italic_style))

                for bullet in exp.get("responsibilities", []):
                    story.append(Paragraph(f"• {bullet}", bullet_style))

                story.append(Spacer(1, 4))

        # ---- Education ----
        education = resume_data.get("education", [])
        if education:
            add_section_heading("Education")
            for edu in education:
                degree = edu.get("degree", "")
                institution = edu.get("institution", "")
                year = edu.get("year", "")
                location = edu.get("location", "")

                story.append(Paragraph(f"<b>{degree}</b> — {institution}", bold_style))
                date_loc = year
                if location:
                    date_loc += f"  |  {location}"
                story.append(Paragraph(date_loc, italic_style))
                story.append(Spacer(1, 4))

        # ---- Certifications ----
        certs = resume_data.get("certifications", [])
        if certs:
            add_section_heading("Certifications")
            for cert in certs:
                story.append(Paragraph(f"• {cert}", bullet_style))

        doc.build(story)
        logger.info(f"PDF generated: {output_path}")
        return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_resume = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "phone": "+1-555-1234",
        "location": "Remote",
        "linkedin": "linkedin.com/in/janedeveloper",
        "summary": "AI/ML Engineer with 5+ years of experience building production ML systems.",
        "skills": ["Python", "TensorFlow", "PyTorch", "FastAPI", "Docker", "AWS"],
        "experience": [{
            "title": "Senior ML Engineer",
            "company": "TechCorp",
            "start_date": "2021",
            "end_date": "Present",
            "location": "Remote",
            "responsibilities": [
                "Built and deployed ML models serving 10M+ requests/day",
                "Led team of 5 engineers on NLP pipeline project",
            ]
        }],
        "education": [{
            "degree": "M.S. Computer Science",
            "institution": "State University",
            "year": "2019",
            "location": "New York, NY",
        }],
        "certifications": ["AWS Certified ML Specialty", "Google Cloud Professional Data Engineer"],
    }
    gen = PDFGenerator()
    gen.generate_resume_pdf(sample_resume, "/tmp/test_resume.pdf")
    print("PDF generated at /tmp/test_resume.pdf")
