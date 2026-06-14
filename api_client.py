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
    """İsteği çalıştır; hata durumunda sunucunun mesajını ilet (HTTP 4xx/5xx, ağ/timeout dahil)."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            resp = json.loads(e.read())
        except Exception:
            raise Exception(f"Sunucu hatası (HTTP {e.code})")
    except (urllib.error.URLError, OSError) as e:
        raise Exception(f"Sunucuya bağlanılamadı: {getattr(e, 'reason', e)}")
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
    return _request(req, 30)   # bulut sunucu yanıtı yerel ağdan yavaş olabilir

def _post(path, data, auth=True):
    url = _server_url + path
    body = json.dumps(data, ensure_ascii=False).encode()
    req  = urllib.request.Request(url, data=body, method="POST",
                                  headers=_headers() if auth else {"Content-Type":"application/json"})
    return _request(req, 30)

def _put(path, data):
    url  = _server_url + path
    body = json.dumps(data, ensure_ascii=False).encode()
    req  = urllib.request.Request(url, data=body, method="PUT", headers=_headers())
    return _request(req, 30)

def _delete(path):
    req = urllib.request.Request(_server_url + path, method="DELETE", headers=_headers())
    return _request(req, 30)


# ── Fabrics ──────────────────────────────────────────────────────

def get_all_fabrics(search="", location="", fabric_type="", include_deleted=False):
    return _get("/api/fabrics", {"search": search, "location": location, "fabric_type": fabric_type})

def get_fabric(fid):
    return _get(f"/api/fabrics/{fid}")

def add_fabric(product_name, product_code, color, location, meter, kg,
               piece_count, birim_fiyat, fabric_type, lot, description, user_name="",
               entry_location="", lab_no="", print_type="", zemin_rengi="", baski_desen_no=""):
    return _post("/api/fabrics", {
        "product_name": product_name, "product_code": product_code,
        "color": color, "location": location, "meter": meter, "kg": kg,
        "piece_count": piece_count, "birim_fiyat": birim_fiyat,
        "fabric_type": fabric_type, "lot": lot, "description": description,
        "entry_location": entry_location, "lab_no": lab_no,
        "print_type": print_type, "zemin_rengi": zemin_rengi, "baski_desen_no": baski_desen_no,
    })["id"]

def update_fabric(fid, product_name, product_code, color, location, meter, kg,
                  piece_count, birim_fiyat, fabric_type, lot, description,
                  entry_location=None, lab_no=None, print_type=None, zemin_rengi=None,
                  baski_desen_no=None):
    _put(f"/api/fabrics/{fid}", {
        "product_name": product_name, "product_code": product_code,
        "color": color, "location": location, "meter": meter, "kg": kg,
        "piece_count": piece_count, "birim_fiyat": birim_fiyat,
        "fabric_type": fabric_type, "lot": lot, "description": description,
        "entry_location": entry_location, "lab_no": lab_no,
        "print_type": print_type, "zemin_rengi": zemin_rengi, "baski_desen_no": baski_desen_no,
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
                 out_color="", lab_no="", parti_no="",
                 out_fabric_type="", out_print_type="", out_zemin_rengi="", out_baski_desen_no=""):
    r = _post("/api/movements", {
        "fabric_id": fid, "movement_type": movement_type,
        "meter": meter, "kg": kg, "piece_count": piece_count, "notes": notes,
        "destination": destination, "destination_type": destination_type,
        "deduct_meter": deduct_meter, "deduct_kg": deduct_kg,
        "out_color": out_color, "lab_no": lab_no, "parti_no": parti_no,
        "out_fabric_type": out_fabric_type, "out_print_type": out_print_type,
        "out_zemin_rengi": out_zemin_rengi, "out_baski_desen_no": out_baski_desen_no,
    })
    return (r or {}).get("id")


def download_backup(dest_path):
    """Buluttaki veritabanının tutarlı kopyasını indirir (admin gerekli)."""
    import base64
    r = _get("/api/backup")
    data = base64.b64decode(r["db_base64"])
    with open(dest_path, "wb") as f:
        f.write(data)
    return len(data)


# ── Customers ────────────────────────────────────────────────────

def get_all_customers(search="", active_only=True):
    return _get("/api/customers", {"search": search,
                                   "active_only": "1" if active_only else "0"}) or []

def get_customer(cid):
    return _get(f"/api/customers/{cid}")

def add_customer(name, code="", phone="", address="", tax_no=""):
    r = _post("/api/customers", {"name": name, "code": code,
                                 "phone": phone, "address": address, "tax_no": tax_no})
    return (r or {}).get("id")

def update_customer(cid, name, code, phone, address, tax_no="", active=1):
    _put(f"/api/customers/{cid}", {"name": name, "code": code, "phone": phone,
                                   "address": address, "tax_no": tax_no, "active": active})

def delete_customer(cid):
    _delete(f"/api/customers/{cid}")

def import_customers_bulk(records):
    r = _post("/api/customers/bulk", {"records": records})
    return (r or {}).get("count", 0)


# ── Tedarikçiler ─────────────────────────────────────────────────

def get_all_suppliers(search="", active_only=True):
    return _get("/api/suppliers", {"search": search,
                                   "active_only": "1" if active_only else "0"}) or []

def get_supplier(sid):
    return _get(f"/api/suppliers/{sid}")

def add_supplier(name, code="", phone="", address="", tax_no="", email=""):
    r = _post("/api/suppliers", {"name": name, "code": code,
                                 "phone": phone, "address": address, "tax_no": tax_no,
                                 "email": email})
    return (r or {}).get("id")

def update_supplier(sid, name, code, phone, address, tax_no="", active=1, email=""):
    _put(f"/api/suppliers/{sid}", {"name": name, "code": code, "phone": phone,
                                   "address": address, "tax_no": tax_no, "active": active,
                                   "email": email})

def delete_supplier(sid):
    _delete(f"/api/suppliers/{sid}")

def import_suppliers_bulk(records):
    r = _post("/api/suppliers/bulk", {"records": records})
    return (r or {}).get("count", 0)


# ── Ürün Kataloğu ────────────────────────────────────────────────

def get_all_products(search="", active_only=True):
    return _get("/api/products", {"search": search,
                                  "active_only": "1" if active_only else "0"}) or []

def get_product(pid):
    return _get(f"/api/products/{pid}")

def get_product_by_code(code):
    for p in get_all_products(search=code, active_only=False):
        if str(p.get("product_code","")).strip().upper() == code.strip().upper():
            return p
    return None

def add_product(product_code, product_name="", composition="", width="", gramaj="", shrinkage="", price=0, supplier="", reference_code=""):
    r = _post("/api/products", {
        "product_code": product_code, "product_name": product_name,
        "composition": composition, "width": width,
        "gramaj": gramaj, "shrinkage": shrinkage,
        "price": price, "supplier": supplier, "reference_code": reference_code,
    })
    return (r or {}).get("id")

def update_product(pid, product_code, product_name, composition, width, gramaj, shrinkage, price, supplier, active=1, reference_code=""):
    _put(f"/api/products/{pid}", {
        "product_code": product_code, "product_name": product_name,
        "composition": composition, "width": width,
        "gramaj": gramaj, "shrinkage": shrinkage,
        "price": price, "supplier": supplier, "active": active,
        "reference_code": reference_code,
    })

def delete_product(pid):
    _delete(f"/api/products/{pid}")

def import_products_bulk(records):
    r = _post("/api/products/bulk", {"records": records})
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
    _put(f"/api/users/{uid}/toggle", {})

def delete_user(uid):
    _delete(f"/api/users/{uid}")


# ── Siparişler ───────────────────────────────────────────────────

def get_all_orders(search="", status=""):
    return _get("/api/orders", {"search": search, "status": status}) or []

def get_order(oid):
    return _get(f"/api/orders/{oid}")

def add_order(customer_id, customer_name, customer_ref, currency, payment_method,
               delivery_terms, delivery_address, delivery_date, order_date,
               notes, items, created_by=""):
    r = _post("/api/orders", {
        "customer_id": customer_id, "customer_name": customer_name, "customer_ref": customer_ref,
        "currency": currency,
        "payment_method": payment_method, "delivery_terms": delivery_terms,
        "delivery_address": delivery_address, "delivery_date": delivery_date,
        "order_date": order_date, "notes": notes,
        "items": items, "created_by": created_by,
    })
    return r["id"], r["order_no"]

def update_order(oid, customer_id, customer_name, customer_ref, currency,
                 payment_method, delivery_terms, delivery_address, delivery_date,
                 order_date, notes, items):
    _put(f"/api/orders/{oid}", {
        "customer_id": customer_id, "customer_name": customer_name, "customer_ref": customer_ref,
        "currency": currency,
        "payment_method": payment_method, "delivery_terms": delivery_terms,
        "delivery_address": delivery_address, "delivery_date": delivery_date,
        "order_date": order_date, "notes": notes,
        "items": items,
    })

def delete_order(oid):
    _delete(f"/api/orders/{oid}")

def update_order_status(order_id, status):
    _put(f"/api/orders/{order_id}/status", {"status": status})


# ── Satınalma Siparişleri ──────────────────────────────────────────

def get_fabric_stock_in_depo(product_code, fabric_type="HAM"):
    return _get("/api/stock_in_depo", {"product_code": product_code, "fabric_type": fabric_type}) \
           or {"meter": 0, "kg": 0}

def get_all_purchase_orders(search="", status="", order_id=None):
    params = {"search": search, "status": status}
    if order_id:
        params["order_id"] = str(order_id)
    return _get("/api/purchase_orders", params) or []

def get_purchase_order(po_id):
    return _get(f"/api/purchase_orders/{po_id}")

def add_purchase_order(supplier_id, supplier_name, order_id, order_no, currency,
                       payment_method, delivery_terms, expected_delivery, notes,
                       items, created_by=""):
    r = _post("/api/purchase_orders", {
        "supplier_id": supplier_id, "supplier_name": supplier_name,
        "order_id": order_id, "order_no": order_no, "currency": currency,
        "payment_method": payment_method, "delivery_terms": delivery_terms,
        "expected_delivery": expected_delivery, "notes": notes,
        "items": items, "created_by": created_by,
    })
    return r["id"], r["po_no"]

def update_purchase_order_status(po_id, status):
    _put(f"/api/purchase_orders/{po_id}/status", {"status": status})

def delete_purchase_order(po_id):
    _delete(f"/api/purchase_orders/{po_id}")

def receive_purchase_order_item(po_item_id, meter, kg, location, user_name="",
                                location_group=""):
    _post(f"/api/purchase_orders/items/{po_item_id}/receive",
          {"meter": meter, "kg": kg, "location": location,
           "location_group": location_group})

def get_po_receipts(po_id):
    return _get(f"/api/purchase_orders/{po_id}/receipts") or []

def get_boyahane_queue(status_filter=""):
    return _get("/api/boyahane/queue", {"status": status_filter}) or []

def update_boyahane_receipt_status(receipt_id, status):
    _put(f"/api/boyahane/receipts/{receipt_id}/status", {"status": status})


# ── Ayarlar ──────────────────────────────────────────────────────

def get_company_settings():
    return _get("/api/settings/company") or {}

def save_company_settings(**kwargs):
    _put("/api/settings/company", kwargs)


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
