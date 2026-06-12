"""
Bursa Knitted Depo Takip — Web Sunucusu
- Yerel ağ: http://IP:5055  (aynı WiFi)
- İnternet: ngrok ile herkese açık HTTPS
- Tam CRUD: giriş/çıkış/ekleme/düzenleme/silme
- Oturum yönetimi: cookie tabanlı
"""
import threading, socket, json, os, hashlib, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote_plus
import database as db

_server       = None
_thread       = None
_ngrok_tunnel = None
PORT          = 5055

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Aktif oturumlar: {token: {user_id, username, full_name, role}}
_sessions: dict = {}


# ── Config ──────────────────────────────────────────────────────

def load_config():
    try:
        with open(CONFIG_PATH) as f: return json.load(f)
    except Exception: return {}

def save_config(data):
    cfg = load_config(); cfg.update(data)
    with open(CONFIG_PATH, "w") as f: json.dump(cfg, f, indent=2)

def get_ngrok_token():  return load_config().get("ngrok_token", "")
def set_ngrok_token(t): save_config({"ngrok_token": t.strip()})

def is_readonly():
    """Mobil arayüz salt-izleme modu (varsayılan: açık)."""
    return load_config().get("web_readonly", True)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:    s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except: return "127.0.0.1"
    finally: s.close()


# ── Oturum ──────────────────────────────────────────────────────

def _create_session(user):
    token = str(uuid.uuid4())
    _sessions[token] = dict(user)
    return token

def _get_session(req_headers):
    cookie = req_headers.get("Cookie", "")
    for part in cookie.split(";"):
        k, _, v = part.strip().partition("=")
        if k.strip() == "bk_token":
            return _sessions.get(v.strip())
    return None

def _delete_session(req_headers):
    cookie = req_headers.get("Cookie", "")
    for part in cookie.split(";"):
        k, _, v = part.strip().partition("=")
        if k.strip() == "bk_token":
            _sessions.pop(v.strip(), None)


# ── HTML Şablonları ──────────────────────────────────────────────

def _page(title, content, user=None, active=""):
    ro = is_readonly()
    nav_items = [
        ("/"        , "📊 Dashboard" , "dashboard"),
        ("/stok"    , "📦 Stok"      , "stok"),
        ("/hareket" , "📋 Hareketler", "hareket"),
    ]
    if not ro:
        nav_items += [
            ("/giris"   , "↑ Stok Giriş" , "giris"),
            ("/cikis"   , "↓ Stok Çıkış" , "cikis"),
        ]
        if user and user.get("role") == "admin":
            nav_items.append(("/yeni", "＋ Yeni Kumaş", "yeni"))

    nav_html = "".join(
        f'<a href="{href}" class="nav-item {"active" if active==key else ""}">{label}</a>'
        for href, label, key in nav_items
    )
    ro_badge = '<span style="background:rgba(255,255,255,.2);border-radius:4px;padding:3px 8px;font-size:11px;margin-right:10px">👁 İzleme Modu</span>' if ro else ""
    user_bar = (ro_badge +
                f'<span style="opacity:.8">{user["full_name"]}</span> &nbsp; <a href="/logout" style="color:rgba(255,255,255,.7);font-size:12px">Çıkış</a>') if user else ""

    return f"""<!DOCTYPE html>
<html lang="tr"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Bursa Knitted Depo</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f4ff;color:#212121;font-size:14px}}
.topbar{{background:#1565C0;color:white;padding:0 16px;display:flex;align-items:center;height:48px;position:sticky;top:0;z-index:100;box-shadow:0 2px 6px rgba(0,0,0,.3)}}
.topbar h1{{font-size:15px;font-weight:700;margin-right:20px;white-space:nowrap}}
.nav-item{{color:rgba(255,255,255,.75);text-decoration:none;padding:6px 12px;border-radius:4px;font-size:13px;white-space:nowrap}}
.nav-item:hover,.nav-item.active{{background:rgba(255,255,255,.2);color:white}}
.spacer{{flex:1}}
.user-bar{{font-size:13px;color:white}}
.user-bar a{{color:rgba(255,255,255,.7);text-decoration:none}}
.container{{max-width:1200px;margin:0 auto;padding:16px}}
.card{{background:white;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:16px;overflow:hidden}}
.card-header{{background:#1565C0;color:white;padding:10px 16px;font-weight:700}}
.card-body{{padding:16px}}
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}}
.stat{{background:white;border-radius:8px;padding:16px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
.stat .val{{font-size:24px;font-weight:700}}.stat .lbl{{font-size:11px;color:#757575;margin-top:4px}}
.blue{{color:#1565C0}}.green{{color:#2E7D32}}.purple{{color:#6A1B9A}}.red{{color:#B71C1C}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#1565C0;color:white;padding:8px 10px;text-align:left;white-space:nowrap}}
td{{padding:7px 10px;border-bottom:1px solid #eee;vertical-align:middle}}
tr:nth-child(even) td{{background:#f8f9ff}}
tr:hover td{{background:#e3f2fd}}
.badge{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700}}
.b-ham{{background:#EFEBE9;color:#5D4037}}
.b-pfd{{background:#E0F2F1;color:#00695C}}
.b-boyali{{background:#E3F2FD;color:#1565C0}}
.b-baskili{{background:#F3E5F5;color:#6A1B9A}}
.b-giris{{background:#E8F5E9;color:#2E7D32}}
.b-cikis{{background:#FFEBEE;color:#C62828}}
.b-silme{{background:#FCE4EC;color:#880E4F}}
.b-loc{{background:#E3F2FD;color:#1565C0}}
.num{{text-align:right}}
.btn{{display:inline-block;padding:6px 14px;border-radius:4px;font-size:13px;font-weight:700;cursor:pointer;border:none;text-decoration:none}}
.btn-primary{{background:#1565C0;color:white}}.btn-primary:hover{{background:#1976D2}}
.btn-success{{background:#2E7D32;color:white}}.btn-success:hover{{background:#388E3C}}
.btn-danger{{background:#C62828;color:white}}.btn-danger:hover{{background:#D32F2F}}
.btn-warn{{background:#F57F17;color:white}}.btn-warn:hover{{background:#F9A825}}
.btn-sm{{padding:3px 10px;font-size:12px}}
input,select,textarea{{width:100%;padding:8px 10px;border:1px solid #ddd;border-radius:4px;font-size:14px;background:white}}
input:focus,select:focus,textarea:focus{{outline:none;border-color:#1565C0}}
.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px}}
.form-group{{margin-bottom:10px}}
.form-group label{{display:block;font-size:12px;font-weight:700;color:#555;margin-bottom:4px}}
.required{{color:#C62828}}
.alert{{padding:10px 14px;border-radius:4px;margin-bottom:12px;font-size:13px}}
.alert-err{{background:#FFEBEE;color:#C62828;border:1px solid #FFCDD2}}
.alert-ok{{background:#E8F5E9;color:#2E7D32;border:1px solid #C8E6C9}}
.search-bar{{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}}
.search-bar input,.search-bar select{{flex:1;min-width:120px}}
.text-muted{{color:#9E9E9E}}
.tbl-actions a{{margin-right:6px}}
@media(max-width:600px){{.form-row{{grid-template-columns:1fr}}.topbar h1{{font-size:13px}}}}
</style></head>
<body>
<div class="topbar">
  <h1>🏭 Bursa Knitted</h1>
  <nav style="display:flex;gap:4px;overflow-x:auto">{nav_html}</nav>
  <div class="spacer"></div>
  <div class="user-bar">{user_bar}</div>
</div>
<div class="container">{content}</div>
<div style="text-align:center;padding:20px;color:#9E9E9E;font-size:11px">
  Bursa Knitted Depo Takip Sistemi
</div>
</body></html>"""


def _login_page(error=""):
    err = f'<div class="alert alert-err">{error}</div>' if error else ""
    return f"""<!DOCTYPE html><html lang="tr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Giriş — Bursa Knitted</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,sans-serif;background:#1565C0;display:flex;align-items:center;justify-content:center;min-height:100vh}}
.box{{background:white;border-radius:12px;padding:36px 32px;width:320px;box-shadow:0 8px 32px rgba(0,0,0,.2)}}
.logo{{text-align:center;margin-bottom:20px;font-size:22px;font-weight:800;color:#1565C0}}
.logo small{{display:block;font-size:13px;color:#757575;font-weight:400}}
label{{font-size:12px;font-weight:700;color:#555;display:block;margin-bottom:4px;margin-top:12px}}
input{{width:100%;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px}}
input:focus{{outline:none;border-color:#1565C0}}
button{{width:100%;padding:11px;background:#1565C0;color:white;border:none;border-radius:4px;font-size:15px;font-weight:700;cursor:pointer;margin-top:18px}}
button:hover{{background:#1976D2}}
.alert-err{{background:#FFEBEE;color:#C62828;border:1px solid #FFCDD2;padding:8px 12px;border-radius:4px;font-size:13px;margin-top:10px}}
</style></head><body>
<div class="box">
  <div class="logo">Bursa Knitted<small>Depo Takip Sistemi</small></div>
  {err}
  <form method="post" action="/login">
    <label>Kullanıcı Adı</label>
    <input name="username" autofocus autocomplete="username">
    <label>Şifre</label>
    <input name="password" type="password" autocomplete="current-password">
    <button type="submit">Giriş Yap</button>
  </form>
</div>
</body></html>"""


# ── Sayfa İçerikleri ─────────────────────────────────────────────

def _dashboard(user):
    s = db.get_summary()
    total_items = s["total_items"] or 0
    total_meter = s["total_meter"] or 0
    total_kg    = s["total_kg"]    or 0
    total_value = s["total_value"] or 0

    from collections import defaultdict
    locs = db.get_active_locations()
    groups = defaultdict(lambda: [0, 0.0, 0.0, 0.0])
    for l in locs:
        rows = db.get_all_fabrics(location=l["name"])
        g = l["group_name"]
        groups[g][0] += len(rows)
        groups[g][1] += sum(r["meter"] or 0 for r in rows)
        groups[g][2] += sum(r["kg"]   or 0 for r in rows)
        groups[g][3] += sum(((r["meter"] or 0)*(r["birim_fiyat"] or 0)) if (r["meter"] or 0)>0
                            else ((r["kg"] or 0)*(r["birim_fiyat"] or 0)) for r in rows)

    loc_rows = ""
    for g in sorted(groups.keys()):
        cnt, mt, kg, val = groups[g]
        clr = "#1565C0" if g=="DEPO" else "#37474F"
        loc_rows += f"""<tr>
          <td><span class="badge" style="background:{clr};color:white">{g}</span></td>
          <td class="num">{cnt}</td>
          <td class="num">{mt:,.0f} mt</td>
          <td class="num">{kg:,.0f} kg</td>
          <td class="num" style="color:#B71C1C;font-weight:700">{f"{val:,.0f} $" if val else "—"}</td>
        </tr>"""

    content = f"""
<div class="stat-grid">
  <div class="stat"><div class="val blue">{total_items}</div><div class="lbl">Ürün Kalemi</div></div>
  <div class="stat"><div class="val green">{total_meter:,.0f} mt</div><div class="lbl">Toplam Metre</div></div>
  <div class="stat"><div class="val purple">{total_kg:,.0f} kg</div><div class="lbl">Toplam Kilo</div></div>
  <div class="stat"><div class="val red">{total_value:,.0f} $</div><div class="lbl">Stok Değeri</div></div>
</div>
<div class="card">
  <div class="card-header">Depo / Lokasyon Özeti</div>
  <table><tr><th>Grup</th><th>Kalem</th><th>Metre</th><th>Kilo</th><th>Değer</th></tr>{loc_rows}</table>
</div>"""
    return _page("Dashboard", content, user, "dashboard")


def _stok_page(user, search="", location="", ftype=""):
    if location.startswith("__GRP_"):
        grp_name = location[7:-2]
        grp_locs = [l["name"] for l in db.get_active_locations() if l["group_name"]==grp_name]
        rows = []
        for gl in grp_locs: rows.extend(db.get_all_fabrics(search, gl, ftype))
    else:
        rows = db.get_all_fabrics(search, location, ftype)

    all_locs  = db.get_active_locations()
    from collections import defaultdict
    grps = defaultdict(list)
    for l in all_locs: grps[l["group_name"]].append(l["name"])
    loc_opts = '<option value="">Tüm Lokasyonlar</option>'
    for g in sorted(grps.keys()):
        if g == "DEPO":
            sel = 'selected' if location == f"__GRP_DEPO__" else ""
            loc_opts += f'<option value="__GRP_DEPO__" {sel}>DEPO (Tümü)</option>'
        else:
            for n in sorted(grps[g]):
                sel = 'selected' if location == n else ""
                loc_opts += f'<option value="{n}" {sel}>{n}</option>'

    type_opts = "".join(
        f'<option value="{t}" {"selected" if ftype==t else ""}>{t}</option>'
        for t in ["","HAM","PFD","BOYALI","BASKILI"]
    )

    TYPE_BADGES = {"HAM":"b-ham","PFD":"b-pfd","BOYALI":"b-boyali","BASKILI":"b-baskili"}
    table_rows = ""
    for r in rows:
        mt  = r["meter"] or 0
        kg  = r["kg"]    or 0
        fiy = r["birim_fiyat"] or 0
        val = mt*fiy if mt>0 else kg*fiy
        tip = r["fabric_type"] or ""
        tip_badge = f'<span class="badge {TYPE_BADGES.get(tip,"")}">{tip}</span>' if tip else ""
        can_edit = user and user.get("role") == "admin" and not is_readonly()
        actions = f'''<a href="/duzenle?id={r["id"]}" class="btn btn-warn btn-sm">✎</a>
                      <a href="/sil?id={r["id"]}" class="btn btn-danger btn-sm" onclick="return confirm('Silinsin mi?')">✕</a>''' if can_edit else ""
        table_rows += f"""<tr>
          <td><b>{r['product_code'] or ''}</b><br><small class="text-muted">{r['product_name'] or ''}</small></td>
          <td>{r['color'] or ''}</td>
          <td><span class="badge b-loc">{r['location'] or ''}</span></td>
          <td>{tip_badge}</td>
          <td>{r['lot'] or ''}</td>
          <td class="num">{mt:,.2f}</td>
          <td class="num">{kg:,.2f}</td>
          <td class="num" style="color:#1565C0;font-weight:600">{fiy:,.2f} $</td>
          <td class="num" style="color:#B71C1C;font-weight:700">{f"{val:,.0f} $" if val else ""}</td>
          <td><a href="/detay?id={r['id']}" class="btn btn-primary btn-sm">Detay</a> {actions}</td>
        </tr>"""

    add_btn = '<a href="/yeni" class="btn btn-success" style="margin-left:8px">＋ Yeni Kumaş</a>' if user and user.get("role")=="admin" and not is_readonly() else ""
    content = f"""
<div class="search-bar">
  <form method="get" action="/stok" style="display:contents">
    <input name="q" value="{search}" placeholder="Ürün kodu, adı, renk...">
    <select name="loc" onchange="this.form.submit()">{loc_opts}</select>
    <select name="tip" onchange="this.form.submit()">
      <option value="">Tüm Tipler</option>{type_opts}
    </select>
    <button type="submit" class="btn btn-primary">Ara</button>
    {add_btn}
  </form>
</div>
<div class="card">
  <div class="card-header">Stok Listesi — {len(rows)} kayıt</div>
  <div style="overflow-x:auto">
  <table>
    <tr><th>Ürün</th><th>Renk</th><th>Lokasyon</th><th>Tip</th><th>Lot</th><th>Metre</th><th>Kilo</th><th>Birim $</th><th>Değer $</th><th></th></tr>
    {table_rows if table_rows else '<tr><td colspan="10" style="text-align:center;padding:30px;color:#9E9E9E">Kayıt bulunamadı</td></tr>'}
  </table>
  </div>
</div>"""
    return _page("Stok Listesi", content, user, "stok")


def _detay_page(user, fabric_id):
    fabric = db.get_fabric(fabric_id)
    if not fabric:
        return _page("Hata", '<div class="alert alert-err">Kayıt bulunamadı</div>', user)
    movements = db.get_movements(fabric_id)
    mt  = fabric["meter"] or 0
    kg  = fabric["kg"]    or 0
    fiy = fabric["birim_fiyat"] or 0
    val = mt*fiy if mt>0 else kg*fiy

    mv_rows = ""
    for m in movements:
        t = m["movement_type"]
        cls = "b-giris" if t=="GİRİŞ" else ("b-silme" if t=="SİLME" else "b-cikis")
        mv_rows += f"""<tr>
          <td>{str(m['movement_date'])[:16]}</td>
          <td><span class="badge {cls}">{t}</span></td>
          <td class="num">{m['meter']:,.2f} mt</td>
          <td class="num">{m['kg']:,.2f} kg</td>
          <td>{m['user_name'] or '—'}</td>
          <td>{m['notes'] or ''}</td>
        </tr>"""

    tip = fabric['fabric_type'] or ''
    TYPE_BADGES = {"HAM":"b-ham","PFD":"b-pfd","BOYALI":"b-boyali","BASKILI":"b-baskili"}
    tip_badge = f'<span class="badge {TYPE_BADGES.get(tip,"")}">{tip}</span>' if tip else "—"

    actions = ""
    if user and user.get("role") == "admin" and not is_readonly():
        actions = f'''
        <a href="/giris?id={fabric_id}" class="btn btn-success">↑ Stok Giriş</a>
        <a href="/cikis?id={fabric_id}" class="btn btn-danger" style="margin-left:8px">↓ Stok Çıkış</a>
        <a href="/duzenle?id={fabric_id}" class="btn btn-warn" style="margin-left:8px">✎ Düzenle</a>'''

    content = f"""
<div class="card">
  <div class="card-header">{fabric['product_code']} / {fabric['color']}</div>
  <div class="card-body">
    <div class="form-row">
      <div>
        <table style="width:100%">
          <tr><td style="color:#555;width:120px">Ürün Kodu</td><td><b>{fabric['product_code']}</b></td></tr>
          <tr><td style="color:#555">Ürün Bilgisi</td><td>{fabric['product_name'] or '—'}</td></tr>
          <tr><td style="color:#555">Renk</td><td>{fabric['color'] or '—'}</td></tr>
          <tr><td style="color:#555">Lokasyon</td><td><span class="badge b-loc">{fabric['location'] or '—'}</span></td></tr>
          <tr><td style="color:#555">Kumaş Tipi</td><td>{tip_badge}</td></tr>
          <tr><td style="color:#555">Lot</td><td>{fabric['lot'] or '—'}</td></tr>
        </table>
      </div>
      <div>
        <table style="width:100%">
          <tr><td style="color:#555;width:120px">Metre</td><td><b style="color:#2E7D32;font-size:18px">{mt:,.2f} mt</b></td></tr>
          <tr><td style="color:#555">Kilo</td><td><b style="color:#6A1B9A">{kg:,.2f} kg</b></td></tr>
          <tr><td style="color:#555">Birim Fiyat</td><td>{fiy:,.2f} $</td></tr>
          <tr><td style="color:#555">Toplam Değer</td><td><b style="color:#B71C1C;font-size:16px">{val:,.0f} $</b></td></tr>
          <tr><td style="color:#555">Açıklama</td><td>{fabric['description'] or '—'}</td></tr>
        </table>
      </div>
    </div>
    {actions}
  </div>
</div>
<div class="card">
  <div class="card-header">Hareket Geçmişi ({len(movements)} kayıt)</div>
  <div style="overflow-x:auto">
  <table>
    <tr><th>Tarih</th><th>Tür</th><th>Metre</th><th>Kilo</th><th>Kullanıcı</th><th>Not</th></tr>
    {mv_rows if mv_rows else '<tr><td colspan="6" style="text-align:center;padding:20px;color:#9E9E9E">Hareket yok</td></tr>'}
  </table>
  </div>
</div>
<a href="/stok" style="color:#1565C0">← Stok Listesine Dön</a>"""
    return _page(f"{fabric['product_code']}", content, user, "stok")


def _hareket_page(user):
    movements = db.get_all_movements(300)
    from datetime import date
    today = date.today().isoformat()
    rows = ""
    for m in movements:
        t = m["movement_type"]
        cls = "b-giris" if t=="GİRİŞ" else ("b-silme" if t=="SİLME" else "b-cikis")
        is_today = str(m["movement_date"]).startswith(today)
        style = "font-weight:bold" if is_today else ""
        rows += f"""<tr style="{style}">
          <td>{str(m['movement_date'])[:16]}</td>
          <td><span class="badge {cls}">{t}</span></td>
          <td><a href="/detay?id={m['fabric_id']}" style="color:#1565C0"><b>{m['product_code'] or ''}</b></a>
              <small class="text-muted"> {m['color'] or ''}</small></td>
          <td class="num">{m['meter']:,.2f}</td>
          <td class="num">{m['kg']:,.2f}</td>
          <td>{m['user_name'] or '—'}</td>
          <td>{m['notes'] or ''}</td>
        </tr>"""
    content = f"""<div class="card">
  <div class="card-header">Son 300 Hareket</div>
  <div style="overflow-x:auto">
  <table><tr><th>Tarih</th><th>Tür</th><th>Ürün</th><th>Metre</th><th>Kilo</th><th>Kullanıcı</th><th>Not</th></tr>
  {rows if rows else '<tr><td colspan="7" style="text-align:center;padding:30px;color:#9E9E9E">Kayıt yok</td></tr>'}
  </table></div></div>"""
    return _page("Hareketler", content, user, "hareket")


def _movement_form(user, fabric_id, movement_type, error="", post_data=None):
    fabric = db.get_fabric(fabric_id)
    if not fabric:
        return _page("Hata", '<div class="alert alert-err">Kayıt bulunamadı</div>', user)
    label = "↑ Stok Giriş" if movement_type=="GİRİŞ" else "↓ Stok Çıkış"
    color = "#2E7D32" if movement_type=="GİRİŞ" else "#C62828"
    err = f'<div class="alert alert-err">{error}</div>' if error else ""
    pd = post_data or {}
    route = "/giris" if movement_type=="GİRİŞ" else "/cikis"
    content = f"""
{err}
<div class="card">
  <div class="card-header" style="background:{color}">{label}</div>
  <div class="card-body">
    <div style="background:#E3F2FD;padding:10px;border-radius:4px;margin-bottom:14px">
      <b>{fabric['product_code']}</b> / {fabric['color']} &nbsp;|&nbsp;
      Lokasyon: {fabric['location']} &nbsp;|&nbsp;
      Mevcut: <b>{fabric['meter']:,.2f} mt</b> / <b>{fabric['kg']:,.2f} kg</b>
    </div>
    <form method="post" action="{route}?id={fabric_id}">
      <div class="form-row">
        <div class="form-group">
          <label>Metre</label>
          <input name="meter" type="number" step="0.01" min="0" value="{pd.get('meter','')}" placeholder="0.00">
        </div>
        <div class="form-group">
          <label>Kilo</label>
          <input name="kg" type="number" step="0.01" min="0" value="{pd.get('kg','')}" placeholder="0.00">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Top/Adet</label>
          <input name="piece_count" value="{pd.get('piece_count','')}">
        </div>
        <div class="form-group">
          <label>Not</label>
          <input name="notes" value="{pd.get('notes','')}">
        </div>
      </div>
      <button type="submit" class="btn btn-primary" style="background:{color}">Kaydet</button>
      <a href="/detay?id={fabric_id}" class="btn btn-primary" style="background:#757575;margin-left:8px">İptal</a>
    </form>
  </div>
</div>"""
    key = "giris" if movement_type=="GİRİŞ" else "cikis"
    return _page(label, content, user, key)


def _fabric_form(user, fabric=None, error="", post_data=None):
    is_new = fabric is None
    pd = post_data or {}

    # Lokasyon seçenekleri
    all_locs = db.get_active_locations()
    from collections import defaultdict
    grps = defaultdict(list)
    for l in all_locs: grps[l["group_name"]].append(l["name"])
    loc_opts = '<option value="">— Seçiniz —</option>'
    cur_loc = pd.get("location") or (fabric["location"] if fabric else "")
    for g in sorted(grps.keys()):
        loc_opts += f'<optgroup label="── {g} ──">'
        for n in sorted(grps[g]):
            sel = "selected" if cur_loc==n else ""
            loc_opts += f'<option value="{n}" {sel}>{n}</option>'
        loc_opts += "</optgroup>"

    cur_type = pd.get("fabric_type") or (fabric["fabric_type"] if fabric else "")
    type_opts = '<option value="">— Seçiniz —</option>' + "".join(
        f'<option value="{t}" {"selected" if cur_type==t else ""}>{t}</option>'
        for t in ["HAM","PFD","BOYALI","BASKILI"]
    )

    def v(key, default=""):
        if post_data and key in post_data: return post_data[key]
        if fabric: return fabric.get(key) or default
        return default

    err = f'<div class="alert alert-err">{error}</div>' if error else ""
    title = "Yeni Kumaş" if is_new else f"Düzenle: {fabric['product_code']}"
    action = "/yeni" if is_new else f"/duzenle?id={fabric['id']}"

    content = f"""
{err}
<div class="card">
  <div class="card-header">{title}</div>
  <div class="card-body">
    <form method="post" action="{action}">
      <div class="form-row">
        <div class="form-group">
          <label>Ürün Kodu <span class="required">*</span></label>
          <input name="product_code" value="{v('product_code')}" required>
        </div>
        <div class="form-group">
          <label>Ürün Bilgisi</label>
          <input name="product_name" value="{v('product_name')}">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Renk</label>
          <input name="color" value="{v('color')}">
        </div>
        <div class="form-group">
          <label>Lot</label>
          <input name="lot" value="{v('lot')}">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Lokasyon <span class="required">*</span></label>
          <select name="location">{loc_opts}</select>
        </div>
        <div class="form-group">
          <label>Kumaş Tipi <span class="required">*</span></label>
          <select name="fabric_type">{type_opts}</select>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Metre</label>
          <input name="meter" type="number" step="0.01" min="0" value="{v('meter','0')}">
        </div>
        <div class="form-group">
          <label>Kilo</label>
          <input name="kg" type="number" step="0.01" min="0" value="{v('kg','0')}">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Top/Adet</label>
          <input name="piece_count" value="{v('piece_count')}">
        </div>
        <div class="form-group">
          <label>Birim Fiyat ($/mt) <span class="required">*</span></label>
          <input name="birim_fiyat" type="number" step="0.01" min="0" value="{v('birim_fiyat','0')}">
        </div>
      </div>
      <div class="form-group">
        <label>Açıklama</label>
        <textarea name="description" rows="2">{v('description')}</textarea>
      </div>
      <button type="submit" class="btn btn-success">Kaydet</button>
      <a href="/stok" class="btn btn-primary" style="background:#757575;margin-left:8px">İptal</a>
    </form>
  </div>
</div>"""
    return _page(title, content, user, "yeni" if is_new else "stok")


# ── POST veri parse ──────────────────────────────────────────────

def _parse_post(handler):
    length = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(length).decode("utf-8")
    data = {}
    for part in raw.split("&"):
        k, _, v = part.partition("=")
        data[unquote_plus(k)] = unquote_plus(v)
    return data


# ── HTTP Handler ─────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def _send(self, body, code=200, cookie=None, redirect=None):
        if redirect:
            self.send_response(302)
            self.send_header("Location", redirect)
            if cookie: self.send_header("Set-Cookie", cookie)
            self.end_headers()
            return
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if cookie: self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs     = parse_qs(parsed.query)
        path   = parsed.path
        user   = _get_session(self.headers)

        # Giriş gerektiren sayfalar
        if path not in ("/login", "/favicon.ico") and not user:
            self._send("", redirect="/login")
            return

        # İzleme modunda işlem sayfaları kapalı
        if is_readonly() and path in ("/giris", "/cikis", "/yeni", "/duzenle", "/sil"):
            self._send("", redirect="/stok")
            return

        try:
            if path in ("/", "/dashboard"):
                self._send(_dashboard(user))
            elif path == "/stok":
                self._send(_stok_page(user,
                    search  =qs.get("q",   [""])[0],
                    location=qs.get("loc", [""])[0],
                    ftype   =qs.get("tip", [""])[0]))
            elif path == "/detay":
                self._send(_detay_page(user, int(qs.get("id",[0])[0])))
            elif path == "/hareket":
                self._send(_hareket_page(user))
            elif path == "/giris":
                fid = int(qs.get("id",[0])[0])
                self._send(_movement_form(user, fid, "GİRİŞ"))
            elif path == "/cikis":
                fid = int(qs.get("id",[0])[0])
                self._send(_movement_form(user, fid, "ÇIKIŞ"))
            elif path == "/yeni":
                if user.get("role") != "admin":
                    self._send("", redirect="/stok"); return
                self._send(_fabric_form(user))
            elif path == "/duzenle":
                if user.get("role") != "admin":
                    self._send("", redirect="/stok"); return
                fid = int(qs.get("id",[0])[0])
                self._send(_fabric_form(user, db.get_fabric(fid)))
            elif path == "/sil":
                if user.get("role") != "admin":
                    self._send("", redirect="/stok"); return
                fid = int(qs.get("id",[0])[0])
                db.soft_delete_fabric(fid, user["full_name"])
                self._send("", redirect="/stok")
            elif path == "/logout":
                _delete_session(self.headers)
                self._send("", cookie="bk_token=; Max-Age=0; Path=/", redirect="/login")
            elif path == "/login":
                self._send(_login_page())
            else:
                self._send(_page("404", '<div class="alert alert-err">Sayfa bulunamadı</div>', user))
        except Exception as e:
            import traceback
            self._send(_page("Hata", f'<div class="alert alert-err">{e}</div>', user))

    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        qs     = parse_qs(parsed.query)
        user   = _get_session(self.headers)

        try:
            if path == "/login":
                pd = _parse_post(self)
                u  = db.authenticate(pd.get("username",""), pd.get("password",""))
                if u:
                    token = _create_session(u)
                    self._send("", cookie=f"bk_token={token}; Path=/; HttpOnly", redirect="/")
                else:
                    self._send(_login_page("Kullanıcı adı veya şifre hatalı!"))
                return

            if not user:
                self._send("", redirect="/login"); return

            # İzleme modunda hiçbir değişiklik kabul edilmez
            if is_readonly():
                self._send("", redirect="/"); return

            if path == "/giris":
                fid = int(qs.get("id",[0])[0])
                pd  = _parse_post(self)
                meter = float(pd.get("meter") or 0)
                kg    = float(pd.get("kg")    or 0)
                if meter <= 0 and kg <= 0:
                    fabric = db.get_fabric(fid)
                    self._send(_movement_form(user, fid, "GİRİŞ",
                        "Metre veya kilo giriniz!", pd)); return
                db.add_movement(fid, "GİRİŞ", meter, kg,
                    pd.get("piece_count",""), pd.get("notes",""), user["full_name"])
                self._send("", redirect=f"/detay?id={fid}")

            elif path == "/cikis":
                fid = int(qs.get("id",[0])[0])
                pd  = _parse_post(self)
                meter = float(pd.get("meter") or 0)
                kg    = float(pd.get("kg")    or 0)
                if meter <= 0 and kg <= 0:
                    self._send(_movement_form(user, fid, "ÇIKIŞ",
                        "Metre veya kilo giriniz!", pd)); return
                db.add_movement(fid, "ÇIKIŞ", meter, kg,
                    pd.get("piece_count",""), pd.get("notes",""), user["full_name"])
                self._send("", redirect=f"/detay?id={fid}")

            elif path == "/yeni":
                if user.get("role") != "admin":
                    self._send("", redirect="/stok"); return
                pd = _parse_post(self)
                errors = []
                if not pd.get("product_code","").strip(): errors.append("Ürün kodu zorunlu")
                if not pd.get("location","").strip():     errors.append("Lokasyon zorunlu")
                if not pd.get("fabric_type","").strip():  errors.append("Kumaş tipi zorunlu")
                if float(pd.get("birim_fiyat") or 0) <= 0: errors.append("Birim fiyat zorunlu")
                if errors:
                    self._send(_fabric_form(user, error=", ".join(errors), post_data=pd)); return
                db.add_fabric(
                    pd.get("product_name",""), pd.get("product_code","").upper(),
                    pd.get("color","").upper(), pd.get("location",""),
                    float(pd.get("meter") or 0), float(pd.get("kg") or 0),
                    pd.get("piece_count",""), float(pd.get("birim_fiyat") or 0),
                    pd.get("fabric_type",""), pd.get("lot",""), pd.get("description",""),
                    user_name=user["full_name"]
                )
                self._send("", redirect="/stok")

            elif path == "/duzenle":
                if user.get("role") != "admin":
                    self._send("", redirect="/stok"); return
                fid = int(qs.get("id",[0])[0])
                pd  = _parse_post(self)
                db.update_fabric(fid,
                    pd.get("product_name",""), pd.get("product_code","").upper(),
                    pd.get("color","").upper(), pd.get("location",""),
                    float(pd.get("meter") or 0), float(pd.get("kg") or 0),
                    pd.get("piece_count",""), float(pd.get("birim_fiyat") or 0),
                    pd.get("fabric_type",""), pd.get("lot",""), pd.get("description","")
                )
                self._send("", redirect=f"/detay?id={fid}")

        except Exception as e:
            self._send(_page("Hata", f'<div class="alert alert-err">{e}</div>', user))


# ── Sunucu başlat/durdur ─────────────────────────────────────────

def start():
    global _server, _thread
    if _server:
        return get_local_ip(), PORT
    _server = HTTPServer(("0.0.0.0", PORT), Handler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    return get_local_ip(), PORT


def stop():
    global _server, _thread
    if _server:
        _server.shutdown(); _server = None; _thread = None
    stop_ngrok()


def is_running():
    return _server is not None


# ── Ngrok ────────────────────────────────────────────────────────

def start_ngrok():
    global _ngrok_tunnel
    token = get_ngrok_token()
    if not token: raise ValueError("ngrok token girilmemiş")
    if not is_running(): start()
    from pyngrok import ngrok, conf
    conf.get_default().auth_token = token
    _ngrok_tunnel = ngrok.connect(PORT, "http")
    return _ngrok_tunnel.public_url


def stop_ngrok():
    global _ngrok_tunnel
    if _ngrok_tunnel:
        try:
            from pyngrok import ngrok
            ngrok.disconnect(_ngrok_tunnel.public_url)
        except Exception: pass
        _ngrok_tunnel = None


def ngrok_url():    return _ngrok_tunnel.public_url if _ngrok_tunnel else None
def ngrok_running(): return _ngrok_tunnel is not None
