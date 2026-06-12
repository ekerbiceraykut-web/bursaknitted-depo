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

def _request(req, timeout):
    """İsteği çalıştır; hata durumunda sunucunun mesajını ilet (HTTP 4xx/5xx dahil)."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            resp = json.loads(e.read())
        except Exception:
            raise Exception(f"Sunucu hatası (HTTP {e.code})")
    if not resp.get("ok"):
        raise Exception(resp.get("error", "API hatası"))
    return resp.get("data")

def _get(path, params=None, auth=True):
    url = _server_url + path
    if params:
        encoded = urllib.parse.urlencode({k: v for k, v in params.items() if v})
        if encoded:
            url += "?" + encoded
    req = urllib.request.Request(url, headers=_headers() if auth else {})
    return _request(req, 15)

def _post(path, data, auth=True):
    url = _server_url + path
    body = json.dumps(data, ensure_ascii=False).encode()
    req  = urllib.request.Request(url, data=body, method="POST",
                                  headers=_headers() if auth else {"Content-Type":"application/json"})
    return _request(req, 10)

def _put(path, data):
    url  = _server_url + path
    body = json.dumps(data, ensure_ascii=False).encode()
    req  = urllib.request.Request(url, data=body, method="PUT", headers=_headers())
    return _request(req, 10)

def _delete(path):
    req = urllib.request.Request(_server_url + path, method="DELETE", headers=_headers())
    return _request(req, 10)


# ── Fabrics ──────────────────────────────────────────────────────

def get_all_fabrics(search="", location="", fabric_type="", include_deleted=False):
    return _get("/api/fabrics", {"search": search, "location": location, "fabric_type": fabric_type})

def get_fabric(fid):
    return _get(f"/api/fabrics/{fid}")

def add_fabric(product_name, product_code, color, location, meter, kg,
               piece_count, birim_fiyat, fabric_type, lot, description, user_name="",
               entry_location=""):
    return _post("/api/fabrics", {
        "product_name": product_name, "product_code": product_code,
        "color": color, "location": location, "meter": meter, "kg": kg,
        "piece_count": piece_count, "birim_fiyat": birim_fiyat,
        "fabric_type": fabric_type, "lot": lot, "description": description,
        "entry_location": entry_location,
    })["id"]

def update_fabric(fid, product_name, product_code, color, location, meter, kg,
                  piece_count, birim_fiyat, fabric_type, lot, description,
                  entry_location=None):
    _put(f"/api/fabrics/{fid}", {
        "product_name": product_name, "product_code": product_code,
        "color": color, "location": location, "meter": meter, "kg": kg,
        "piece_count": piece_count, "birim_fiyat": birim_fiyat,
        "fabric_type": fabric_type, "lot": lot, "description": description,
        "entry_location": entry_location,
    })

def soft_delete_fabric(fid, user_name=""):
    _delete(f"/api/fabrics/{fid}")

def restore_fabric(fid):
    pass  # Uzak modda geri yükleme API'den yapılır

def reverse_movement(mid):
    pass  # Şimdilik


# ── Movements ────────────────────────────────────────────────────

def add_movement(fid, movement_type, meter, kg, piece_count, notes, user_name="",
                 destination="", destination_type="", deduct_meter=None, deduct_kg=None,
                 out_color="", lab_no="", parti_no=""):
    r = _post("/api/movements", {
        "fabric_id": fid, "movement_type": movement_type,
        "meter": meter, "kg": kg, "piece_count": piece_count, "notes": notes,
        "destination": destination, "destination_type": destination_type,
        "deduct_meter": deduct_meter, "deduct_kg": deduct_kg,
        "out_color": out_color, "lab_no": lab_no, "parti_no": parti_no,
    })
    return (r or {}).get("id")


# ── Customers ────────────────────────────────────────────────────

def get_all_customers(search="", active_only=True):
    return _get("/api/customers", {"search": search,
                                   "active_only": "1" if active_only else "0"}) or []

def get_customer(cid):
    return _get(f"/api/customers/{cid}")

def add_customer(name, code="", phone="", address=""):
    r = _post("/api/customers", {"name": name, "code": code,
                                 "phone": phone, "address": address})
    return (r or {}).get("id")

def update_customer(cid, name, code, phone, address, active=1):
    _put(f"/api/customers/{cid}", {"name": name, "code": code, "phone": phone,
                                   "address": address, "active": active})

def delete_customer(cid):
    _delete(f"/api/customers/{cid}")

def import_customers_bulk(records):
    r = _post("/api/customers/bulk", {"records": records})
    return (r or {}).get("count", 0)


# ── Fire kayıtları ───────────────────────────────────────────────

def get_fire_records():
    return _get("/api/fire") or []

def add_fire_record(fabric_id, movement_id, product_code, color, lot, boyahane,
                    customer, pre_meter, pre_kg, out_meter, out_kg, fire_pct,
                    manual_pct=False, record_type="ÇIKIŞ", user_name="",
                    out_color="", lab_no="", parti_no=""):
    r = _post("/api/fire", {
        "fabric_id": fabric_id, "movement_id": movement_id,
        "product_code": product_code, "color": color, "lot": lot,
        "boyahane": boyahane, "customer": customer,
        "pre_meter": pre_meter, "pre_kg": pre_kg,
        "out_meter": out_meter, "out_kg": out_kg, "fire_pct": fire_pct,
        "manual_pct": manual_pct, "record_type": record_type,
        "out_color": out_color, "lab_no": lab_no, "parti_no": parti_no,
    })
    return (r or {}).get("id")

def reset_lot_fire(fabric_id, user_name=""):
    return _post("/api/fire/reset", {"fabric_id": fabric_id})

def finalize_lot_if_consumed(fabric_id, user_name=""):
    r = _post("/api/fire/finalize", {"fabric_id": fabric_id})
    return (r or {}).get("finalized", False)

def lot_total_exists(product_code, color, lot, boyahane):
    r = _get("/api/fire/total_exists", {
        "product_code": product_code, "color": color,
        "lot": lot, "boyahane": boyahane,
    })
    return (r or {}).get("exists", False)

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
    _post("/api/locations", {"name": name, "group_name": group_name,
                             "description": description})

def sync_locations():
    _post("/api/locations/sync", {})

def get_all_locations():
    return _get("/api/locations/all") or []

def update_location(loc_id, name, group_name, description, active):
    _put(f"/api/locations/{loc_id}", {"name": name, "group_name": group_name,
                                      "description": description,
                                      "active": 1 if active else 0})

def delete_location(loc_id):
    _delete(f"/api/locations/{loc_id}")


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
