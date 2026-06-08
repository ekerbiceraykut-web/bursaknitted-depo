"""
Bursa Knitted Depo — API Sunucusu
Ana Mac'te çalışır, diğer bilgisayarlar buraya bağlanır.
Port: 5060

Başlatmak için: python3 server.py
"""
import sys, os, json, hashlib, uuid, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote_plus
import database as db

PORT = 5060
_tokens: dict = {}  # {token: user_dict}


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

            # ── Locations ────────────────────────────────────────
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
            body = self._body()
            u = db.authenticate(body.get("username",""), body.get("password",""))
            if u:
                token = str(uuid.uuid4())
                _tokens[token] = dict(u)
                data = dict(u); data["token"] = token
                return self._send(_ok(data))
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
                    body.get("description",""),  user_name=user["full_name"]
                )
                self._send(_ok({"id": fid}))

            # ── Hareket ekle ─────────────────────────────────────
            elif path == "/api/movements":
                fid = body.get("fabric_id")
                mid = db.add_movement(
                    fid, body.get("movement_type","GİRİŞ"),
                    body.get("meter",0), body.get("kg",0),
                    body.get("piece_count",""), body.get("notes",""),
                    user_name=user["full_name"]
                )
                self._send(_ok({"id": mid}))

            # ── Kullanıcı ekle (admin) ────────────────────────────
            elif path == "/api/users":
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                db.add_user(body["username"], body.get("full_name",""),
                            body["password"], body.get("role","kullanici"))
                self._send(_ok())

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
                    body.get("description","")
                )
                self._send(_ok())
            elif path.startswith("/api/users/") and path.endswith("/password"):
                uid = int(path.split("/")[-2])
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                db.update_user_password(uid, body["password"])
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
    server = HTTPServer(("0.0.0.0", PORT), APIHandler)
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
