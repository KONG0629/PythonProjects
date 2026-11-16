from datetime import datetime


def peso(value):
    try:
        return f"PHP {float(value or 0):,.2f}"
    except Exception:
        return "PHP 0.00"


def safe(value):
    return "" if value is None else str(value)


def safe_float(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def get_first_existing(row, keys, default=0):
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return default


def compute_discounted_totals(rows):
    """
    Computes receipt totals safely.

    Item subtotal remains original item subtotal.
    Receipt total becomes:
    subtotal_amount - discount_amount
    """

    if not rows:
        return {
            "total_qty": 0,
            "item_subtotal": 0.0,
            "subtotal_amount": 0.0,
            "discount_type": "No Discount",
            "discount_amount": 0.0,
            "final_total": 0.0,
            "amount_received": 0.0,
            "change_amount": 0.0,
            "payment_method": "Cash",
            "online_reference": ""
        }

    first = rows[0]

    total_qty = 0
    item_subtotal = 0.0

    for row in rows:
        total_qty += safe_int(row.get("quantity"))
        item_subtotal += safe_float(row.get("subtotal"))

    subtotal_amount = safe_float(first.get("subtotal_amount"))

    if subtotal_amount <= 0:
        subtotal_amount = item_subtotal

    discount_type = safe(first.get("discount_type")) or "No Discount"
    discount_amount = safe_float(first.get("discount_amount"))

    if discount_amount < 0:
        discount_amount = 0.0

    if discount_amount > subtotal_amount:
        discount_amount = subtotal_amount

    # Always compute final total from subtotal - discount.
    final_total = subtotal_amount - discount_amount

    if final_total < 0:
        final_total = 0.0

    # If there is no discount and backend sent a valid final total, allow it.
    if discount_amount <= 0:
        backend_total = safe_float(
            get_first_existing(
                first,
                ["final_total", "net_total", "grand_total", "total_amount"],
                0
            )
        )

        if backend_total > 0:
            final_total = backend_total

    payment_method = safe(first.get("payment_method")) or "Cash"
    online_reference = safe(first.get("online_reference"))

    amount_received = safe_float(first.get("amount_received"))
    change_amount = safe_float(first.get("change_amount"))

    if payment_method.lower() == "online payment":
        amount_received = final_total
        change_amount = 0.0
    else:
        if amount_received <= 0:
            amount_received = final_total

        change_amount = amount_received - final_total

        if change_amount < 0:
            change_amount = 0.0

    return {
        "total_qty": total_qty,
        "item_subtotal": item_subtotal,
        "subtotal_amount": subtotal_amount,
        "discount_type": discount_type,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "amount_received": amount_received,
        "change_amount": change_amount,
        "payment_method": payment_method,
        "online_reference": online_reference
    }


def generate_receipt_pdf(rows, filename, generated_by="Admin", start_date=None, end_date=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    if not rows:
        raise ValueError("No receipt data found.")

    first = rows[0]
    totals = compute_discounted_totals(rows)

    order_id = safe(first.get("order_id"))
    cashier_name = safe(first.get("cashier_name"))
    sale_date = safe(first.get("sale_date") or first.get("created_at"))[:19]

    payment_method = totals["payment_method"]
    online_reference = totals["online_reference"]

    total_qty = totals["total_qty"]
    subtotal_amount = totals["subtotal_amount"]
    discount_type = totals["discount_type"]
    discount_amount = totals["discount_amount"]
    final_total = totals["final_total"]
    amount_received = totals["amount_received"]
    change_amount = totals["change_amount"]

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=55,
        leftMargin=55,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#7B1C1C"),
        spaceAfter=4
    )

    center_style = ParagraphStyle(
        "Center",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333")
    )

    right_style = ParagraphStyle(
        "Right",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontSize=10,
        leading=12
    )

    elements = []

    elements.append(Paragraph("Eugene Dressed Chicken Stall", title_style))
    elements.append(Paragraph("OFFICIAL RECEIPT", center_style))
    elements.append(Paragraph("Thank you for your purchase!", center_style))
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("=" * 82, center_style))
    elements.append(Spacer(1, 8))

    receipt_ref = f"RCPT-{order_id.zfill(6)}" if order_id.isdigit() else f"RCPT-{order_id}"

    info_rows = [
        ["Receipt No:", receipt_ref],
        ["Order ID:", order_id],
        ["Cashier:", cashier_name],
        ["Sale Date:", sale_date],
        ["Payment Method:", payment_method],
    ]

    if payment_method.lower() == "online payment":
        info_rows.append(["Reference No:", online_reference if online_reference else "—"])

    info_rows.extend([
        ["Generated By:", safe(generated_by)],
        ["Generated At:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    ])

    info_table = Table(
        info_rows,
        colWidths=[120, 330]
    )

    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("-" * 82, center_style))
    elements.append(Spacer(1, 8))

    item_data = [["Item", "Qty", "Price", "Subtotal"]]

    for row in rows:
        unit_price = row.get("unit_price")

        if unit_price is None:
            unit_price = row.get("price")

        item_data.append([
            safe(row.get("product_name")),
            str(safe_int(row.get("quantity"))),
            peso(unit_price),
            peso(row.get("subtotal"))
        ])

    item_table = Table(
        item_data,
        colWidths=[230, 50, 85, 100],
        repeatRows=1
    )

    item_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),

        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),

        ("LINEBELOW", (0, -1), (-1, -1), 0.7, colors.black),
    ]))

    elements.append(item_table)
    elements.append(Spacer(1, 12))

    summary_rows = [
        ["Total Items:", str(total_qty)],
        ["Subtotal:", peso(subtotal_amount)],
    ]

    if discount_amount > 0:
        summary_rows.append([f"Discount ({discount_type}):", f"-{peso(discount_amount)}"])
    else:
        summary_rows.append(["Discount:", peso(0)])

    summary_rows.extend([
        ["Amount Received:", peso(amount_received)],
        ["Change:", peso(change_amount)],
        ["TOTAL:", peso(final_total)]
    ])

    summary_table = Table(
        summary_rows,
        colWidths=[330, 135]
    )

    total_row_index = len(summary_rows) - 1

    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

        ("LINEABOVE", (0, total_row_index), (-1, total_row_index), 1, colors.black),
        ("FONTSIZE", (0, total_row_index), (-1, total_row_index), 12),
        ("TEXTCOLOR", (0, total_row_index), (-1, total_row_index), colors.HexColor("#7B1C1C")),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("=" * 82, center_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("This receipt serves as proof of transaction.", center_style))
    elements.append(Paragraph("Please keep this copy for your records.", center_style))
    elements.append(Spacer(1, 18))
    elements.append(Paragraph("Authorized Signature: ___________________________", right_style))

    doc.build(elements)

    return filename