"""
PDF Certificate Generator utility using ReportLab.
Renders an elegant, professional landscape A4 certificate without external fonts or images.
"""

from pathlib import Path
import textwrap
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


# Color palette for professional certificate styling
COLOR_PRIMARY_NAVY = colors.HexColor("#1A2B4C")
COLOR_GOLD = colors.HexColor("#C59B27")
COLOR_ACCENT_GOLD = colors.HexColor("#D4AF37")
COLOR_DARK_TEXT = colors.HexColor("#2C3E50")
COLOR_MUTED_GRAY = colors.HexColor("#64748B")
COLOR_BG_BORDER = colors.HexColor("#F8FAFC")


def draw_decorative_badge(c: canvas.Canvas, cx: float, cy: float, radius: float = 24.0) -> None:
    """Draw a vector decorative seal / badge at (cx, cy)."""
    # Outer gold circle
    c.saveState()
    c.setStrokeColor(COLOR_GOLD)
    c.setFillColor(colors.HexColor("#FEF9C3"))
    c.setLineWidth(1.5)
    c.circle(cx, cy, radius, stroke=1, fill=1)

    # Inner dotted circle
    c.setStrokeColor(COLOR_ACCENT_GOLD)
    c.setLineWidth(1)
    c.circle(cx, cy, radius - 4, stroke=1, fill=0)

    # Center star or emblem
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx, cy - 3.5, "VERIFIED")
    c.restoreState()


def draw_corner_ornament(c: canvas.Canvas, x: float, y: float, size: float = 12.0) -> None:
    """Draw a small diamond corner accent."""
    c.saveState()
    c.setFillColor(COLOR_GOLD)
    c.setStrokeColor(COLOR_GOLD)
    path = c.beginPath()
    path.moveTo(x, y - size / 2)
    path.lineTo(x + size / 2, y)
    path.lineTo(x, y + size / 2)
    path.lineTo(x - size / 2, y)
    path.close()
    c.drawPath(path, fill=1, stroke=1)
    c.restoreState()


def generate_certificate_pdf(
    output_path: Path,
    certificate_id: str,
    recipient_name: str,
    event_name: str,
    organization_name: str,
    certificate_title: str,
    issue_date: str,
    certificate_text: Optional[str] = None,
) -> Path:
    """
    Generate an elegant landscape A4 PDF certificate.

    Args:
        output_path: Absolute destination path for the PDF file.
        certificate_id: Unique UUID/identifier for the certificate.
        recipient_name: Full name of the certificate recipient.
        event_name: Name of the event, workshop, or course.
        organization_name: Name of the issuing organization.
        certificate_title: Main title (e.g. 'Certificate of Participation').
        issue_date: Date string formatted for display.
        certificate_text: Optional custom narrative or achievements description.

    Returns:
        Path: The generated output file Path.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Landscape A4 dimensions (841.89 pt x 595.27 pt)
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(str(output_path), pagesize=landscape(A4))
    c.setTitle(f"Certificate - {recipient_name}")
    c.setAuthor(organization_name)
    c.setSubject(certificate_title)

    center_x = page_width / 2.0

    # 1. Outer & Inner Borders
    c.saveState()
    # Background border fill
    c.setStrokeColor(COLOR_PRIMARY_NAVY)
    c.setLineWidth(3.0)
    margin_outer = 25.0
    c.rect(
        margin_outer,
        margin_outer,
        page_width - 2 * margin_outer,
        page_height - 2 * margin_outer,
        stroke=1,
        fill=0,
    )

    # Inner decorative gold border
    c.setStrokeColor(COLOR_GOLD)
    c.setLineWidth(1.2)
    margin_inner = 33.0
    c.rect(
        margin_inner,
        margin_inner,
        page_width - 2 * margin_inner,
        page_height - 2 * margin_inner,
        stroke=1,
        fill=0,
    )

    # Corner ornaments
    draw_corner_ornament(c, margin_inner, margin_inner)
    draw_corner_ornament(c, page_width - margin_inner, margin_inner)
    draw_corner_ornament(c, margin_inner, page_height - margin_inner)
    draw_corner_ornament(c, page_width - margin_inner, page_height - margin_inner)
    c.restoreState()

    # 2. Organization Name (Header)
    c.saveState()
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawCentredString(center_x, page_height - 75, organization_name.upper())

    # Decorative header divider
    c.setStrokeColor(COLOR_GOLD)
    c.setLineWidth(1.0)
    c.line(center_x - 120, page_height - 85, center_x + 120, page_height - 85)
    c.restoreState()

    # 3. Certificate Title
    c.saveState()
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(COLOR_GOLD)
    c.drawCentredString(center_x, page_height - 125, certificate_title.upper())
    c.restoreState()

    # 4. Presentation Label
    c.saveState()
    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(COLOR_DARK_TEXT)
    c.drawCentredString(center_x, page_height - 165, "This is proudly presented to")
    c.restoreState()

    # 5. Recipient Name (Prominent)
    c.saveState()
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawCentredString(center_x, page_height - 210, recipient_name)

    # Elegant underline below recipient name
    c.setStrokeColor(COLOR_ACCENT_GOLD)
    c.setLineWidth(1.5)
    name_width = min(c.stringWidth(recipient_name, "Helvetica-Bold", 28) + 40, 480.0)
    c.line(center_x - (name_width / 2), page_height - 220, center_x + (name_width / 2), page_height - 220)
    c.restoreState()

    # 6. Event Name / Reason
    c.saveState()
    c.setFont("Helvetica", 12)
    c.setFillColor(COLOR_DARK_TEXT)
    c.drawCentredString(center_x, page_height - 250, "for participating in and completing")

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawCentredString(center_x, page_height - 275, event_name)
    c.restoreState()

    # 7. Custom Certificate Description
    body_text = certificate_text or "In recognition of outstanding dedication and successful participation."
    c.saveState()
    c.setFont("Helvetica", 11)
    c.setFillColor(COLOR_DARK_TEXT)
    
    # Wrap text cleanly across lines
    wrapped_lines = textwrap.wrap(body_text, width=80)
    curr_y = page_height - 310
    for line in wrapped_lines[:3]:  # Limit to 3 lines maximum
        c.drawCentredString(center_x, curr_y, line)
        curr_y -= 16
    c.restoreState()

    # 8. Bottom Signatures & Seal Section
    # Left: Issue Date
    date_x = 120.0
    bottom_y = 100.0
    c.saveState()
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawString(date_x, bottom_y + 15, issue_date)
    c.setStrokeColor(COLOR_MUTED_GRAY)
    c.setLineWidth(0.8)
    c.line(date_x, bottom_y + 10, date_x + 140, bottom_y + 10)
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_MUTED_GRAY)
    c.drawString(date_x + 35, bottom_y - 4, "Date of Issue")
    c.restoreState()

    # Center: Decorative Seal
    draw_decorative_badge(c, center_x, bottom_y + 10, radius=26.0)

    # Right: Signature Line
    sig_x = page_width - 260.0
    c.saveState()
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawString(sig_x + 25, bottom_y + 15, "Authorized Signatory")
    c.setStrokeColor(COLOR_MUTED_GRAY)
    c.setLineWidth(0.8)
    c.line(sig_x, bottom_y + 10, sig_x + 140, bottom_y + 10)
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_MUTED_GRAY)
    c.drawString(sig_x + 30, bottom_y - 4, "Authorized Signature")
    c.restoreState()

    # 9. Certificate ID & Verification Footer
    c.saveState()
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_MUTED_GRAY)
    c.drawCentredString(
        center_x,
        margin_outer + 12,
        f"Certificate ID: {certificate_id}  |  Issued by {organization_name}",
    )
    c.restoreState()

    # Render and save PDF
    c.showPage()
    c.save()

    return output_path
