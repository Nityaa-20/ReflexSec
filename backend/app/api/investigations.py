import io
import uuid
import html
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from pydantic import BaseModel, ConfigDict
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.database.db import get_db
from app.database.models import Investigation

# Routers
investigations_router = APIRouter(prefix="/investigations", tags=["Investigations"])
reports_router = APIRouter(prefix="/reports", tags=["Reports"])


# Pydantic schemas
class InvestigationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    severity: str
    threat_type: Optional[str]
    created_at: datetime


class InvestigationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    severity: str
    threat_type: Optional[str]
    created_at: datetime
    report_json: dict


# Endpoints
@investigations_router.get("", response_model=list[InvestigationListResponse])
async def list_investigations(
    db: AsyncSession = Depends(get_db),
) -> list[InvestigationListResponse]:
    logger.info("Listing all historical investigations")
    try:
        query = select(Investigation).order_by(Investigation.created_at.desc())
        result = await db.execute(query)
        investigations = result.scalars().all()
        return investigations
    except Exception as exc:
        logger.error("Failed to list investigations | error={}", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve investigations list."
        ) from exc


@investigations_router.get("/{investigation_id}", response_model=InvestigationDetailResponse)
async def get_investigation(
    investigation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> InvestigationDetailResponse:
    logger.info("Fetching investigation details | id={}", investigation_id)
    try:
        query = select(Investigation).where(Investigation.id == investigation_id)
        result = await db.execute(query)
        investigation = result.scalar_one_or_none()
        if not investigation:
            logger.warning("Investigation not found | id={}", investigation_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation with ID {investigation_id} not found."
            )
        return investigation
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch investigation | id={} error={}", investigation_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve investigation details."
        ) from exc


def format_pdf_text(text: str) -> str:
    if not text:
        return "N/A"
    # Escaping special characters for ReportLab XML parser safety
    escaped = html.escape(str(text))
    # Replace newlines with <br/> to preserve basic paragraph formatting
    return escaped.replace("\n", "<br/>")


def generate_investigation_pdf(investigation: Investigation) -> io.BytesIO:
    buffer = io.BytesIO()
    
    # 0.75 in margin (54pt)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=80,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles with enterprise / premium look (navy blue header, clean layouts)
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0088cc'), # clean blue/cyan accent
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e4a6e'), # deep navy blue
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155'), # dark slate gray
        spaceAfter=10
    )

    bullet_style = ParagraphStyle(
        'BulletItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=5
    )
    
    story = []
    
    # Title
    story.append(Paragraph("REFLEXSEC CYBER THREAT INTELLIGENCE", title_style))
    story.append(Paragraph("DETAILED INVESTIGATION REPORT", subtitle_style))
    
    # Meta Information Table
    meta_data = [
        [
            Paragraph("<b>Investigation Title:</b>", body_style),
            Paragraph(format_pdf_text(investigation.title), body_style)
        ],
        [
            Paragraph("<b>Overall Severity:</b>", body_style),
            Paragraph(format_pdf_text(investigation.severity.upper()), body_style)
        ],
        [
            Paragraph("<b>Threat Classification:</b>", body_style),
            Paragraph(format_pdf_text(investigation.threat_type.upper()), body_style)
        ],
        [
            Paragraph("<b>Generated On:</b>", body_style),
            Paragraph(investigation.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'), body_style)
        ],
        [
            Paragraph("<b>Investigation ID:</b>", body_style),
            Paragraph(str(investigation.id), body_style)
        ]
    ]
    
    meta_table = Table(meta_data, colWidths=[150, 354])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Extract report sections
    report_data = investigation.report_json.get("report", {})
    
    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(format_pdf_text(report_data.get("executive_summary", "N/A")), body_style))
    
    # Threat Assessment
    story.append(Paragraph("2. Threat Assessment", h1_style))
    story.append(Paragraph(format_pdf_text(report_data.get("threat_assessment", "N/A")), body_style))
    
    # Risk Analysis
    story.append(Paragraph("3. Risk Analysis", h1_style))
    story.append(Paragraph(format_pdf_text(report_data.get("risk_analysis", "N/A")), body_style))
    
    # Mitigation Strategy
    story.append(Paragraph("4. Mitigation Strategy", h1_style))
    story.append(Paragraph(format_pdf_text(report_data.get("mitigation_strategy", "N/A")), body_style))
    
    # Confidence Assessment
    story.append(Paragraph("5. Confidence Assessment", h1_style))
    story.append(Paragraph(format_pdf_text(report_data.get("confidence_assessment", "N/A")), body_style))
    
    # SOC Recommendations
    story.append(Paragraph("6. SOC Recommendations", h1_style))
    soc_recs = report_data.get("soc_recommendations", [])
    if isinstance(soc_recs, list):
        for rec in soc_recs:
            story.append(Paragraph(f"• {format_pdf_text(rec)}", bullet_style))
    else:
        story.append(Paragraph(format_pdf_text(str(soc_recs)), body_style))
        
    # First Page / Header & Footer Callback Setup
    def on_first_page(canvas, doc):
        canvas.saveState()
        # Top banner divider line
        canvas.setStrokeColor(colors.HexColor("#00d4ff"))
        canvas.setLineWidth(1.5)
        canvas.line(54, 745, 558, 745)
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(54, 36, "CONFIDENTIAL - INTERNAL SECURITY USE ONLY")
        canvas.drawRightString(558, 36, f"Page {doc.page}")
        canvas.restoreState()
        
    def on_later_pages(canvas, doc):
        canvas.saveState()
        # Header text
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(colors.HexColor("#0f172a"))
        canvas.drawString(54, 750, "REFLEXSEC // CYBER THREAT INTELLIGENCE REPORT")
        
        # Header divider line
        canvas.setStrokeColor(colors.HexColor("#00d4ff"))
        canvas.setLineWidth(1)
        canvas.line(54, 742, 558, 742)
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(54, 36, "CONFIDENTIAL - INTERNAL SECURITY USE ONLY")
        canvas.drawRightString(558, 36, f"Page {doc.page}")
        canvas.restoreState()
        
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    buffer.seek(0)
    return buffer


@reports_router.get("/export/{investigation_id}")
async def export_report(
    investigation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Request received to export investigation PDF | id={}", investigation_id)
    try:
        query = select(Investigation).where(Investigation.id == investigation_id)
        result = await db.execute(query)
        investigation = result.scalar_one_or_none()
        
        if not investigation:
            logger.warning("Investigation not found for PDF export | id={}", investigation_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation with ID {investigation_id} not found."
            )
            
        pdf_buffer = generate_investigation_pdf(investigation)
        
        # Safe filename
        safe_title = investigation.title.lower().replace(" ", "_")
        safe_title = "".join(c for c in safe_title if c.isalnum() or c == "_")
        filename = f"reflexsec_report_{safe_title}_{investigation_id.hex[:8]}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to generate and export PDF | id={} error={}", investigation_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate threat intelligence PDF."
        ) from exc
