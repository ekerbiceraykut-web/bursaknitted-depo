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
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                 Table, TableStyle)

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "TRY": "₺"}

_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
_APPROVALS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "onaylar_logo_seridi.png")
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
pdfmetrics.registerFont(TTFont("Turkish", os.path.join(_FONT_DIR, "Arial.ttf")))
pdfmetrics.registerFont(TTFont("Turkish-Bold", os.path.join(_FONT_DIR, "Arial Bold.ttf")))

_styles = getSampleStyleSheet()
_STYLE_COMPANY = ParagraphStyle("Company", parent=_styles["Normal"], fontName="Turkish-Bold", fontSize=12, leading=14)
_STYLE_NORMAL = ParagraphStyle("TrNormal", parent=_styles["Normal"], fontName="Turkish", fontSize=9, leading=12)
_STYLE_SMALL = ParagraphStyle("TrSmall", parent=_styles["Normal"], fontName="Turkish", fontSize=8, leading=10)
_STYLE_CELL = ParagraphStyle("TrCell", parent=_styles["Normal"], fontName="Turkish", fontSize=7.5, leading=9)
_STYLE_CELL_BOLD = ParagraphStyle("TrCellBold", parent=_styles["Normal"], fontName="Turkish-Bold", fontSize=7.5, leading=9)
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
    # Bundled Arial fontu ₺ (U+20BA) glifini içermiyor; PDF'te "TL" olarak yazılır.
    return escape(text or "").replace("₺", "TL").replace("\n", "<br/>")


def generate_order_pdf(order, company, file_path):
    symbol = CURRENCY_SYMBOLS.get(order.get("currency", "USD"), "$")
    if symbol == "₺":
        symbol = "TL"
    items = order.get("items") or []

    doc = SimpleDocTemplate(
        file_path, pagesize=landscape(A4),
        topMargin=12 * mm, bottomMargin=12 * mm,
        leftMargin=12 * mm, rightMargin=12 * mm,
    )
    elements = []

    # ── Firma başlığı + logo ─────────────────────────────────────
    company_info = [
        Paragraph(escape(company.get("name", "")), _STYLE_COMPANY),
        Paragraph(escape(company.get("address", "")), _STYLE_SMALL),
        Paragraph(
            f"Tel: {escape(company.get('phone', ''))}  |  Vergi No: {escape(company.get('tax', ''))}"
            f"  |  Menşei: {escape(company.get('origin', ''))}", _STYLE_SMALL),
    ]
    contact_links = []
    website = (company.get("website") or "").strip()
    if website:
        contact_links.append(
            f'<link href="https://{escape(website)}"><font color="#1565C0"><u>{escape(website)}</u></font></link>')
    for email in (company.get("email_info") or "").strip(), (company.get("email_planlama") or "").strip():
        if email:
            contact_links.append(
                f'<link href="mailto:{escape(email)}"><font color="#1565C0"><u>{escape(email)}</u></font></link>')
    if contact_links:
        company_info.append(Paragraph("  |  ".join(contact_links), _STYLE_SMALL))
    logo_cell = ""
    if os.path.exists(_LOGO_PATH):
        logo_cell = Image(_LOGO_PATH, width=42 * mm, height=42 * mm * 469 / 1293)
    header_table = Table([[company_info, logo_cell]], colWidths=[220 * mm, 53 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.HexColor("#2C2C2C")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#9E9E9E")),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 5 * mm))

    # ── Başlık ───────────────────────────────────────────────────
    elements.append(Paragraph("SİPARİŞ SÖZLEŞMESİ", _STYLE_TITLE))
    elements.append(Spacer(1, 4 * mm))

    # ── Sipariş bilgileri ────────────────────────────────────────
    # Termin, sipariş tarihinin hemen altında; müşteri referansı kalem tablosunda
    info_data = [
        ["Sipariş No:", order.get("order_no", ""), "Sipariş Tarihi:", _fmt_date(order.get("order_date"))],
        ["Müşteri:", order.get("customer_name", ""), "Termin:", _fmt_date(order.get("delivery_date"))],
        ["Müşteri Vergi No:", order.get("customer_tax_no", "") or "", "Ödeme Şekli:", order.get("payment_method", "")],
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
    # Baskı sütunları yalnız BASKILI kalem varsa basılır (boyalı siparişte gelmez)
    has_print = any((it.get("fabric_type") or "").upper() == "BASKILI" for it in items)
    musteri_ref = order.get("customer_ref", "") or ""

    def _h(text):
        return Paragraph(escape(text), _STYLE_CELL_BOLD)

    def _c(text):
        # Tüm hücreler Paragraph: uzun yazı hücre içinde alt satıra sarar, taşmaz
        return Paragraph(escape(str(text or "")), _STYLE_CELL)

    headers = [_h("Ürün Kodu"), _h("Kompozisyon"), _h("En"), _h("Gramaj"),
               _h("Kumaş Tipi"), _h("Renk"), _h("Lab No"), _h("Müşteri Ref."),
               _h("Açıklama"), _h("Metre"), _h("Kilo"),
               _h(f"Birim Fiyat ({symbol})"), _h(f"Tutar ({symbol})")]
    if has_print:
        headers += [_h("Baskı Tipi"), _h("Zemin Rengi"), _h("Baskı Desen No")]
    item_rows = [headers]
    grand_total = 0.0
    total_meter = 0.0
    total_kg = 0.0
    for it in items:
        meter = it.get("meter") or 0
        kg = it.get("kg") or 0
        sale_price = it.get("sale_price") or 0
        total = meter * sale_price
        grand_total += total
        total_meter += meter
        total_kg += kg
        row = [
            _c(it.get("product_code", "")),
            _c(it.get("composition", "")),
            _c(it.get("width", "")),
            _c(it.get("gramaj", "")),
            _c(it.get("fabric_type", "")),
            _c(it.get("color", "")),
            _c(it.get("lab_no", "")),
            _c(it.get("musteri_ref") or musteri_ref),
            _c(it.get("description", "")),
            _fmt_num(meter),
            _fmt_num(kg),
            _fmt_num(sale_price),
            _fmt_num(total),
        ]
        if has_print:
            row += [_c(it.get("print_type")), _c(it.get("zemin_rengi")),
                    _c(it.get("baski_desen_no"))]
        item_rows.append(row)
    toplam_row = ["GENEL TOPLAM:", "", "", "", "", "", "", "", "",
                  _fmt_num(total_meter), _fmt_num(total_kg), "", _fmt_num(grand_total)]
    if has_print:
        toplam_row += ["", "", ""]
    item_rows.append(toplam_row)

    if has_print:
        col_widths = [w * mm for w in
                      (24, 29, 9, 11, 17, 16, 14, 20, 26, 13, 13, 16, 16, 16, 15, 18)]
    else:
        col_widths = [w * mm for w in
                      (26, 34, 10, 12, 16, 18, 16, 24, 41, 14, 14, 24, 24)]
    items_table = Table(item_rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Turkish-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Turkish"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EAF6")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BDBDBD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (9, 0), (12, -1), "RIGHT"),
        ("SPAN", (0, -1), (8, -1)),
        ("ALIGN", (0, -1), (8, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Turkish-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F5F5F5")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5 * mm))

    # ── Banka bilgilerimiz ───────────────────────────────────────
    elements.append(Paragraph("Banka Bilgilerimiz", _STYLE_HEADING))
    elements.append(Spacer(1, 1 * mm))
    bank_blocks = [b.strip() for b in (company.get("bank_info", "") or "").split("\n\n") if b.strip()]
    if not bank_blocks:
        bank_blocks = [""]
    bank_col_width = 273 * mm / len(bank_blocks)
    bank_table = Table(
        [[Paragraph(_multiline(b), _STYLE_NORMAL) for b in bank_blocks]],
        colWidths=[bank_col_width] * len(bank_blocks))
    bank_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#9E9E9E")),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#9E9E9E")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(bank_table)
    elements.append(Spacer(1, 3 * mm))

    if (order.get("notes") or "").strip():
        elements.append(Paragraph("Notlar", _STYLE_HEADING))
        elements.append(Paragraph(_multiline(order.get("notes", "")), _STYLE_NORMAL))
        elements.append(Spacer(1, 3 * mm))

    # ── Sözleşme şartnamesi ──────────────────────────────────────
    elements.append(Paragraph("Sözleşme Şartnamesi", _STYLE_HEADING))
    elements.append(Spacer(1, 1 * mm))
    contract_lines = [ln.strip() for ln in (company.get("contract_template", "") or "").split("\n") if ln.strip()]
    if not contract_lines:
        contract_lines = [""]
    contract_table = Table(
        [[Paragraph(_multiline(ln), _STYLE_SMALL)] for ln in contract_lines],
        colWidths=[273 * mm])
    contract_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#9E9E9E")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(contract_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Kaşe / İmza alanları ──────────────────────────────────────
    sig_table = Table(
        [
            [Paragraph(f"<b>{escape(company.get('name', ''))}</b>", _STYLE_NORMAL),
             Paragraph(f"<b>{escape(order.get('customer_name', ''))}</b>", _STYLE_NORMAL)],
            [Paragraph("Kaşe / İmza", _STYLE_SMALL),
             Paragraph("Kaşe / İmza", _STYLE_SMALL)],
        ],
        colWidths=[136.5 * mm, 136.5 * mm], rowHeights=[8 * mm, 26 * mm])
    sig_table.setStyle(TableStyle([
        ("BOX", (0, 0), (0, -1), 0.75, colors.HexColor("#9E9E9E")),
        ("BOX", (1, 0), (1, -1), 0.75, colors.HexColor("#9E9E9E")),
        ("VALIGN", (0, 0), (-1, 0), "TOP"),
        ("VALIGN", (0, 1), (-1, 1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(sig_table)

    # ── Çalıştığımız markalar / sertifikalar ──────────────────────
    if os.path.exists(_APPROVALS_PATH):
        elements.append(Spacer(1, 5 * mm))
        elements.append(Image(_APPROVALS_PATH, width=273 * mm, height=273 * mm * 192 / 1840))

    doc.build(elements)
