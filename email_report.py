"""
Günlük stok raporu e-posta ile gönderir.
SMTP (Gmail App Password veya başka SMTP) kullanır.
"""
import smtplib
import threading
import time
import json
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date
import database as _local_db

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def _db():
    """Aktif bağlantıya göre veri kaynağı: uzak modda api_client (bulut),
    yerel modda database. Rapor daha önce hep yerel dosyayı okuduğu için
    bulut kullanıcılarında içerik 0 geliyordu."""
    try:
        import sys
        m = sys.modules.get("__main__")
        if m is not None and getattr(m, "CONNECTION_MODE", "local") == "remote":
            import api_client
            if getattr(api_client, "_token", None):
                return api_client
    except Exception:
        pass
    return _local_db

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
    db    = _db()   # uzak modda bulut verisi, yerel modda stok.db
    today = date.today().strftime("%d.%m.%Y")
    now   = datetime.now().strftime("%d.%m.%Y %H:%M")
    s     = db.get_summary()
    total_items = s["total_items"] or 0
    total_meter = s["total_meter"] or 0
    total_kg    = s["total_kg"] or 0
    total_value = s["total_value"] or 0

    # Bugünün tüm hareketleri
    today_str = date.today().isoformat()
    today_mv  = [dict(m) for m in db.get_movements_by_range(today_str, today_str)]

    mv_rows = ""
    for m in today_mv:
        t   = m["movement_type"]
        clr = {"GİRİŞ": "#2E7D32", "SATINALMA GİRİŞİ": "#1565C0",
               "SİLME": "#880E4F"}.get(t, "#C62828")
        dest = m.get("destination") or ""
        dest_type = m.get("destination_type") or ""
        dest_lbl = f"{dest_type}: {dest}" if dest and dest_type else dest
        extra = []
        if m.get("out_color"): extra.append(f"Renk: {m['out_color']}")
        if m.get("lab_no"):    extra.append(f"Lab: {m['lab_no']}")
        if m.get("parti_no"):  extra.append(f"Parti: {m['parti_no']}")
        notes = m.get("notes") or ""
        if extra:
            notes = (notes + "  |  " if notes else "") + "  ".join(extra)
        mv_rows += f"""<tr>
          <td style="padding:6px 10px;border-bottom:1px solid #eee">{str(m['movement_date'])[:16]}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;color:{clr};font-weight:700">{t}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee"><b>{m['product_code'] or ''}</b> {m['color'] or ''}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right">{(m['meter'] or 0):,.2f} mt</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right">{(m['kg'] or 0):,.2f} kg</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;color:#1565C0">{dest_lbl}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee">{m['user_name'] or '—'}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;color:#555">{notes}</td>
        </tr>"""

    mv_section = f"""
    <h2 style="color:#1565C0;font-size:16px;margin:28px 0 10px">Bugünkü Hareketler ({len(today_mv)} işlem)</h2>
    {"<p style='color:#9E9E9E'>Bugün hareket kaydedilmemiş.</p>" if not mv_rows else f'''
    <div style="overflow-x:auto">
    <table width="100%" style="border-collapse:collapse;font-size:13px">
      <tr style="background:#1565C0;color:white">
        <th style="padding:7px 10px;text-align:left">Tarih</th>
        <th style="padding:7px 10px;text-align:left">Tür</th>
        <th style="padding:7px 10px;text-align:left">Ürün</th>
        <th style="padding:7px 10px;text-align:right">Metre</th>
        <th style="padding:7px 10px;text-align:right">Kilo</th>
        <th style="padding:7px 10px;text-align:left">Hedef</th>
        <th style="padding:7px 10px;text-align:left">Kullanıcı</th>
        <th style="padding:7px 10px;text-align:left">Not</th>
      </tr>
      {mv_rows}
    </table>
    </div>'''}"""

    # Bugünün fire kayıtları
    fire_all = [dict(r) for r in db.get_fire_records()]
    today_fire = [r for r in fire_all if str(r.get("created_at", "")).startswith(today_str)]

    fire_rows = ""
    for r in today_fire:
        is_total = r["record_type"] == "LOT TOPLAMI"
        elle = " (elle)" if r.get("manual_pct") else ""
        pre_m, out_m = r["pre_meter"] or 0, r["out_meter"] or 0
        pre_k, out_k = r["pre_kg"] or 0, r["out_kg"] or 0
        fire_m, fire_k = max(0, pre_m - out_m), max(0, pre_k - out_k)
        pct_m = (fire_m / pre_m * 100) if pre_m > 0 else 0
        pct_k = (fire_k / pre_k * 100) if pre_k > 0 else 0
        bg = "#FFF8E1" if is_total else "#FFFFFF"
        bold = "font-weight:700;" if is_total else ""
        fire_rows += f"""<tr style="background:{bg};{bold}">
          <td style="padding:6px 8px;border-bottom:1px solid #eee">{r['boyahane'] or ''}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee"><b>{r['product_code'] or ''}</b> {r.get('out_color') or r['color'] or ''}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee">{r['lot'] or ''}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee">{r.get('lab_no') or ''} {r.get('parti_no') or ''}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee">{r['customer'] or ''}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right">{pre_m:,.2f}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right">{out_m:,.2f}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right;color:#C62828;font-weight:700">{fire_m:,.2f} (%{pct_m:.1f}){elle}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right;color:#C62828">{fire_k:,.2f} kg (%{pct_k:.1f})</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee">{r['record_type']}</td>
        </tr>"""

    fire_section = f"""
    <h2 style="color:#C62828;font-size:16px;margin:28px 0 10px">🔥 Bugünkü Boyahane Fire Oranları ({len(today_fire)} kayıt)</h2>
    {"<p style='color:#9E9E9E'>Bugün fire kaydı yok.</p>" if not fire_rows else f'''
    <div style="overflow-x:auto">
    <table width="100%" style="border-collapse:collapse;font-size:12px">
      <tr style="background:#C62828;color:white">
        <th style="padding:7px 8px;text-align:left">Boyahane</th>
        <th style="padding:7px 8px;text-align:left">Ürün</th>
        <th style="padding:7px 8px;text-align:left">Lot</th>
        <th style="padding:7px 8px;text-align:left">Lab/Parti</th>
        <th style="padding:7px 8px;text-align:left">Hedef</th>
        <th style="padding:7px 8px;text-align:right">Öncesi mt</th>
        <th style="padding:7px 8px;text-align:right">Çıkış mt</th>
        <th style="padding:7px 8px;text-align:right">Fire mt (%)</th>
        <th style="padding:7px 8px;text-align:right">Fire kg (%)</th>
        <th style="padding:7px 8px;text-align:left">Tür</th>
      </tr>
      {fire_rows}
    </table>
    </div>'''}"""

    # Kumaş tipi özeti (HAM / PFD / BOYALI / İPLİĞİ BOYALI / BASKILI)
    fabrics = db.get_all_fabrics()
    tip_colors = {"HAM": "#5D4037", "PFD": "#00695C", "BOYALI": "#1565C0", "İPLİĞİ BOYALI": "#EF6C00", "BASKILI": "#6A1B9A"}
    tip_bgs    = {"HAM": "#EFEBE9", "PFD": "#E0F2F1", "BOYALI": "#E3F2FD", "İPLİĞİ BOYALI": "#FFF3E0", "BASKILI": "#F3E5F5"}
    tip_stats  = {t: {"count": 0, "meter": 0.0, "kg": 0.0} for t in tip_colors}
    for r in fabrics:
        t = r["fabric_type"] or ""
        if t in tip_stats:
            tip_stats[t]["count"] += 1
            tip_stats[t]["meter"] += r["meter"] or 0
            tip_stats[t]["kg"]    += r["kg"] or 0

    tip_cards = ""
    for t in ["HAM", "PFD", "BOYALI", "İPLİĞİ BOYALI", "BASKILI"]:
        st = tip_stats[t]
        tip_cards += f"""
      <td width="20%" style="padding:0 4px">
        <div style="background:{tip_bgs[t]};border-radius:8px;padding:14px;text-align:center">
          <div style="font-size:13px;font-weight:700;color:{tip_colors[t]}">{t}</div>
          <div style="font-size:22px;font-weight:700;color:{tip_colors[t]};margin-top:4px">{st['meter']:,.0f} mt</div>
          <div style="font-size:12px;color:#555;margin-top:4px">{st['kg']:,.0f} kg · {st['count']} kalem</div>
        </div>
      </td>"""

    tip_section = f"""
    <h2 style="color:#1565C0;font-size:16px;margin:28px 0 10px">🧵 Kumaş Tipi Dağılımı</h2>
    <table width="100%"><tr>{tip_cards}</tr></table>"""

    # Depo / dış depo özeti
    dis_depolar = {l["name"] for l in db.get_active_locations() if l["group_name"] != "DEPO"}
    depots = {}
    for r in fabrics:
        loc = r["location"] or ""
        key = loc if loc in dis_depolar else "DEPO"
        mt  = r["meter"] or 0
        kg  = r["kg"] or 0
        fiy = r["birim_fiyat"] or 0
        val = mt * fiy if mt > 0 else kg * fiy
        d = depots.setdefault(key, {"count": 0, "meter": 0.0, "kg": 0.0, "value": 0.0})
        d["count"] += 1; d["meter"] += mt; d["kg"] += kg; d["value"] += val

    depot_rows = ""
    keys = (["DEPO"] if "DEPO" in depots else []) + sorted(k for k in depots if k != "DEPO")
    for i, key in enumerate(keys):
        d = depots[key]
        bg = "#F8F9FF" if i % 2 else "#FFFFFF"
        grp = "DEPO" if key == "DEPO" else "DIŞ DEPO"
        grp_clr = "#1565C0" if key == "DEPO" else "#E65100"
        depot_rows += f"""<tr style="background:{bg}">
          <td style="padding:6px 10px;border-bottom:1px solid #eee;font-weight:700">{key}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;color:{grp_clr};font-weight:600">{grp}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right">{d['count']}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right;color:#2E7D32;font-weight:600">{d['meter']:,.2f}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right;color:#6A1B9A">{d['kg']:,.2f}</td>
          <td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right;color:#B71C1C;font-weight:700">{d['value']:,.0f} $</td>
        </tr>"""
    t_count = sum(d["count"] for d in depots.values())
    t_meter = sum(d["meter"] for d in depots.values())
    t_kg    = sum(d["kg"] for d in depots.values())
    t_value = sum(d["value"] for d in depots.values())
    depot_rows += f"""<tr style="background:#E3F2FD;font-weight:700">
      <td style="padding:7px 10px" colspan="2">TOPLAM</td>
      <td style="padding:7px 10px;text-align:right">{t_count}</td>
      <td style="padding:7px 10px;text-align:right;color:#2E7D32">{t_meter:,.2f}</td>
      <td style="padding:7px 10px;text-align:right;color:#6A1B9A">{t_kg:,.2f}</td>
      <td style="padding:7px 10px;text-align:right;color:#B71C1C">{t_value:,.0f} $</td>
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

    {tip_section}

    <!-- Depo / Dış Depo Özeti -->
    <h2 style="color:#1565C0;font-size:16px;margin:28px 0 10px">🗂 Depo / Dış Depo Özeti</h2>
    <table width="100%" style="border-collapse:collapse;font-size:13px">
      <tr style="background:#1565C0;color:white">
        <th style="padding:7px 10px;text-align:left">Depo / Lokasyon</th>
        <th style="padding:7px 10px;text-align:left">Grup</th>
        <th style="padding:7px 10px;text-align:right">Kalem</th>
        <th style="padding:7px 10px;text-align:right">Toplam Metre</th>
        <th style="padding:7px 10px;text-align:right">Toplam Kilo</th>
        <th style="padding:7px 10px;text-align:right">Toplam Değer $</th>
      </tr>
      {depot_rows}
    </table>

    {mv_section}

    {fire_section}

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


def send_email_with_attachment(to_addr, subject, body_text, attachment_path):
    """Tek bir alıcıya, PDF eki ile düz metin e-posta gönderir
    (Satınalma Siparişi formu vb. için)."""
    cfg = get_email_config()
    if not cfg["smtp_user"] or not cfg["smtp_pass"]:
        raise ValueError("E-posta ayarları eksik. Lütfen ayarları doldurun.")
    if not to_addr:
        raise ValueError("Alıcı e-posta adresi girilmemiş.")

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = cfg["from_addr"] or cfg["smtp_user"]
    msg["To"] = to_addr
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    with open(attachment_path, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
    part.add_header("Content-Disposition", "attachment",
                    filename=os.path.basename(attachment_path))
    msg.attach(part)

    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg["smtp_user"], cfg["smtp_pass"])
        server.sendmail(msg["From"], [to_addr], msg.as_string())


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
