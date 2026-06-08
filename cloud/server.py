"""
Bursa Knitted Depo — Bulut API Sunucusu
Render.com'da çalışır, PostgreSQL kullanır.
"""
import sys, os, json, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db   # cloud/db.py — SQLite veya PostgreSQL

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT     = int(os.environ.get("PORT", 5060))
_tokens  = {}   # {token: user_dict}


def _ok(data=None): return json.dumps({"ok": True,  "data": data}, ensure_ascii=False)
def _err(msg):      return json.dumps({"ok": False, "error": msg},  ensure_ascii=False)

def _auth(headers):
    return _tokens.get(headers.get("X-Token",""))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, f, *a): pass

    def _send(self, body, code=200):
        if isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type",  "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,X-Token")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length",0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,X-Token")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        qs     = parse_qs(parsed.query)

        if path == "/ping":
            return self._send(_ok("pong"))

        # Health check for Render
        if path == "/health":
            return self._send(_ok({"status": "ok"}))

        user = _auth(self.headers)
        if not user:
            return self._send(_err("Yetkisiz erişim"), 401)

        try:
            if path == "/api/fabrics":
                rows = db.get_all_fabrics(
                    search      = qs.get("search",[""])[0],
                    location    = qs.get("location",[""])[0],
                    fabric_type = qs.get("fabric_type",[""])[0],
                )
                self._send(_ok(rows))

            elif path.startswith("/api/fabrics/"):
                fid = int(path.split("/")[-1])
                self._send(_ok(db.get_fabric(fid)))

            elif path == "/api/movements":
                fid = qs.get("fabric_id",[""])[0]
                if fid:
                    self._send(_ok(db.get_movements(int(fid))))
                else:
                    self._send(_ok(db.get_all_movements(int(qs.get("limit",["300"])[0]))))

            elif path == "/api/locations":
                self._send(_ok(db.get_active_locations()))

            elif path == "/api/summary":
                self._send(_ok(db.get_summary()))

            elif path == "/api/users":
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                self._send(_ok(db.get_all_users()))

            else:
                self._send(_err("Bulunamadı"), 404)

        except Exception as e:
            self._send(_err(str(e)), 500)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        qs   = parse_qs(urlparse(self.path).query)

        if path == "/api/login":
            body = self._body()
            u = db.authenticate(body.get("username",""), body.get("password",""))
            if u:
                token = str(uuid.uuid4())
                _tokens[token] = u
                data = dict(u); data["token"] = token
                return self._send(_ok(data))
            return self._send(_err("Kullanıcı adı veya şifre hatalı"), 401)

        user = _auth(self.headers)
        if not user:
            return self._send(_err("Yetkisiz erişim"), 401)

        try:
            body = self._body()

            if path == "/api/fabrics":
                fid = db.add_fabric(
                    body.get("product_name",""), body.get("product_code",""),
                    body.get("color",""),         body.get("location",""),
                    body.get("meter",0),          body.get("kg",0),
                    body.get("piece_count",""),   body.get("birim_fiyat",0),
                    body.get("fabric_type",""),   body.get("lot",""),
                    body.get("description",""),   user_name=user["full_name"]
                )
                self._send(_ok({"id": fid}))

            elif path == "/api/movements":
                mid = db.add_movement(
                    body.get("fabric_id"), body.get("movement_type","GİRİŞ"),
                    body.get("meter",0),   body.get("kg",0),
                    body.get("piece_count",""), body.get("notes",""),
                    user_name=user["full_name"]
                )
                self._send(_ok({"id": mid}))

            elif path == "/api/users":
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                db.add_user(body["username"], body.get("full_name",""),
                            body["password"], body.get("role","kullanici"))
                self._send(_ok())

            else:
                self._send(_err("Bulunamadı"), 404)

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
                    body.get("color",""),         body.get("location",""),
                    body.get("meter",0),          body.get("kg",0),
                    body.get("piece_count",""),   body.get("birim_fiyat",0),
                    body.get("fabric_type",""),   body.get("lot",""),
                    body.get("description","")
                )
                self._send(_ok())
            elif "/password" in path:
                uid = int(path.split("/")[-2])
                if user.get("role") != "admin":
                    return self._send(_err("Yetki yok"), 403)
                db.update_user_password(uid, body["password"])
                self._send(_ok())
            else:
                self._send(_err("Bulunamadı"), 404)
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
                self._send(_err("Bulunamadı"), 404)
        except Exception as e:
            self._send(_err(str(e)), 500)


def run():
    db.init_db()
    print(f"Bulut API sunucusu port {PORT}'de başladı")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    run()
