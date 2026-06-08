import sqlite3
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stok.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'kullanici',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS fabrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            deleted_at TEXT DEFAULT NULL,
            deleted_by TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fabric_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            meter REAL DEFAULT 0,
            kg REAL DEFAULT 0,
            piece_count TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            user_name TEXT DEFAULT '',
            movement_date TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (fabric_id) REFERENCES fabrics(id)
        );

        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            group_name TEXT DEFAULT 'DEPO',
            description TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_fabrics_code ON fabrics(product_code);
        CREATE INDEX IF NOT EXISTS idx_fabrics_location ON fabrics(location);
        CREATE INDEX IF NOT EXISTS idx_movements_fabric ON movements(fabric_id);
    """)

    # Migrations — mevcut DB'ye yeni sütunlar
    migrations = [
        "ALTER TABLE fabrics ADD COLUMN birim_fiyat REAL DEFAULT 0",
        "ALTER TABLE fabrics ADD COLUMN fabric_type TEXT DEFAULT ''",
        "ALTER TABLE fabrics ADD COLUMN lot TEXT DEFAULT ''",
        "ALTER TABLE fabrics ADD COLUMN deleted_at TEXT DEFAULT NULL",
        "ALTER TABLE fabrics ADD COLUMN deleted_by TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN user_name TEXT DEFAULT ''",
    ]
    for sql in migrations:
        try:
            c.execute(sql)
        except Exception:
            pass

    conn.commit()

    # Mevcut fabric lokasyonlarından locations tablosunu otomatik doldur
    _sync_locations_from_fabrics(conn)

    # Varsayılan admin kullanıcı
    existing = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        c.execute("""
            INSERT INTO users (username, full_name, password_hash, role)
            VALUES ('admin', 'Yönetici', ?, 'admin')
        """, (_hash("admin123"),))
        conn.commit()

    conn.close()


# ── Locations ───────────────────────────────────────────────────

DEPO_PATTERN_NAMES = {"DEPO", "M11", "M7", "OFİS", "OFIS"}

def _is_depo_loc(name):
    import re
    u = name.strip().upper()
    return u in DEPO_PATTERN_NAMES or bool(re.match(r"^(RAF|PALET|P\d|H\d|HP|H-P)", u))

def _sync_locations_from_fabrics(conn):
    """Fabric tablosundaki lokasyonları locations tablosuna ekle (eksik olanları)."""
    existing = {r[0] for r in conn.execute("SELECT name FROM locations").fetchall()}
    fabric_locs = conn.execute(
        "SELECT DISTINCT location FROM fabrics WHERE location != '' AND deleted_at IS NULL"
    ).fetchall()
    i = len(existing)
    for row in fabric_locs:
        name = row[0].strip()
        if name and name not in existing:
            grp = "DEPO" if _is_depo_loc(name) else "DIŞ DEPO"
            conn.execute(
                "INSERT OR IGNORE INTO locations (name, group_name, sort_order) VALUES (?,?,?)",
                (name, grp, i)
            )
            i += 1
    conn.commit()

def get_all_locations():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM locations ORDER BY group_name, sort_order, name"
    ).fetchall()
    conn.close()
    return rows

def get_active_locations():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM locations WHERE active=1 ORDER BY group_name, sort_order, name"
    ).fetchall()
    conn.close()
    return rows

def add_location(name, group_name="DEPO", description=""):
    conn = get_connection()
    max_order = conn.execute("SELECT COALESCE(MAX(sort_order),0) FROM locations").fetchone()[0]
    conn.execute(
        "INSERT INTO locations (name, group_name, description, sort_order) VALUES (?,?,?,?)",
        (name.strip().upper(), group_name, description, max_order + 1)
    )
    conn.commit()
    conn.close()

def update_location(loc_id, name, group_name, description, active):
    conn = get_connection()
    conn.execute(
        "UPDATE locations SET name=?, group_name=?, description=?, active=? WHERE id=?",
        (name.strip().upper(), group_name, description, int(active), loc_id)
    )
    conn.commit()
    conn.close()

def delete_location(loc_id):
    conn = get_connection()
    conn.execute("DELETE FROM locations WHERE id=?", (loc_id,))
    conn.commit()
    conn.close()

def sync_locations():
    """Yeni eklenen fabric lokasyonlarını senkronize et."""
    conn = get_connection()
    _sync_locations_from_fabrics(conn)
    conn.close()


# ── Users ──────────────────────────────────────────────────────

def authenticate(username, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND active=1",
        (username,)
    ).fetchone()
    conn.close()
    if row and row["password_hash"] == _hash(password):
        return dict(row)
    return None


def get_all_users():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY full_name").fetchall()
    conn.close()
    return rows


def add_user(username, full_name, password, role="kullanici"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (username, full_name, password_hash, role) VALUES (?,?,?,?)",
        (username.strip(), full_name.strip(), _hash(password), role)
    )
    conn.commit()
    conn.close()


def update_user_password(user_id, new_password):
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (_hash(new_password), user_id))
    conn.commit()
    conn.close()


def toggle_user_active(user_id):
    conn = get_connection()
    conn.execute("UPDATE users SET active = 1 - active WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


# ── Fabrics ─────────────────────────────────────────────────────

def get_all_fabrics(search="", location="", fabric_type="", include_deleted=False):
    conn = get_connection()
    query = "SELECT * FROM fabrics WHERE 1=1"
    params = []
    if not include_deleted:
        query += " AND deleted_at IS NULL"
    if search:
        query += " AND (product_name LIKE ? OR product_code LIKE ? OR color LIKE ? OR description LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    if location:
        query += " AND location = ?"
        params.append(location)
    if fabric_type:
        query += " AND fabric_type = ?"
        params.append(fabric_type)
    query += " ORDER BY location, product_code, color"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_fabric(fabric_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM fabrics WHERE id=?", (fabric_id,)).fetchone()
    conn.close()
    return row


def add_fabric(product_name, product_code, color, location, meter, kg,
               piece_count, birim_fiyat, fabric_type, lot, description, user_name=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO fabrics (product_name, product_code, color, location,
                             meter, kg, piece_count, birim_fiyat, fabric_type, lot, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (product_name, product_code, color, location,
          meter or 0, kg or 0, piece_count, birim_fiyat or 0, fabric_type, lot, description))
    fabric_id = c.lastrowid
    if meter or kg:
        c.execute("""
            INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count, notes, user_name)
            VALUES (?, 'GİRİŞ', ?, ?, ?, 'İlk stok girişi', ?)
        """, (fabric_id, meter or 0, kg or 0, piece_count, user_name))
    conn.commit()
    conn.close()
    return fabric_id


def update_fabric(fabric_id, product_name, product_code, color, location,
                  meter, kg, piece_count, birim_fiyat, fabric_type, lot, description):
    conn = get_connection()
    conn.execute("""
        UPDATE fabrics SET product_name=?, product_code=?, color=?, location=?,
        meter=?, kg=?, piece_count=?, birim_fiyat=?, fabric_type=?, lot=?, description=?,
        updated_at=datetime('now','localtime')
        WHERE id=?
    """, (product_name, product_code, color, location,
          meter or 0, kg or 0, piece_count, birim_fiyat or 0, fabric_type, lot, description, fabric_id))
    conn.commit()
    conn.close()


def restore_fabric(fabric_id):
    """Soft-delete'i geri al."""
    conn = get_connection()
    conn.execute("""
        UPDATE fabrics SET deleted_at=NULL, deleted_by='', updated_at=datetime('now','localtime')
        WHERE id=?
    """, (fabric_id,))
    conn.execute("DELETE FROM movements WHERE fabric_id=? AND movement_type='SİLME'", (fabric_id,))
    conn.commit()
    conn.close()


def reverse_movement(movement_id):
    """Son hareketi geri al: GİRİŞ → ÇIKIŞ kadar düş, ÇIKIŞ → GİRİŞ kadar ekle."""
    conn = get_connection()
    m = conn.execute("SELECT * FROM movements WHERE id=?", (movement_id,)).fetchone()
    if not m:
        conn.close()
        return
    fabric = conn.execute("SELECT meter, kg FROM fabrics WHERE id=?", (m["fabric_id"],)).fetchone()
    if fabric:
        if m["movement_type"] == "GİRİŞ":
            new_meter = max(0, (fabric["meter"] or 0) - (m["meter"] or 0))
            new_kg    = max(0, (fabric["kg"] or 0) - (m["kg"] or 0))
        else:
            new_meter = (fabric["meter"] or 0) + (m["meter"] or 0)
            new_kg    = (fabric["kg"] or 0) + (m["kg"] or 0)
        conn.execute("UPDATE fabrics SET meter=?, kg=?, updated_at=datetime('now','localtime') WHERE id=?",
                     (new_meter, new_kg, m["fabric_id"]))
    conn.execute("DELETE FROM movements WHERE id=?", (movement_id,))
    conn.commit()
    conn.close()


def soft_delete_fabric(fabric_id, user_name=""):
    """Stoktan siler ama tüm hareket geçmişi korunur."""
    conn = get_connection()
    fabric = conn.execute("SELECT * FROM fabrics WHERE id=?", (fabric_id,)).fetchone()
    if fabric:
        conn.execute("""
            UPDATE fabrics SET deleted_at=datetime('now','localtime'), deleted_by=?,
            updated_at=datetime('now','localtime') WHERE id=?
        """, (user_name, fabric_id))
        # Silme hareketi kaydet
        conn.execute("""
            INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count, notes, user_name)
            VALUES (?, 'SİLME', ?, ?, ?, 'Stoktan silindi', ?)
        """, (fabric_id, fabric["meter"] or 0, fabric["kg"] or 0,
              fabric["piece_count"] or "", user_name))
    conn.commit()
    conn.close()


# ── Movements ───────────────────────────────────────────────────

def add_movement(fabric_id, movement_type, meter, kg, piece_count, notes, user_name=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count, notes, user_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (fabric_id, movement_type, meter or 0, kg or 0, piece_count, notes, user_name))
    fabric = conn.execute("SELECT meter, kg FROM fabrics WHERE id=?", (fabric_id,)).fetchone()
    if fabric:
        if movement_type == "GİRİŞ":
            new_meter = (fabric["meter"] or 0) + (meter or 0)
            new_kg    = (fabric["kg"] or 0) + (kg or 0)
        else:
            new_meter = max(0, (fabric["meter"] or 0) - (meter or 0))
            new_kg    = max(0, (fabric["kg"] or 0) - (kg or 0))
        conn.execute("""
            UPDATE fabrics SET meter=?, kg=?, updated_at=datetime('now','localtime') WHERE id=?
        """, (new_meter, new_kg, fabric_id))
    conn.commit()
    mid = c.lastrowid
    conn.close()
    return mid


def get_movements(fabric_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM movements WHERE fabric_id=? ORDER BY movement_date DESC",
        (fabric_id,)
    ).fetchall()
    conn.close()
    return rows


def get_all_movements(limit=200):
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.*, f.product_code, f.product_name, f.color, f.location
        FROM movements m
        LEFT JOIN fabrics f ON m.fabric_id = f.id
        ORDER BY m.movement_date DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


# ── Stats ───────────────────────────────────────────────────────

def get_locations():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT location FROM fabrics WHERE location != '' AND deleted_at IS NULL ORDER BY location"
    ).fetchall()
    conn.close()
    return [r["location"] for r in rows]


def get_summary():
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(*) as total_items,
               SUM(meter) as total_meter,
               SUM(kg) as total_kg,
               SUM(CASE WHEN birim_fiyat > 0 AND meter > 0 THEN meter * birim_fiyat
                        WHEN birim_fiyat > 0 AND kg > 0    THEN kg * birim_fiyat
                        ELSE 0 END) as total_value,
               COUNT(CASE WHEN birim_fiyat > 0 THEN 1 END) as priced_items
        FROM fabrics WHERE deleted_at IS NULL
    """).fetchone()
    conn.close()
    return row


def import_fabrics_bulk(records):
    conn = get_connection()
    c = conn.cursor()
    for r in records:
        c.execute("""
            INSERT INTO fabrics (product_name, product_code, color, location,
                                 meter, kg, piece_count, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (r.get("product_name", ""), r.get("product_code", ""),
              r.get("color", ""), r.get("location", ""),
              r.get("meter") or 0, r.get("kg") or 0,
              r.get("piece_count", ""), r.get("description", "")))
    conn.commit()
    conn.close()
