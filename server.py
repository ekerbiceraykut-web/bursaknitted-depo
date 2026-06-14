"""
Bursa Knitted Depo — API Sunucusu
Ana Mac'te çalışır, diğer bilgisayarlar buraya bağlanır.
Port: 5060

Başlatmak için: python3 server.py
"""
import sys, os, json, hashlib, uuid, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote_plus
import database as db

PORT = int(os.environ.get("PORT", "5060"))   # bulutta Render PORT verir
_tokens: dict = {}  # {token: user_dict}
_login_fails: dict = {}  # {ip: [zaman damgaları]} — kaba kuvvet koruması


def _hash(p): return hashlib.sha256(p.encode()).hexdigest()
def _ok(data=None):  return json.dumps({"ok": True,  "data": data},  ensure_ascii=False)
def _err(msg):       return json.dumps({"ok": False, "error": msg},  ensure_ascii=False)


def _auth(headers):
    token = headers.get("X-Token", "")
    return _tokens.get(token)


class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass  # sessiz

    def _send(self, body, code=200):
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,X-Token")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        qs     = parse_qs(parsed.query)

        # Sağlık kontrolü — token gerekmez
        if path == "/ping":
            return self._send(_ok("pong"))

        user = _auth(self.headers)
        if not user:
            return self._send(_err("Yetkisiz erişim"), 401)

        try:
            # ── Fabrics ──────────────────────────────────────────
            if path == "/api/fabrics":
                rows = db.get_all_fabrics(
                    search      = qs.get("search",[""])[0],
                    location    = qs.get("location",[""])[0],
                    fabric_type = qs.get("fabric_type",[""])[0],
                )
                self._send(_ok([dict(r) for r in rows]))

            elif path.startswith("/api/fabrics/"):
                fid = int(path.split("/")[-1])
                r = db.get_fabric(fid)
                self._send(_ok(dict(r)) if r else _err("Bulunamadı"))

            # ── Movements ────────────────────────────────────────
            elif path == "/api/movements":
                fid = qs.get("fabric_id",[""])[0]
                if fid:
                    rows = db.get_movements(int(fid))
                else:
                    limit = int(qs.get("limit",["300"])[0])
                    rows = db.get_all_movements(limit)
                self._send(_ok([dict(r) for r in rows]))

            # ── Yedek indirme (admin) ────────────────────────────
            elif path == "/api/backup":
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                import sqlite3, base64, tempfile
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
                tmp.close()
                src = sqlite3.connect(db.DB_PATH, timeout=30)
                dst = sqlite3.connect(tmp.name)
                src.backup(dst)   # WAL dahil tutarlı kopya
                dst.close(); src.close()
                with open(tmp.name, "rb") as f:
                    data = f.read()
                os.unlink(tmp.name)
                self._send(_ok({"db_base64": base64.b64encode(data).decode(),
                                "size": len(data)}))

            # ── Fire kayıtları ───────────────────────────────────
            elif path == "/api/fire":
                rows = db.get_fire_records()
                self._send(_ok([dict(r) for r in rows]))

            elif path == "/api/fire/total_exists":
                exists = db.lot_total_exists(
                    qs.get("product_code",[""])[0], qs.get("color",[""])[0],
                    qs.get("lot",[""])[0], qs.get("boyahane",[""])[0])
                self._send(_ok({"exists": exists}))

            # ── Customers ────────────────────────────────────────
            elif path == "/api/customers":
                rows = db.get_all_customers(
                    search=qs.get("search",[""])[0],
                    active_only=qs.get("active_only",["1"])[0] == "1")
                self._send(_ok([dict(r) for r in rows]))

            elif path.startswith("/api/customers/"):
                cid = int(path.split("/")[-1])
                r = db.get_customer(cid)
                self._send(_ok(dict(r)) if r else _err("Bulunamadı"))

            # ── Tedarikçiler ─────────────────────────────────────
            elif path == "/api/suppliers":
                rows = db.get_all_suppliers(
                    search=qs.get("search",[""])[0],
                    active_only=qs.get("active_only",["1"])[0] == "1")
                self._send(_ok([dict(r) for r in rows]))

            elif path.startswith("/api/suppliers/"):
                sid = int(path.split("/")[-1])
                r = db.get_supplier(sid)
                self._send(_ok(dict(r)) if r else _err("Bulunamadı"))

            # ── Ürünler ────────────────────────────────────────────
            elif path == "/api/products":
                rows = db.get_all_products(
                    search=qs.get("search",[""])[0],
                    active_only=qs.get("active_only",["1"])[0] == "1")
                self._send(_ok([dict(r) for r in rows]))

            elif path.startswith("/api/products/"):
                pid = int(path.split("/")[-1])
                r = db.get_product(pid)
                self._send(_ok(dict(r)) if r else _err("Bulunamadı"))

            # ── Locations ────────────────────────────────────────
            elif path == "/api/locations/all":
                rows = db.get_all_locations()
                self._send(_ok([dict(r) for r in rows]))

            elif path == "/api/locations":
                rows = db.get_active_locations()
                self._send(_ok([dict(r) for r in rows]))

            # ── Summary ──────────────────────────────────────────
            elif path == "/api/summary":
                self._send(_ok(dict(db.get_summary())))

            # ── Users (sadece admin) ─────────────────────────────
            elif path == "/api/users":
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                self._send(_ok([dict(r) for r in db.get_all_users()]))

            # ── Siparişler ───────────────────────────────────────
            elif path == "/api/orders":
                rows = db.get_all_orders(
                    search=qs.get("search",[""])[0],
                    status=qs.get("status",[""])[0])
                self._send(_ok([dict(r) for r in rows]))

            elif path.startswith("/api/orders/"):
                oid = int(path.split("/")[-1])
                r = db.get_order(oid)
                self._send(_ok(dict(r)) if r else _err("Bulunamadı"))

            # ── Ayarlar ────────────────────────────────────────────
            elif path == "/api/settings/company":
                self._send(_ok(db.get_company_settings()))

            else:
                self._send(_err("Endpoint bulunamadı"), 404)

        except Exception as e:
            self._send(_err(str(e)), 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        qs     = parse_qs(parsed.query)

        # ── Giriş ────────────────────────────────────────────────
        if path == "/api/login":
            import time as _time
            fwd = self.headers.get("X-Forwarded-For", "")
            ip = fwd.split(",")[0].strip() if fwd else self.client_address[0]
            now = _time.time()
            fails = [t for t in _login_fails.get(ip, []) if now - t < 300]
            if len(fails) >= 5:
                _login_fails[ip] = fails
                return self._send(_err("Çok fazla başarısız deneme — 5 dakika sonra tekrar deneyin"), 429)

            body = self._body()
            u = db.authenticate(body.get("username",""), body.get("password",""))
            if u:
                _login_fails.pop(ip, None)
                token = str(uuid.uuid4())
                _tokens[token] = dict(u)
                data = dict(u); data["token"] = token
                return self._send(_ok(data))
            fails.append(now)
            _login_fails[ip] = fails
            return self._send(_err("Kullanıcı adı veya şifre hatalı"), 401)

        user = _auth(self.headers)
        if not user:
            return self._send(_err("Yetkisiz erişim"), 401)

        try:
            body = self._body()

            # ── Fabric ekle ───────────────────────────────────────
            if path == "/api/fabrics":
                fid = db.add_fabric(
                    body.get("product_name",""), body.get("product_code",""),
                    body.get("color",""),        body.get("location",""),
                    body.get("meter",0),         body.get("kg",0),
                    body.get("piece_count",""),  body.get("birim_fiyat",0),
                    body.get("fabric_type",""),  body.get("lot",""),
                    body.get("description",""),  user_name=user["full_name"],
                    entry_location=body.get("entry_location",""),
                    lab_no=body.get("lab_no",""),
                    print_type=body.get("print_type",""),
                    zemin_rengi=body.get("zemin_rengi",""),
                    baski_desen_no=body.get("baski_desen_no","")
                )
                self._send(_ok({"id": fid}))

            # ── Hareket ekle ─────────────────────────────────────
            elif path == "/api/movements":
                fid = body.get("fabric_id")
                mid = db.add_movement(
                    fid, body.get("movement_type","GİRİŞ"),
                    body.get("meter",0), body.get("kg",0),
                    body.get("piece_count",""), body.get("notes",""),
                    user_name=user["full_name"],
                    destination=body.get("destination",""),
                    destination_type=body.get("destination_type",""),
                    deduct_meter=body.get("deduct_meter"),
                    deduct_kg=body.get("deduct_kg"),
                    out_color=body.get("out_color",""),
                    lab_no=body.get("lab_no",""),
                    parti_no=body.get("parti_no","")
                )
                self._send(_ok({"id": mid}))

            # ── Fire kaydı ekle ──────────────────────────────────
            elif path == "/api/fire":
                rid = db.add_fire_record(
                    body.get("fabric_id"), body.get("movement_id"),
                    body.get("product_code",""), body.get("color",""),
                    body.get("lot",""), body.get("boyahane",""),
                    body.get("customer",""),
                    body.get("pre_meter",0), body.get("pre_kg",0),
                    body.get("out_meter",0), body.get("out_kg",0),
                    body.get("fire_pct",0),
                    manual_pct=body.get("manual_pct", False),
                    record_type=body.get("record_type","ÇIKIŞ"),
                    user_name=user["full_name"],
                    out_color=body.get("out_color",""),
                    lab_no=body.get("lab_no",""),
                    parti_no=body.get("parti_no","")
                )
                self._send(_ok({"id": rid}))

            # ── Lot sıfırlama / kapanış ──────────────────────────
            elif path == "/api/fire/reset":
                res = db.reset_lot_fire(body.get("fabric_id"), user["full_name"])
                self._send(_ok(res))

            elif path == "/api/fire/finalize":
                done = db.finalize_lot_if_consumed(body.get("fabric_id"), user["full_name"])
                self._send(_ok({"finalized": bool(done)}))

            # ── Lokasyon ekle / senkronize ────────────────────────
            elif path == "/api/locations":
                db.add_location(body.get("name",""), body.get("group_name","DEPO"),
                                body.get("description",""))
                self._send(_ok())

            elif path == "/api/locations/sync":
                db.sync_locations()
                self._send(_ok())

            # ── Müşteri ekle / toplu aktar ────────────────────────
            elif path == "/api/customers":
                cid = db.add_customer(body.get("name",""), body.get("code",""),
                                      body.get("phone",""), body.get("address",""),
                                      body.get("tax_no",""))
                self._send(_ok({"id": cid}))

            elif path == "/api/customers/bulk":
                n = db.import_customers_bulk(body.get("records", []))
                self._send(_ok({"count": n}))

            # ── Tedarikçi ekle / toplu aktar ───────────────────────
            elif path == "/api/suppliers":
                sid = db.add_supplier(body.get("name",""), body.get("code",""),
                                      body.get("phone",""), body.get("address",""),
                                      body.get("tax_no",""))
                self._send(_ok({"id": sid}))

            elif path == "/api/suppliers/bulk":
                n = db.import_suppliers_bulk(body.get("records", []))
                self._send(_ok({"count": n}))

            # ── Ürün ekle / toplu aktar ────────────────────────────
            elif path == "/api/products":
                pid = db.add_product(
                    body.get("product_code",""), body.get("product_name",""),
                    body.get("composition",""),  body.get("width",""),
                    body.get("gramaj",""),        body.get("shrinkage",""),
                    body.get("price",0),          body.get("supplier",""),
                    body.get("reference_code","")
                )
                self._send(_ok({"id": pid}))

            elif path == "/api/products/bulk":
                n = db.import_products_bulk(body.get("records", []))
                self._send(_ok({"count": n}))

            # ── Kullanıcı ekle (admin) ────────────────────────────
            elif path == "/api/users":
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                db.add_user(body["username"], body.get("full_name",""),
                            body["password"], body.get("role","kullanici"))
                self._send(_ok())

            # ── Sipariş ekle ───────────────────────────────────────
            elif path == "/api/orders":
                oid, order_no = db.add_order(
                    body.get("customer_id"), body.get("customer_name",""), body.get("customer_ref",""),
                    body.get("currency","USD"), body.get("payment_method",""), body.get("delivery_terms",""),
                    body.get("delivery_address",""), body.get("delivery_date",""),
                    body.get("order_date",""), body.get("notes",""),
                    body.get("items",[]),
                    created_by=body.get("created_by") or user["full_name"]
                )
                self._send(_ok({"id": oid, "order_no": order_no}))

            else:
                self._send(_err("Endpoint bulunamadı"), 404)

        except Exception as e:
            self._send(_err(str(e)), 500)

    def do_PUT(self):
        path = urlparse(self.path).path.rstrip("/")
        user = _auth(self.headers)
        if not user:
            return self._send(_err("Yetkisiz erişim"), 401)
        try:
            body = self._body()
            if path.startswith("/api/fabrics/"):
                fid = int(path.split("/")[-1])
                db.update_fabric(fid,
                    body.get("product_name",""), body.get("product_code",""),
                    body.get("color",""),        body.get("location",""),
                    body.get("meter",0),         body.get("kg",0),
                    body.get("piece_count",""),  body.get("birim_fiyat",0),
                    body.get("fabric_type",""),  body.get("lot",""),
                    body.get("description",""),
                    entry_location=body.get("entry_location"),
                    lab_no=body.get("lab_no"),
                    print_type=body.get("print_type"),
                    zemin_rengi=body.get("zemin_rengi"),
                    baski_desen_no=body.get("baski_desen_no")
                )
                self._send(_ok())
            elif path.startswith("/api/customers/"):
                cid = int(path.split("/")[-1])
                db.update_customer(cid, body.get("name",""), body.get("code",""),
                                   body.get("phone",""), body.get("address",""),
                                   body.get("tax_no",""), body.get("active",1))
                self._send(_ok())
            elif path.startswith("/api/suppliers/"):
                sid = int(path.split("/")[-1])
                db.update_supplier(sid, body.get("name",""), body.get("code",""),
                                   body.get("phone",""), body.get("address",""),
                                   body.get("tax_no",""), body.get("active",1))
                self._send(_ok())
            elif path.startswith("/api/products/"):
                pid = int(path.split("/")[-1])
                db.update_product(pid,
                    body.get("product_code",""), body.get("product_name",""),
                    body.get("composition",""),  body.get("width",""),
                    body.get("gramaj",""),        body.get("shrinkage",""),
                    body.get("price",0),          body.get("supplier",""),
                    body.get("active",1),         body.get("reference_code","")
                )
                self._send(_ok())
            elif path.startswith("/api/locations/"):
                lid = int(path.split("/")[-1])
                db.update_location(lid, body.get("name",""), body.get("group_name","DEPO"),
                                   body.get("description",""), body.get("active",1))
                self._send(_ok())
            elif path.startswith("/api/users/") and path.endswith("/password"):
                uid = int(path.split("/")[-2])
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                db.update_user_password(uid, body["password"])
                self._send(_ok())
            elif path.startswith("/api/users/") and path.endswith("/toggle"):
                uid = int(path.split("/")[-2])
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                db.toggle_user_active(uid)
                self._send(_ok())
            elif path.startswith("/api/orders/"):
                oid = int(path.split("/")[-1])
                db.update_order(oid,
                    body.get("customer_id"), body.get("customer_name",""), body.get("customer_ref",""),
                    body.get("currency","USD"), body.get("payment_method",""), body.get("delivery_terms",""),
                    body.get("delivery_address",""), body.get("delivery_date",""),
                    body.get("order_date",""), body.get("notes",""),
                    body.get("items",[])
                )
                self._send(_ok())
            elif path == "/api/settings/company":
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                db.save_company_settings(**body)
                self._send(_ok())
            else:
                self._send(_err("Endpoint bulunamadı"), 404)
        except Exception as e:
            self._send(_err(str(e)), 500)

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/")
        user = _auth(self.headers)
        if not user:
            return self._send(_err("Yetkisiz erişim"), 401)
        try:
            if path.startswith("/api/fabrics/"):
                fid = int(path.split("/")[-1])
                db.soft_delete_fabric(fid, user["full_name"])
                self._send(_ok())
            elif path.startswith("/api/customers/"):
                cid = int(path.split("/")[-1])
                db.delete_customer(cid)
                self._send(_ok())
            elif path.startswith("/api/suppliers/"):
                sid = int(path.split("/")[-1])
                db.delete_supplier(sid)
                self._send(_ok())
            elif path.startswith("/api/products/"):
                pid = int(path.split("/")[-1])
                db.delete_product(pid)
                self._send(_ok())
            elif path.startswith("/api/orders/"):
                oid = int(path.split("/")[-1])
                db.delete_order(oid)
                self._send(_ok())
            elif path.startswith("/api/locations/"):
                lid = int(path.split("/")[-1])
                db.delete_location(lid)
                self._send(_ok())
            elif path.startswith("/api/users/"):
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                uid = int(path.split("/")[-1])
                if uid == user.get("id"):
                    return self._send(_err("Kendi hesabınızı silemezsiniz"), 400)
                db.delete_user(uid)
                self._send(_ok())
            else:
                self._send(_err("Endpoint bulunamadı"), 404)
        except Exception as e:
            self._send(_err(str(e)), 500)


def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:    s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except: return "127.0.0.1"
    finally: s.close()


def start_server():
    db.init_db()
    ip = get_local_ip()
    # Threading: yavaş bir istemci diğerlerini bekletmesin
    server = ThreadingHTTPServer(("0.0.0.0", PORT), APIHandler)
    print(f"""
╔══════════════════════════════════════════════════╗
║   Bursa Knitted Depo — API Sunucusu Başladı      ║
╠══════════════════════════════════════════════════╣
║  Yerel adres : http://localhost:{PORT}              ║
║  Ağ adresi  : http://{ip}:{PORT}         ║
║                                                  ║
║  Diğer bilgisayarlarda program ilk açılırken:    ║
║  Sunucu adresi: http://{ip}:{PORT}       ║
║                                                  ║
║  Durdurmak için: Ctrl+C                          ║
╚══════════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu durduruldu.")


if __name__ == "__main__":
    start_server()
