"""
Veritabanı katmanı — SQLite (local) veya PostgreSQL (cloud) destekler.
DATABASE_URL env değişkeni varsa PostgreSQL, yoksa SQLite kullanır.
"""
import os, hashlib

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# ── Bağlantı ────────────────────────────────────────────────────

def get_conn():
    if DATABASE_URL:
        import psycopg2, psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        conn.autocommit = False
        return conn, "pg"
    else:
        import sqlite3
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stok.db")
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

# SQL uyumluluk: PostgreSQL ? yerine %s kullanır
def _q(sql):
    if DATABASE_URL:
        return sql.replace("?", "%s")
    return sql

def _now():
    return "NOW()" if DATABASE_URL else "datetime('now','localtime')"

def _rows_to_dicts(rows, cursor):
    """psycopg2 sonuçlarını dict listesine çevir."""
    if not rows: return []
    if DATABASE_URL:
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, r)) for r in rows]
    return [dict(r) for r in rows]  # sqlite3.Row zaten dict-like


# ── Init ─────────────────────────────────────────────────────────

def init_db():
    conn, mode = get_conn()
    c = conn.cursor()

    if mode == "pg":
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT DEFAULT '',
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'kullanici',
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW()
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS fabrics (
                id SERIAL PRIMARY KEY,
                product_name TEXT DEFAULT '',
                product_code TEXT NOT NULL,
                color TEXT DEFAULT '',
                location TEXT DEFAULT '',
                meter REAL DEFAULT 0,
                kg REAL DEFAULT 0,
                piece_count TEXT DEFAULT '',
                birim_fiyat REAL DEFAULT 0,
                fabric_type TEXT DEFAULT '',
                lot TEXT DEFAULT '',
                description TEXT DEFAULT '',
                deleted_at TIMESTAMP DEFAULT NULL,
                deleted_by TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS movements (
                id SERIAL PRIMARY KEY,
                fabric_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                meter REAL DEFAULT 0,
                kg REAL DEFAULT 0,
                piece_count TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                user_name TEXT DEFAULT '',
                movement_date TIMESTAMP DEFAULT NOW()
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                group_name TEXT DEFAULT 'DEPO',
                description TEXT DEFAULT '',
                active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0
            )""")
    else:
        # SQLite — mevcut database.py ile uyumlu, burası sadece cloud için
        pass

    conn.commit()

    # Admin kullanıcı oluştur
    c.execute(_q("SELECT id FROM users WHERE username=?"), ("admin",))
    if not c.fetchone():
        c.execute(_q("INSERT INTO users (username, full_name, password_hash, role) VALUES (?,?,?,?)"),
                  ("admin", "Yönetici", _hash("admin123"), "admin"))
        conn.commit()
    conn.close()


def _hash(p): return hashlib.sha256(p.encode()).hexdigest()


# ── Users ────────────────────────────────────────────────────────

def authenticate(username, password):
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute(_q("SELECT * FROM users WHERE username=%s AND active=1" if mode=="pg" else
                 "SELECT * FROM users WHERE username=? AND active=1"), (username,))
    row = c.fetchone()
    conn.close()
    if row:
        d = dict(row) if mode=="pg" else dict(row)
        if d["password_hash"] == _hash(password):
            return d
    return None

def get_all_users():
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY full_name")
    rows = _rows_to_dicts(c.fetchall(), c)
    conn.close()
    return rows

def add_user(username, full_name, password, role="kullanici"):
    conn, _ = get_conn()
    conn.cursor().execute(
        _q("INSERT INTO users (username,full_name,password_hash,role) VALUES (?,?,?,?)"),
        (username, full_name, _hash(password), role))
    conn.commit(); conn.close()

def update_user_password(uid, pw):
    conn, _ = get_conn()
    conn.cursor().execute(_q("UPDATE users SET password_hash=? WHERE id=?"), (_hash(pw), uid))
    conn.commit(); conn.close()

def toggle_user_active(uid):
    conn, _ = get_conn()
    conn.cursor().execute(_q("UPDATE users SET active=1-active WHERE id=?"), (uid,))
    conn.commit(); conn.close()

def delete_user(uid):
    conn, _ = get_conn()
    conn.cursor().execute(_q("DELETE FROM users WHERE id=?"), (uid,))
    conn.commit(); conn.close()


# ── Locations ────────────────────────────────────────────────────

def get_active_locations():
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM locations WHERE active=1 ORDER BY group_name, sort_order, name")
    rows = _rows_to_dicts(c.fetchall(), c)
    conn.close()
    return rows

def add_location(name, group_name="DEPO", description=""):
    conn, _ = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(MAX(sort_order),0) FROM locations")
    mx = c.fetchone()[0]
    c.execute(_q("INSERT INTO locations (name,group_name,description,sort_order) VALUES (?,?,?,?)"),
              (name.upper(), group_name, description, mx+1))
    conn.commit(); conn.close()


# ── Fabrics ──────────────────────────────────────────────────────

def get_all_fabrics(search="", location="", fabric_type="", include_deleted=False):
    conn, mode = get_conn()
    c = conn.cursor()
    sql = "SELECT * FROM fabrics WHERE 1=1"
    params = []
    if not include_deleted:
        sql += " AND deleted_at IS NULL"
    if search:
        if mode == "pg":
            sql += " AND (product_name ILIKE %s OR product_code ILIKE %s OR color ILIKE %s OR description ILIKE %s)"
        else:
            sql += " AND (product_name LIKE ? OR product_code LIKE ? OR color LIKE ? OR description LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    if location:
        sql += _q(" AND location=?"); params.append(location)
    if fabric_type:
        sql += _q(" AND fabric_type=?"); params.append(fabric_type)
    sql += " ORDER BY location, product_code, color"
    c.execute(_q(sql) if mode=="sqlite" else sql, params)
    rows = _rows_to_dicts(c.fetchall(), c)
    conn.close()
    return rows

def get_fabric(fid):
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute(_q("SELECT * FROM fabrics WHERE id=?"), (fid,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def add_fabric(product_name, product_code, color, location, meter, kg,
               piece_count, birim_fiyat, fabric_type, lot, description, user_name=""):
    conn, mode = get_conn()
    c = conn.cursor()
    if mode == "pg":
        c.execute("""INSERT INTO fabrics (product_name,product_code,color,location,meter,kg,
                     piece_count,birim_fiyat,fabric_type,lot,description)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                  (product_name,product_code,color,location,meter or 0,kg or 0,
                   piece_count,birim_fiyat or 0,fabric_type,lot,description))
        fid = c.fetchone()[0]
    else:
        c.execute("""INSERT INTO fabrics (product_name,product_code,color,location,meter,kg,
                     piece_count,birim_fiyat,fabric_type,lot,description)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (product_name,product_code,color,location,meter or 0,kg or 0,
                   piece_count,birim_fiyat or 0,fabric_type,lot,description))
        fid = c.lastrowid
    if meter or kg:
        c.execute(_q("INSERT INTO movements (fabric_id,movement_type,meter,kg,piece_count,notes,user_name) VALUES (?,?,?,?,?,?,?)"),
                  (fid,"GİRİŞ",meter or 0,kg or 0,piece_count,"İlk stok girişi",user_name))
    conn.commit(); conn.close()
    return fid

def update_fabric(fid, product_name, product_code, color, location, meter, kg,
                  piece_count, birim_fiyat, fabric_type, lot, description):
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute(_q("""UPDATE fabrics SET product_name=?,product_code=?,color=?,location=?,
               meter=?,kg=?,piece_count=?,birim_fiyat=?,fabric_type=?,lot=?,description=?,
               updated_at=""" + _now() + " WHERE id=?"),
              (product_name,product_code,color,location,meter or 0,kg or 0,
               piece_count,birim_fiyat or 0,fabric_type,lot,description,fid))
    conn.commit(); conn.close()

def soft_delete_fabric(fid, user_name=""):
    conn, mode = get_conn()
    c = conn.cursor()
    f = get_fabric(fid)
    if f:
        c.execute(_q("UPDATE fabrics SET deleted_at=" + _now() + ",deleted_by=?,updated_at=" + _now() + " WHERE id=?"),
                  (user_name, fid))
        c.execute(_q("INSERT INTO movements (fabric_id,movement_type,meter,kg,piece_count,notes,user_name) VALUES (?,?,?,?,?,?,?)"),
                  (fid,"SİLME",f["meter"] or 0,f["kg"] or 0,f.get("piece_count",""),"Stoktan silindi",user_name))
    conn.commit(); conn.close()


# ── Movements ────────────────────────────────────────────────────

def add_movement(fid, movement_type, meter, kg, piece_count, notes, user_name=""):
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute(_q("INSERT INTO movements (fabric_id,movement_type,meter,kg,piece_count,notes,user_name) VALUES (?,?,?,?,?,?,?)"),
              (fid,movement_type,meter or 0,kg or 0,piece_count,notes,user_name))
    f = get_fabric(fid)
    if f:
        if movement_type == "GİRİŞ":
            nm = (f["meter"] or 0)+(meter or 0); nk = (f["kg"] or 0)+(kg or 0)
        else:
            nm = max(0,(f["meter"] or 0)-(meter or 0)); nk = max(0,(f["kg"] or 0)-(kg or 0))
        c.execute(_q("UPDATE fabrics SET meter=?,kg=?,updated_at=" + _now() + " WHERE id=?"), (nm,nk,fid))
    conn.commit(); conn.close()

def get_movements(fid):
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute(_q("SELECT * FROM movements WHERE fabric_id=? ORDER BY movement_date DESC"), (fid,))
    rows = _rows_to_dicts(c.fetchall(), c)
    conn.close()
    return rows

def get_all_movements(limit=300):
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute(_q("""SELECT m.*,f.product_code,f.product_name,f.color,f.location
                    FROM movements m LEFT JOIN fabrics f ON m.fabric_id=f.id
                    ORDER BY m.movement_date DESC LIMIT ?"""), (limit,))
    rows = _rows_to_dicts(c.fetchall(), c)
    conn.close()
    return rows

def get_summary():
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) as total_items,
                        SUM(meter) as total_meter,
                        SUM(kg) as total_kg,
                        SUM(CASE WHEN birim_fiyat>0 AND meter>0 THEN meter*birim_fiyat
                                 WHEN birim_fiyat>0 AND kg>0    THEN kg*birim_fiyat
                                 ELSE 0 END) as total_value,
                        COUNT(CASE WHEN birim_fiyat>0 THEN 1 END) as priced_items
                 FROM fabrics WHERE deleted_at IS NULL""")
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {}

def get_locations():
    conn, mode = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT location FROM fabrics WHERE location!='' AND deleted_at IS NULL ORDER BY location")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]
