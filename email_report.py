"""
Günlük stok raporu e-posta ile gönderir.
SMTP (Gmail App Password veya başka SMTP) kullanır.
"""
import smtplib
import threading
import time
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date
import database as db

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

_scheduler_thread = None
_stop_event = threading.Event()


# ── Config ──────────────────────────────────────────────────────

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data):
    cfg = load_config()
    cfg.update(data)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def get_email_config():
    cfg = load_config()
    return {
        "smtp_host":   cfg.get("smtp_host",   "smtp.gmail.com"),
        "smtp_port":   cfg.get("smtp_port",   587),
        "smtp_user":   cfg.get("smtp_user",   ""),
        "smtp_pass":   cfg.get("smtp_pass",   ""),
        "from_addr":   cfg.get("from_addr",   ""),
        "to_addrs":    cfg.get("to_addrs",    ""),   # virgülle ayrılmış
        "send_hour":   cfg.get("send_hour",   8),    # kaçta gönderilsin
        "send_enabled":cfg.get("send_enabled", False),
        "last_sent":   cfg.get("last_sent",   ""),
    }

def save_email_config(smtp_host, smtp_port, smtp_user, smtp_pass,
                      from_addr, to_addrs, send_hour, send_enabled):
    save_config({
        "smtp_host":    smtp_host,
        "smtp_port":    int(smtp_port),
        "smtp_user":    smtp_user,
        "smtp_pass":    smtp_pass,
        "from_addr":    from_addr,
        "to_addrs":     to_addrs,
        "send_hour":    int(send_hour),
        "send_enabled": send_enabled,
    })


# ── HTML Rapor ───────────────────────────────────────────────────

def _build_html():
    today = date.today().strftime("%d.%m.%Y")
    now   = datetime.now().strftime("%d.%m.%Y %H:%M")
    s     = db.get_summary()
    total_items = s["total_items"] or 0
    total_meter = s["total_meter"] or 0
    total_kg    = s["total_kg"] or 0
    total_value = s["total_value"] or 0

    # Bugünün hareketleri
    movements = db.get_all_movements(500)
    today_str = date.today().isoformat()
    today_mv  = [m for m in movements if str(m["movement_date"]).startswith(today_str)]

    mv_rows = ""
    for m in today_mv:
        t   = m["movement_type"]
        clr = "#2E7D32" if t == "GİRİŞ" else ("#880E4F" if t == "SİLME" else "#C62828")
        mv_rows += f"""<tr>
          <td style="padding:6px 10px;border-bottom:1px solid #eee">{str(m['movement_date'])[:16]}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;color:{clr};font-weight:700">{t}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee"><b>{m['product_code'] or ''}</b> {m['color'] or ''}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right">{m['meter']:,.2f} mt</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee">{m['user_name'] or '—'}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;color:#555">{m['notes'] or ''}</td>
        </tr>"""

    mv_section = f"""
    <h2 style="color:#1565C0;font-size:16px;margin:28px 0 10px">Bugünkü Hareketler ({len(today_mv)} işlem)</h2>
    {"<p style='color:#9E9E9E'>Bugün hareket kaydedilmemiş.</p>" if not mv_rows else f'''
    <table width="100%" style="border-collapse:collapse;font-size:13px">
      <tr style="background:#1565C0;color:white">
        <th style="padding:7px 10px;text-align:left">Tarih</th>
        <th style="padding:7px 10px;text-align:left">Tür</th>
        <th style="padding:7px 10px;text-align:left">Ürün</th>
        <th style="padding:7px 10px;text-align:right">Miktar</th>
        <th style="padding:7px 10px;text-align:left">Kullanıcı</th>
        <th style="padding:7px 10px;text-align:left">Not</th>
      </tr>
      {mv_rows}
    </table>'''}"""

    # Tüm stok listesi
    fabrics = db.get_all_fabrics()
    stok_rows = ""
    for i, r in enumerate(fabrics):
        mt  = r["meter"] or 0
        kg  = r["kg"] or 0
        fiy = r["birim_fiyat"] or 0
        val = mt * fiy if mt > 0 else kg * fiy
        bg  = "#F8F9FF" if i % 2 else "#FFFFFF"
        tip = r['fabric_type'] or ''
        tip_clr = {"HAM":"#5D4037","BOYALI":"#1565C0","BASKILI":"#6A1B9A"}.get(tip,"#555")
        stok_rows += f"""<tr style="background:{bg}">
          <td style="padding:5px 8px;border-bottom:1px solid #eee">{r['product_code'] or ''}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee">{r['product_name'] or ''}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee">{r['color'] or ''}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee">{r['location'] or ''}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;color:{tip_clr};font-weight:600">{tip}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;text-align:right;color:#2E7D32;font-weight:600">{mt:,.2f}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;text-align:right;color:#6A1B9A">{kg:,.2f}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;text-align:right">{fiy:,.2f} $</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;text-align:right;color:#B71C1C;font-weight:700">{"" if not val else f"{val:,.0f} $"}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;color:#757575;font-size:12px">{r['description'] or ''}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0f4ff;font-family:Arial,sans-serif;color:#212121">
<div style="max-width:900px;margin:24px auto;background:white;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.1)">

  <!-- Header -->
  <div style="background:#1565C0;padding:24px 32px;color:white">
    <h1 style="margin:0;font-size:22px">Bursa Knitted — Günlük Stok Raporu</h1>
    <p style="margin:6px 0 0;opacity:.8;font-size:14px">{now} tarihinde otomatik oluşturuldu</p>
  </div>

  <div style="padding:24px 32px">

    <!-- Dashboard Özeti -->
    <h2 style="color:#1565C0;font-size:16px;margin:0 0 14px">📊 Anlık Durum</h2>
    <table width="100%"><tr>
      <td width="25%" style="padding:0 8px 0 0">
        <div style="background:#E3F2FD;border-radius:8px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#1565C0">{total_items}</div>
          <div style="font-size:12px;color:#555;margin-top:4px">Ürün Kalemi</div>
        </div>
      </td>
      <td width="25%" style="padding:0 8px">
        <div style="background:#E8F5E9;border-radius:8px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#2E7D32">{total_meter:,.0f} mt</div>
          <div style="font-size:12px;color:#555;margin-top:4px">Toplam Metre</div>
        </div>
      </td>
      <td width="25%" style="padding:0 8px">
        <div style="background:#F3E5F5;border-radius:8px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#6A1B9A">{total_kg:,.0f} kg</div>
          <div style="font-size:12px;color:#555;margin-top:4px">Toplam Kilo</div>
        </div>
      </td>
      <td width="25%" style="padding:0 0 0 8px">
        <div style="background:#FFEBEE;border-radius:8px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#B71C1C">{total_value:,.0f} $</div>
          <div style="font-size:12px;color:#555;margin-top:4px">Stok Değeri</div>
        </div>
      </td>
    </tr></table>

    {mv_section}

    <!-- Tüm Stok -->
    <h2 style="color:#1565C0;font-size:16px;margin:28px 0 10px">📦 Tüm Stok Listesi ({len(fabrics)} kalem)</h2>
    <div style="overflow-x:auto">
    <table width="100%" style="border-collapse:collapse;font-size:12px">
      <tr style="background:#1565C0;color:white">
        <th style="padding:7px 8px;text-align:left">Kodu</th>
        <th style="padding:7px 8px;text-align:left">Adı</th>
        <th style="padding:7px 8px;text-align:left">Renk</th>
        <th style="padding:7px 8px;text-align:left">Lokasyon</th>
        <th style="padding:7px 8px;text-align:left">Tip</th>
        <th style="padding:7px 8px;text-align:right">Metre</th>
        <th style="padding:7px 8px;text-align:right">Kilo</th>
        <th style="padding:7px 8px;text-align:right">Birim $</th>
        <th style="padding:7px 8px;text-align:right">Değer $</th>
        <th style="padding:7px 8px;text-align:left">Açıklama</th>
      </tr>
      {stok_rows}
    </table>
    </div>

  </div>

  <!-- Footer -->
  <div style="background:#F5F5F5;padding:14px 32px;text-align:center;color:#9E9E9E;font-size:12px;border-top:1px solid #eee">
    Bursa Knitted Depo Takip Sistemi · Otomatik Rapor · {now}
  </div>
</div>
</body></html>"""
    return html, today


# ── Gönderici ───────────────────────────────────────────────────

def send_report(test=False):
    """Raporu gönder. test=True ise 'son_gönderildi' güncellenmez."""
    cfg = get_email_config()
    if not cfg["smtp_user"] or not cfg["smtp_pass"]:
        raise ValueError("E-posta ayarları eksik. Lütfen ayarları doldurun.")
    if not cfg["to_addrs"]:
        raise ValueError("Alıcı e-posta adresi girilmemiş.")

    html, today = _build_html()
    to_list = [a.strip() for a in cfg["to_addrs"].split(",") if a.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Bursa Knitted Stok Raporu — {today}"
    msg["From"]    = cfg["from_addr"] or cfg["smtp_user"]
    msg["To"]      = ", ".join(to_list)
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg["smtp_user"], cfg["smtp_pass"])
        server.sendmail(msg["From"], to_list, msg.as_string())

    if not test:
        save_config({"last_sent": date.today().isoformat()})

    return len(to_list)


# ── Günlük Zamanlayıcı ───────────────────────────────────────────

def _scheduler_loop():
    while not _stop_event.is_set():
        try:
            cfg = get_email_config()
            if cfg["send_enabled"]:
                now  = datetime.now()
                last = cfg.get("last_sent", "")
                today = date.today().isoformat()
                if last != today and now.hour >= cfg["send_hour"]:
                    try:
                        send_report()
                    except Exception as e:
                        print(f"[Mail] Gönderim hatası: {e}")
        except Exception:
            pass
        # Her 10 dakikada bir kontrol
        _stop_event.wait(600)


def start_scheduler():
    global _scheduler_thread
    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()


def stop_scheduler():
    _stop_event.set()
