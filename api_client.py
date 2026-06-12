"""
API İstemcisi — Uzak sunucuya bağlanarak veritabanı işlemleri yapar.
database.py ile aynı arayüzü sunar.
"""
import json, urllib.request, urllib.error, urllib.parse, os

_server_url = ""
_token      = ""
_user       = None


# ── Bağlantı ────────────────────────────────────────────────────

def configure(server_url: str):
    global _server_url
    _server_url = server_url.rstrip("/")

def is_configured():
    return bool(_server_url)

def login(username: str, password: str):
    global _token, _user
    data = _post("/api/login", {"username": username, "password": password}, auth=False)
    _token = data["token"]
    _user  = data
    return data

def ping():
    try:
        r = _get("/ping", auth=False)
        return r == "pong"
    except Exception:
        return False

def get_current_user():
    return _user


# ── HTTP yardımcıları ────────────────────────────────────────────

def _headers():
    h = {"Content-Type": "application/json", "X-Token": _token}
    return h

def _get(path, params=None, auth=True):
    url = _server_url + path
    if params:
        encoded = urllib.parse.urlencode({k: v for k, v in params.items() if v})
        if encoded:
            url += "?" + encoded
    req = urllib.request.Request(url, headers=_headers() if auth else {})
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise Exception(resp.get("error", "API hatası"))
    return resp.get("data")

def _post(path, data, auth=True):
    url = _server_url + path
    body = json.dumps(data, ensure_ascii=False).encode()
    req  = urllib.request.Request(url, data=body, method="POST",
                                  headers=_headers() if auth else {"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise Exception(resp.get("error", "API hatası"))
    return resp.get("data")

def _put(path, data):
    url  = _server_url + path
    body = json.dumps(data, ensure_ascii=False).encode()
    req  = urllib.request.Request(url, data=body, method="PUT", headers=_headers())
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise Exception(resp.get("error", "API hatası"))

def _delete(path):
    req = urllib.request.Request(_server_url + path, method="DELETE", headers=_headers())
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise Exception(resp.get("error", "API hatası"))


# ── Fabrics ──────────────────────────────────────────────────────

def get_all_fabrics(search="", location="", fabric_type="", include_deleted=False):
    return _get("/api/fabrics", {"search": search, "location": location, "fabric_type": fabric_type})

def get_fabric(fid):
    return _get(f"/api/fabrics/{fid}")

def add_fabric(product_name, product_code, color, location, meter, kg,
               piece_count, birim_fiyat, fabric_type, lot, description, user_name=""):
    return _post("/api/fabrics", {
        "product_name": product_name, "product_code": product_code,
        "color": color, "location": location, "meter": meter, "kg": kg,
        "piece_count": piece_count, "birim_fiyat": birim_fiyat,
        "fabric_type": fabric_type, "lot": lot, "description": description,
    })["id"]

def update_fabric(fid, product_name, product_code, color, location, meter, kg,
                  piece_count, birim_fiyat, fabric_type, lot, description):
    _put(f"/api/fabrics/{fid}", {
        "product_name": product_name, "product_code": product_code,
        "color": color, "location": location, "meter": meter, "kg": kg,
        "piece_count": piece_count, "birim_fiyat": birim_fiyat,
        "fabric_type": fabric_type, "lot": lot, "description": description,
    })

def soft_delete_fabric(fid, user_name=""):
    _delete(f"/api/fabrics/{fid}")

def restore_fabric(fid):
    pass  # Uzak modda geri yükleme API'den yapılır

def reverse_movement(mid):
    pass  # Şimdilik


# ── Movements ────────────────────────────────────────────────────

def add_movement(fid, movement_type, meter, kg, piece_count, notes, user_name=""):
    r = _post("/api/movements", {
        "fabric_id": fid, "movement_type": movement_type,
        "meter": meter, "kg": kg, "piece_count": piece_count, "notes": notes,
    })
    return (r or {}).get("id")

def get_movements(fid):
    return _get("/api/movements", {"fabric_id": str(fid)})

def get_all_movements(limit=300):
    return _get("/api/movements", {"limit": str(limit)})

def get_movements_by_range(start_date, end_date):
    # Sunucuda aralık endpoint'i yok; tümünü çekip istemci tarafında filtrele
    rows = _get("/api/movements", {"limit": "5000"}) or []
    return [m for m in rows if start_date <= str(m.get("movement_date", ""))[:10] <= end_date]


# ── Locations ────────────────────────────────────────────────────

def get_active_locations():
    return _get("/api/locations")

def get_locations():
    rows = get_active_locations()
    return [r["name"] for r in rows] if rows else []

def add_location(name, group_name="DEPO", description=""):
    pass  # Uzak modda lokasyon yönetimi masaüstü uygulamadan yapılır

def sync_locations():
    pass

def get_all_locations():
    return get_active_locations()

def update_location(*a, **kw): pass
def delete_location(*a, **kw): pass


# ── Summary ──────────────────────────────────────────────────────

def get_summary():
    return _get("/api/summary") or {}


# ── Users ────────────────────────────────────────────────────────

def authenticate(username, password):
    """Uzak modda login() kullanılır, bu fonksiyon kullanılmaz."""
    return None

def get_all_users():
    return _get("/api/users") or []

def add_user(username, full_name, password, role="kullanici"):
    _post("/api/users", {"username": username, "full_name": full_name,
                         "password": password, "role": role})

def update_user_password(uid, pw):
    _put(f"/api/users/{uid}/password", {"password": pw})

def toggle_user_active(uid):
    pass

def delete_user(uid):
    pass


# ── Import ───────────────────────────────────────────────────────

def import_fabrics_bulk(records):
    for r in records:
        try:
            add_fabric(
                r.get("product_name",""), r.get("product_code",""),
                r.get("color",""),        r.get("location",""),
                r.get("meter",0),         r.get("kg",0),
                r.get("piece_count",""),  0,
                r.get("fabric_type",""),  r.get("lot",""),
                r.get("description","")
            )
        except Exception:
            pass
