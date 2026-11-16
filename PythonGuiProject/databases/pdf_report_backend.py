"""
databases/pdf_report_backend.py

This file creates PDF reports using ReportLab.

Used by:
- admin/report.py

Flow:
admin/report.py
→ pdf_report_backend.py
→ report_backend.py
→ db.py
→ MySQL
"""

# ============================================================
# IMPORTS
# ============================================================
from datetime import datetime

# ReportLab imports for PDF generation.
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# Backend function for getting accepted orders.
from databases.report_backend import get_report_orders


# ============================================================
# GENERATE SALES REPORT PDF
# ============================================================
def generate_sales_report_pdf(start_date, end_date, filename="sales_report.pdf", generated_by="Admin"):
    """
    Generates a sales report PDF.

    Parameters:
    - start_date: first date included in the report
    - end_date: last date included in the report
    - filename: where the PDF will be saved
    - generated_by: admin name displayed in the PDF

    The report shows:
    - order ID
    - cashier name
    - total amount
    - amount received
    - change amount
    - accepted date
    """

    # Get accepted orders from database.
    orders = get_report_orders(start_date, end_date)

    # Create PDF document.
    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    # ========================================================
    # PDF STYLES
    # ========================================================
    title_style = ParagraphStyle(
        "TitleStyle",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor("#7B1C1C"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.gray,
        spaceAfter=12
    )

    summary_style = ParagraphStyle(
        "SummaryStyle",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#7B1C1C"),
        spaceBefore=12
    )

    # This list holds all PDF elements.
    elements = []

    # ========================================================
    # PDF HEADER
    # ========================================================
    elements.append(Paragraph("Eugene Dressed Chicken Stall — Sales Report", title_style))

    elements.append(
        Paragraph(
            f"Date Range: {start_date} to {end_date} | "
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
            f"By: {generated_by}",
            subtitle_style
        )
    )

    # ========================================================
    # TABLE DATA
    # ========================================================
    table_data = [
        ["Order ID", "Cashier", "Total", "Received", "Change", "Accepted Date"]
    ]

    total_sales = 0.0
    total_received = 0.0
    total_change = 0.0

    for order in orders:
        total_amount = float(order["total_amount"] or 0)
        amount_received = float(order["amount_received"] or 0)
        change_amount = float(order["change_amount"] or 0)

        total_sales += total_amount
        total_received += amount_received
        total_change += change_amount

        accepted_at = order["accepted_at"]
        accepted_text = str(accepted_at)[:16] if accepted_at else ""

        table_data.append(
            [
                str(order["order_id"]),
                str(order["cashier_name"])[:22],
                f"PHP {total_amount:,.2f}",
                f"PHP {amount_received:,.2f}",
                f"PHP {change_amount:,.2f}",
                accepted_text
            ]
        )

    # If there are no orders, add one empty row.
    if len(table_data) == 1:
        table_data.append(["—", "No accepted orders found", "PHP 0.00", "PHP 0.00", "PHP 0.00", "—"])

    # ========================================================
    # CREATE TABLE
    # ========================================================
    table = Table(
        table_data,
        repeatRows=1,
        colWidths=[2.2 * cm, 5.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm, 4.0 * cm]
    )

    table.setStyle(
        TableStyle(
            [
                # Header style.
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7B1C1C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),

                # Body style.
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),

                # Alignment.
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),

                # Grid lines.
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E8D5B0")),

                # Padding.
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),

                # Alternating row backgrounds.
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFF8F0"), colors.white]),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 12))

    # ========================================================
    # SUMMARY
    # ========================================================
    elements.append(
        Paragraph(
            f"Total Sales: PHP {total_sales:,.2f} | "
            f"Total Received: PHP {total_received:,.2f} | "
            f"Total Change: PHP {total_change:,.2f} | "
            f"Total Orders: {len(orders)}",
            summary_style
        )
    )

    # Build and save PDF.
    doc.build(elements)

    return filename