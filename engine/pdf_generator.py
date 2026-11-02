import os
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_ats_pdf(profile: Dict[str, Any], output_path: str) -> str:
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 0.5 to 0.6 inch margins are standard ATS friendly dimensions
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Clean Styles for ATS
    name_style = ParagraphStyle(
        'ATSName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#111827')
    )

    contact_style = ParagraphStyle(
        'ATSContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#374151')
    )

    section_heading_style = ParagraphStyle(
        'ATSSectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=8,
        spaceAfter=2,
        textTransform='uppercase'
    )

    body_style = ParagraphStyle(
        'ATSBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1F2937')
    )

    bullet_style = ParagraphStyle(
        'ATSBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        leftIndent=14,
        firstLineIndent=-10,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=2
    )

    job_title_style = ParagraphStyle(
        'ATSJobTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#111827')
    )

    meta_style = ParagraphStyle(
        'ATSMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#4B5563')
    )

    story = []

    # 1. Header (Name & Contact)
    personal = profile.get("personal", {})
    name = personal.get("full_name", "Candidate")
    story.append(Paragraph(name, name_style))
    story.append(Spacer(1, 3))

    contact_parts = []
    if personal.get("phone"):
        contact_parts.append(personal["phone"])
    if personal.get("email"):
        contact_parts.append(personal["email"])
    if personal.get("location"):
        contact_parts.append(personal["location"])
    if personal.get("linkedin"):
        contact_parts.append(personal["linkedin"].replace("https://", ""))
    if personal.get("github"):
        contact_parts.append(personal["github"].replace("https://", ""))

    contact_line = " | ".join(contact_parts)
    story.append(Paragraph(contact_line, contact_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

    # 2. Professional Summary
    summary = profile.get("summary", "")
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=4))
        story.append(Paragraph(summary, body_style))
        story.append(Spacer(1, 6))

    # 3. Core Competencies & Skills (Category-based for optimal parser indexing)
    skills = profile.get("skills", {})
    if skills:
        story.append(Paragraph("TECHNICAL SKILLS & CORE COMPETENCIES", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=4))
        for cat, sk_list in skills.items():
            if sk_list:
                line = f"<b>{cat}:</b> " + ", ".join(sk_list)
                story.append(Paragraph(line, body_style))
                story.append(Spacer(1, 2))
        story.append(Spacer(1, 6))

    # 4. Professional Experience
    experiences = profile.get("experiences", [])
    if experiences:
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=4))
        
        for exp in experiences:
            # Table row for Title + Company on Left, Location + Date on Right
            title_text = f"<b>{exp.get('title', '')}</b> | {exp.get('company', '')}"
            date_loc = f"{exp.get('location', '')}  ({exp.get('start_date', '')} – {exp.get('end_date', '')})"
            
            row_data = [[
                Paragraph(title_text, job_title_style),
                Paragraph(date_loc, meta_style)
            ]]
            
            t = Table(row_data, colWidths=[360, 180])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)
            story.append(Spacer(1, 2))

            for bullet in exp.get("bullets", []):
                bullet_text = f"• {bullet}"
                story.append(Paragraph(bullet_text, bullet_style))
            
            story.append(Spacer(1, 6))

    # 5. Key Projects (if present)
    projects = profile.get("projects", [])
    if projects:
        story.append(Paragraph("KEY PROJECTS", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=4))
        for proj in projects:
            proj_title = f"<b>{proj.get('name', '')}</b> [<i>{proj.get('tech', '')}</i>]"
            story.append(Paragraph(proj_title, job_title_style))
            story.append(Paragraph(f"• {proj.get('description', '')}", bullet_style))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 4))

    # 6. Education
    education = profile.get("education", [])
    if education:
        story.append(Paragraph("EDUCATION", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=4))
        for edu in education:
            deg = f"<b>{edu.get('degree', '')}</b> – {edu.get('institution', '')}"
            dt = f"{edu.get('graduation_year', '')} | GPA: {edu.get('gpa', 'N/A')}"
            row_data = [[
                Paragraph(deg, job_title_style),
                Paragraph(dt, meta_style)
            ]]
            t = Table(row_data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)
        story.append(Spacer(1, 6))

    # 7. Certifications (if present)
    certs = profile.get("certifications", [])
    if certs:
        story.append(Paragraph("CERTIFICATIONS", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=4))
        certs_line = " • ".join(certs)
        story.append(Paragraph(f"• {certs_line}", body_style))

    # Build PDF document
    doc.build(story)
    return output_path
