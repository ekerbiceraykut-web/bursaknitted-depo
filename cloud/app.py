"""
Bursa Knitted Depo — Bulut Web Uygulaması
Render.com veya Railway'de çalışır.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db   # cloud/db.py

# web_server.py'den tüm sayfa fonksiyonlarını al ama db'yi bizimkiyle değiştir
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import web_server
# web_server'daki 'db' modülünü cloud db ile değiştir
web_server.db = db

from flask import Flask, request, make_response, redirect

application = Flask(__name__)
application.secret_key = os.environ.get("SECRET_KEY", "bursa-knitted-2026")

@application.before_first_request
def _init():
    db.init_db()

# web_server'daki Handler'ı Flask route'larına sarmalıyoruz
import uuid

_sessions = web_server._sessions  # aynı oturum sözlüğünü kullan

def _get_user():
    token = request.cookies.get("bk_token", "")
    return _sessions.get(token)

def _render(html, cookie=None):
    resp = make_response(html)
    if cookie:
        name, val = cookie
        if val:
            resp.set_cookie(name, val, httponly=True, path="/")
        else:
            resp.delete_cookie(name)
    return resp

# Tüm route'ları tek handler'a yönlendir
@application.route("/", defaults={"path": ""}, methods=["GET","POST"])
@application.route("/<path:path>", methods=["GET","POST"])
def catch_all(path):
    full_path = "/" + path
    if request.query_string:
        full_path += "?" + request.query_string.decode()

    user = _get_user()

    # Giriş gerektiren sayfalar
    if path not in ("login", "favicon.ico") and not user:
        return redirect("/login")

    from urllib.parse import urlparse, parse_qs, unquote_plus
    parsed = urlparse("/" + path)
    qs     = parse_qs(request.query_string.decode())

    if request.method == "POST":
        post_data = {k: unquote_plus(v) for k, v in request.form.items()}

    try:
        if request.method == "GET":
            if path in ("", "dashboard"):
                return web_server._dashboard(user)
            elif path == "stok":
                return web_server._stok_page(user,
                    search  =qs.get("q",[""])[0],
                    location=qs.get("loc",[""])[0],
                    ftype   =qs.get("tip",[""])[0])
            elif path == "detay":
                return web_server._detay_page(user, int(qs.get("id",[0])[0]))
            elif path == "hareket":
                return web_server._hareket_page(user)
            elif path == "giris":
                return web_server._movement_form(user, int(qs.get("id",[0])[0]), "GİRİŞ")
            elif path == "cikis":
                return web_server._movement_form(user, int(qs.get("id",[0])[0]), "ÇIKIŞ")
            elif path == "yeni":
                return web_server._fabric_form(user)
            elif path == "duzenle":
                return web_server._fabric_form(user, db.get_fabric(int(qs.get("id",[0])[0])))
            elif path == "sil":
                db.soft_delete_fabric(int(qs.get("id",[0])[0]), user["full_name"])
                return redirect("/stok")
            elif path == "logout":
                token = request.cookies.get("bk_token","")
                _sessions.pop(token, None)
                resp = redirect("/login")
                resp.delete_cookie("bk_token")
                return resp
            elif path == "login":
                return web_server._login_page()
            else:
                return redirect("/")

        else:  # POST
            if path == "login":
                u = db.authenticate(post_data.get("username",""), post_data.get("password",""))
                if u:
                    token = str(uuid.uuid4())
                    _sessions[token] = dict(u)
                    resp = redirect("/")
                    resp.set_cookie("bk_token", token, httponly=True, path="/")
                    return resp
                return web_server._login_page("Kullanıcı adı veya şifre hatalı!")

            elif path == "giris":
                fid   = int(qs.get("id",[0])[0])
                meter = float(post_data.get("meter") or 0)
                kg    = float(post_data.get("kg")    or 0)
                if meter <= 0 and kg <= 0:
                    return web_server._movement_form(user, fid, "GİRİŞ", "Metre veya kilo giriniz!", post_data)
                db.add_movement(fid,"GİRİŞ",meter,kg,post_data.get("piece_count",""),post_data.get("notes",""),user["full_name"])
                return redirect(f"/detay?id={fid}")

            elif path == "cikis":
                fid   = int(qs.get("id",[0])[0])
                meter = float(post_data.get("meter") or 0)
                kg    = float(post_data.get("kg")    or 0)
                if meter <= 0 and kg <= 0:
                    return web_server._movement_form(user, fid, "ÇIKIŞ", "Metre veya kilo giriniz!", post_data)
                db.add_movement(fid,"ÇIKIŞ",meter,kg,post_data.get("piece_count",""),post_data.get("notes",""),user["full_name"])
                return redirect(f"/detay?id={fid}")

            elif path == "yeni":
                errors = []
                if not post_data.get("product_code","").strip(): errors.append("Ürün kodu zorunlu")
                if not post_data.get("location","").strip():     errors.append("Lokasyon zorunlu")
                if not post_data.get("fabric_type","").strip():  errors.append("Kumaş tipi zorunlu")
                if float(post_data.get("birim_fiyat") or 0) <= 0: errors.append("Birim fiyat zorunlu")
                if errors: return web_server._fabric_form(user, error=", ".join(errors), post_data=post_data)
                db.add_fabric(
                    post_data.get("product_name",""), post_data.get("product_code","").upper(),
                    post_data.get("color","").upper(), post_data.get("location",""),
                    float(post_data.get("meter") or 0), float(post_data.get("kg") or 0),
                    post_data.get("piece_count",""), float(post_data.get("birim_fiyat") or 0),
                    post_data.get("fabric_type",""), post_data.get("lot",""), post_data.get("description",""),
                    user_name=user["full_name"])
                return redirect("/stok")

            elif path == "duzenle":
                fid = int(qs.get("id",[0])[0])
                db.update_fabric(fid,
                    post_data.get("product_name",""), post_data.get("product_code","").upper(),
                    post_data.get("color","").upper(), post_data.get("location",""),
                    float(post_data.get("meter") or 0), float(post_data.get("kg") or 0),
                    post_data.get("piece_count",""), float(post_data.get("birim_fiyat") or 0),
                    post_data.get("fabric_type",""), post_data.get("lot",""), post_data.get("description",""))
                return redirect(f"/detay?id={fid}")

        return redirect("/")

    except Exception as e:
        import traceback; traceback.print_exc()
        return f"<h3>Hata: {e}</h3><a href='/'>Ana Sayfa</a>"


if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 5055))
    application.run(host="0.0.0.0", port=port, debug=False)
