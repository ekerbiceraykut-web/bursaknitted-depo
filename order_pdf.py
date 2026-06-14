"""Sipariş sözleşmesi PDF üretimi (reportlab).

Satış personeli, kaydedilmiş bir siparişin sözleşme PDF'ini üretip
müşteriye gönderebilir. Türkçe karakter desteği için fonts/ klasöründeki
Arial fontları kullanılır.
"""

import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                 TableStyle)

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£"}

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
pdfmetrics.registerFont(TTFont("Turkish", os.path.join(_FONT_DIR, "Arial.ttf")))
pdfmetrics.registerFont(TTFont("Turkish-Bold", os.path.join(_FONT_DIR, "Arial Bold.ttf")))

_styles = getSampleStyleSheet()
_STYLE_COMPANY = ParagraphStyle("Company", parent=_styles["Normal"], fontName="Turkish-Bold", fontSize=12, leading=14)
_STYLE_NORMAL = ParagraphStyle("TrNormal", parent=_styles["Normal"], fontName="Turkish", fontSize=9, leading=12)
_STYLE_SMALL = ParagraphStyle("TrSmall", parent=_styles["Normal"], fontName="Turkish", fontSize=8, leading=10)
_STYLE_CELL = ParagraphStyle("TrCell", parent=_styles["Normal"], fontName="Turkish", fontSize=7.5, leading=9)
_STYLE_TITLE = ParagraphStyle("TrTitle", parent=_styles["Normal"], fontName="Turkish-Bold", fontSize=14, leading=18, alignment=TA_CENTER)
_STYLE_HEADING = ParagraphStyle("TrHeading", parent=_styles["Normal"], fontName="Turkish-Bold", fontSize=10, leading=13)


def _fmt_date(value):
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return str(value or "")


def _fmt_num(value, decimals=2):
    try:
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return f"{0:,.{decimals}f}"


def _multiline(text):
    return escape(text or "").replace("\n", "<br/>")


def generate_order_pdf(order, company, file_path):
    symbol = CURRENCY_SYMBOLS.get(order.get("currency", "USD"), "$")
    items = order.get("items") or []

    doc = SimpleDocTemplate(
        file_path, pagesize=landscape(A4),
        topMargin=12 * mm, bottomMargin=12 * mm,
        leftMargin=12 * mm, rightMargin=12 * mm,
    )
    elements = []

    # ── Firma başlığı ────────────────────────────────────────────
    elements.append(Paragraph(escape(company.get("name", "")), _STYLE_COMPANY))
    elements.append(Paragraph(escape(company.get("address", "")), _STYLE_SMALL))
    elements.append(Paragraph(
        f"Tel: {escape(company.get('phone', ''))}  |  Vergi No: {escape(company.get('tax', ''))}"
        f"  |  Menşei: {escape(company.get('origin', ''))}", _STYLE_SMALL))
    elements.append(Spacer(1, 5 * mm))

    # ── Başlık ───────────────────────────────────────────────────
    elements.append(Paragraph("SİPARİŞ SÖZLEŞMESİ", _STYLE_TITLE))
    elements.append(Spacer(1, 4 * mm))

    # ── Sipariş bilgileri ────────────────────────────────────────
    info_data = [
        ["Sipariş No:", order.get("order_no", ""), "Sipariş Tarihi:", _fmt_date(order.get("order_date"))],
        ["Müşteri:", order.get("customer_name", ""), "Müşteri Referans:", order.get("customer_ref", "")],
        ["Termin:", _fmt_date(order.get("delivery_date")), "Ödeme Şekli:", order.get("payment_method", "")],
        ["Teslimat Şartları:", order.get("delivery_terms", ""), "Teslimat Adresi:", order.get("delivery_address", "")],
    ]
    info_table = Table(info_data, colWidths=[32 * mm, 100 * mm, 32 * mm, 109 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Turkish"),
        ("FONTNAME", (0, 0), (0, -1), "Turkish-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Turkish-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Sipariş kalemleri ────────────────────────────────────────
    headers = ["Ürün Kodu", "Kompozisyon", "En", "Gramaj", "Kumaş Tipi", "Renk",
               "Lab No", "Açıklama", "Metre", "Kilo", f"Birim Fiyat ({symbol})", f"Tutar ({symbol})"]
    item_rows = [headers]
    grand_total = 0.0
    for it in items:
        meter = it.get("meter") or 0
        sale_price = it.get("sale_price") or 0
        total = meter * sale_price
        grand_total += total
        item_rows.append([
            Paragraph(escape(it.get("product_code", "")), _STYLE_CELL),
            Paragraph(escape(it.get("composition", "")), _STYLE_CELL),
            it.get("width", "") or "",
            it.get("gramaj", "") or "",
            Paragraph(escape(it.get("fabric_type", "")), _STYLE_CELL),
            Paragraph(escape(it.get("color", "")), _STYLE_CELL),
            it.get("lab_no", "") or "",
            Paragraph(escape(it.get("description", "")), _STYLE_CELL),
            _fmt_num(meter),
            _fmt_num(it.get("kg")),
            _fmt_num(sale_price),
            _fmt_num(total),
        ])
    item_rows.append(["", "", "", "", "", "", "", "", "", "", "GENEL TOPLAM:", _fmt_num(grand_total)])

    col_widths = [22 * mm, 32 * mm, 12 * mm, 14 * mm, 22 * mm, 18 * mm, 16 * mm,
                   38 * mm, 16 * mm, 16 * mm, 24 * mm, 24 * mm]
    items_table = Table(item_rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Turkish-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Turkish"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EAF6")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BDBDBD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (8, 0), (11, -1), "RIGHT"),
        ("ALIGN", (2, 0), (3, -1), "CENTER"),
        ("SPAN", (0, -1), (10, -1)),
        ("ALIGN", (0, -1), (10, -1), "RIGHT"),
        ("FONTNAME", (10, -1), (11, -1), "Turkish-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F5F5F5")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5 * mm))

    # ── Banka bilgilerimiz ───────────────────────────────────────
    elements.append(Paragraph("Banka Bilgilerimiz", _STYLE_HEADING))
    elements.append(Paragraph(_multiline(company.get("bank_info", "")), _STYLE_NORMAL))
    elements.append(Spacer(1, 3 * mm))

    if (order.get("notes") or "").strip():
        elements.append(Paragraph("Notlar", _STYLE_HEADING))
        elements.append(Paragraph(_multiline(order.get("notes", "")), _STYLE_NORMAL))
        elements.append(Spacer(1, 3 * mm))

    # ── Sözleşme şartnamesi ──────────────────────────────────────
    elements.append(Paragraph("Sözleşme Şartnamesi", _STYLE_HEADING))
    elements.append(Paragraph(_multiline(order.get("contract_terms", "")), _STYLE_SMALL))

    doc.build(elements)
