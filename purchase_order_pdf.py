"""Ham dokuma satınalma siparişi (PO) PDF üretimi (reportlab).

Planlama modülünde oluşturulan satınalma siparişleri için tedarikçiye
gönderilecek form niteliğinde tek sayfalık PDF üretir. Font/stil kaydı
order_pdf.py'de yapıldığından burada tekrar register edilmez.
"""

import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle

from order_pdf import (CURRENCY_SYMBOLS, _LOGO_PATH, _STYLE_CELL,
                        _STYLE_CELL_BOLD, _STYLE_COMPANY, _STYLE_HEADING,
                        _STYLE_NORMAL, _STYLE_SMALL, _STYLE_TITLE,
                        _fmt_date, _fmt_num, _multiline)

# Sayı hücreleri: sağa dayalı, gerekirse hücre içinde sarar (taşma yok)
_STYLE_CELL_R = ParagraphStyle("TrCellR", parent=_STYLE_CELL, alignment=TA_RIGHT)

# Ham dokuma satınalma şartları — formun altına eklenir
# (po["contract_terms"] veya company["po_terms"] doluysa onlar kullanılır).
DEFAULT_PO_TERMS = """1. İşbu sipariş formu, tedarikçinin kaşe/imzası ile sözleşme hükmündedir. Tedarikçi, siparişi 2 iş günü içinde yazılı olarak teyit etmediği takdirde form şartlarını kabul etmiş sayılır.
2. Mallar, formda belirtilen konstrüksiyona (iplik, sıklık, tarak/en, gramaj) uygun üretilecektir. En toleransı ±2 cm, gramaj toleransı ±%3'tür.
3. Miktar toleransı ±%5'tir; bu aralık dışındaki eksik veya fazla teslimat için alıcının yazılı onayı gerekir.
4. Ham kumaş; dokuma hatası, iplik kaçığı, yağ/leke vb. kusurlar yönünden 4 puan sistemine göre değerlendirilir. 100 m²'de 28 puanı aşan toplar iade edilir.
5. Her top etiketinde ürün kodu, lot/parti no, metre ve kilo bilgisi bulunacaktır. Lot bütünlüğü korunacak; farklı lotlar ayrı bildirilecektir.
6. Termin tarihi bağlayıcıdır. Tedarikçiden kaynaklanan gecikmelerde alıcı, gecikilen her hafta için fatura bedelinin %1'i oranında cezai şart uygulama veya siparişi kısmen/tamamen iptal etme hakkını saklı tutar.
7. Fiyatlara KDV dahil değildir. Ödeme, formda yazılı ödeme şekline göre, uygun teslimat ve fatura tesliminden sonra yapılır.
8. Kalite uygunsuzlukları teslim tarihinden itibaren 30 gün içinde yazılı bildirilir; kusurlu mal bedeli iade edilir veya mal değiştirilir.
9. Bu sipariş kapsamında paylaşılan konstrüksiyon ve teknik bilgiler gizlidir; üçüncü kişilerle paylaşılamaz ve başka müşteriler için kullanılamaz.
10. Uyuşmazlıklarda Bursa Mahkemeleri ve İcra Daireleri yetkilidir."""


def generate_purchase_order_pdf(po, company, file_path):
    symbol = CURRENCY_SYMBOLS.get(po.get("currency", "USD"), "$")
    if symbol == "₺":
        symbol = "TL"
    items = po.get("items") or []

    doc = SimpleDocTemplate(
        file_path, pagesize=A4,
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
    logo_cell = ""
    if os.path.exists(_LOGO_PATH):
        logo_cell = Image(_LOGO_PATH, width=32 * mm, height=32 * mm * 469 / 1293)
    header_table = Table([[company_info, logo_cell]], colWidths=[140 * mm, 46 * mm])
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
    elements.append(Paragraph("HAM DOKUMA SATINALMA SİPARİŞİ FORMU", _STYLE_TITLE))
    elements.append(Spacer(1, 4 * mm))

    # ── PO bilgileri — Termin, Sipariş Tarihi'nin hemen altında ─────
    def _i(text):
        return Paragraph(escape(str(text or "—")), _STYLE_NORMAL)

    info_data = [
        ["Sipariş (PO) No:", _i(po.get("po_no", "")), "Sipariş Tarihi:", _i(_fmt_date(po.get("po_date")))],
        ["Tedarikçi:", _i(po.get("supplier_name", "")), "Termin:", _i(_fmt_date(po.get("expected_delivery")))],
        ["İlgili Müşteri Siparişi:", _i(po.get("order_no", "")), "Ödeme Şekli:", _i(po.get("payment_method", ""))],
        ["Teslimat Şartları:", _i(po.get("delivery_terms", "")), "Para Birimi:", _i(po.get("currency", "USD"))],
        ["Oluşturan:", _i(po.get("created_by", "")), "Durum:", _i(po.get("status", ""))],
    ]
    info_table = Table(info_data, colWidths=[36 * mm, 60 * mm, 26 * mm, 64 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Turkish-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Turkish-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Kalemler — tüm hücreler sarmalı (taşma yok), açıklama dahil ──
    def _h(t):
        return Paragraph(escape(t), _STYLE_CELL_BOLD)

    def _c(t):
        return Paragraph(escape(str(t or "")), _STYLE_CELL)

    headers = [_h("Ürün Kodu"), _h("Kompozisyon"), _h("En"), _h("Gramaj"),
               _h("Kumaş Tipi"), _h("Çözgü"), _h("Atkı"), _h("Sıklık"),
               _h("Tarak Eni"), _h("Örgü"), _h("Açıklama"),
               _h("Metre"), _h("Kilo"), _h(f"Birim Fiyat ({symbol})"), _h(f"Tutar ({symbol})")]
    item_rows = [headers]
    grand_total = 0.0
    total_meter = 0.0
    total_kg = 0.0
    for it in items:
        meter = it.get("meter") or 0
        kg = it.get("kg") or 0
        unit_price = it.get("unit_price") or 0
        # Metre girildiyse fiyat metre bazlı; metre 0 ise kilo bazlı (iplik vb. $/kg)
        total = meter * unit_price if meter > 0 else kg * unit_price
        grand_total += total
        total_meter += meter
        total_kg += kg
        item_rows.append([
            _c(it.get("product_code", "")),
            _c(it.get("composition", "")),
            _c(it.get("width", "")),
            _c(it.get("gramaj", "")),
            _c(it.get("fabric_type", "")),
            _c(it.get("cozgu", "")),
            _c(it.get("atki", "")),
            _c(it.get("siklik", "")),
            _c(it.get("tarak_eni", "")),
            _c(it.get("orgu", "")),
            _c(it.get("description", "")),
            Paragraph(_fmt_num(meter), _STYLE_CELL_R),
            Paragraph(_fmt_num(kg), _STYLE_CELL_R),
            Paragraph(_fmt_num(unit_price), _STYLE_CELL_R),
            Paragraph(_fmt_num(total), _STYLE_CELL_R),
        ])
    item_rows.append(["GENEL TOPLAM:", "", "", "", "", "", "", "", "", "", "",
                      Paragraph(_fmt_num(total_meter), _STYLE_CELL_R),
                      Paragraph(_fmt_num(total_kg), _STYLE_CELL_R), "",
                      Paragraph(_fmt_num(grand_total), _STYLE_CELL_R)])

    col_widths = [w * mm for w in (14, 13, 8, 9, 10, 14, 14, 12, 9, 8, 13, 15, 13, 12, 16)]
    items_table = Table(item_rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Turkish-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Turkish"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EAF6")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BDBDBD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (11, 0), (14, -1), "RIGHT"),
        ("SPAN", (0, -1), (10, -1)),
        ("ALIGN", (0, -1), (10, -1), "RIGHT"),
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
    bank_col_width = 186 * mm / len(bank_blocks)
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

    if (po.get("notes") or "").strip():
        elements.append(Paragraph("Notlar", _STYLE_HEADING))
        elements.append(Paragraph(_multiline(po.get("notes", "")), _STYLE_NORMAL))
        elements.append(Spacer(1, 3 * mm))

    # ── Satınalma Şartları ───────────────────────────────────────
    terms = (po.get("contract_terms") or company.get("po_terms") or DEFAULT_PO_TERMS).strip()
    if terms:
        elements.append(Paragraph("Satınalma Şartları", _STYLE_HEADING))
        elements.append(Spacer(1, 1 * mm))
        terms_paras = [Paragraph(escape(satir.strip()), _STYLE_SMALL)
                       for satir in terms.split("\n") if satir.strip()]
        terms_table = Table([[terms_paras]], colWidths=[186 * mm])
        terms_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#9E9E9E")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(terms_table)
        elements.append(Spacer(1, 3 * mm))

    # ── Kaşe / İmza alanları ──────────────────────────────────────
    sig_table = Table(
        [
            [Paragraph(f"<b>{escape(company.get('name', ''))}</b>", _STYLE_NORMAL),
             Paragraph(f"<b>{escape(po.get('supplier_name', ''))}</b>", _STYLE_NORMAL)],
            [Paragraph("Kaşe / İmza", _STYLE_SMALL),
             Paragraph("Kaşe / İmza", _STYLE_SMALL)],
        ],
        colWidths=[93 * mm, 93 * mm], rowHeights=[8 * mm, 26 * mm])
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

    doc.build(elements)
