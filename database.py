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

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
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

    # Boyahane fire kayıtları
    c.execute("""
        CREATE TABLE IF NOT EXISTS fire_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fabric_id INTEGER,
            movement_id INTEGER,
            product_code TEXT DEFAULT '',
            color TEXT DEFAULT '',
            lot TEXT DEFAULT '',
            boyahane TEXT DEFAULT '',
            customer TEXT DEFAULT '',
            pre_meter REAL DEFAULT 0,
            pre_kg REAL DEFAULT 0,
            out_meter REAL DEFAULT 0,
            out_kg REAL DEFAULT 0,
            fire_pct REAL DEFAULT 0,
            manual_pct INTEGER DEFAULT 0,
            record_type TEXT DEFAULT 'ÇIKIŞ',
            user_name TEXT DEFAULT '',
            out_color TEXT DEFAULT '',
            lab_no TEXT DEFAULT '',
            parti_no TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    # Migrations — mevcut DB'ye yeni sütunlar
    migrations = [
        "ALTER TABLE fabrics ADD COLUMN birim_fiyat REAL DEFAULT 0",
        "ALTER TABLE fabrics ADD COLUMN fabric_type TEXT DEFAULT ''",
        "ALTER TABLE fabrics ADD COLUMN lot TEXT DEFAULT ''",
        "ALTER TABLE fabrics ADD COLUMN deleted_at TEXT DEFAULT NULL",
        "ALTER TABLE fabrics ADD COLUMN deleted_by TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN user_name TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN destination TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN destination_type TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN linked_movement_id INTEGER DEFAULT 0",
        "ALTER TABLE movements ADD COLUMN out_color TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN lab_no TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN parti_no TEXT DEFAULT ''",
        "ALTER TABLE fire_records ADD COLUMN out_color TEXT DEFAULT ''",
        "ALTER TABLE fire_records ADD COLUMN lab_no TEXT DEFAULT ''",
        "ALTER TABLE fire_records ADD COLUMN parti_no TEXT DEFAULT ''",
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


# ── Customers ───────────────────────────────────────────────────

def get_all_customers(search="", active_only=True):
    conn = get_connection()
    q = "SELECT * FROM customers WHERE 1=1"
    params = []
    if active_only:
        q += " AND active=1"
    if search:
        q += " AND (name LIKE ? OR code LIKE ? OR phone LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
    q += " ORDER BY name"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows

def get_customer(cid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
    conn.close()
    return row

def add_customer(name, code="", phone="", address=""):
    conn = get_connection()
    c = conn.execute(
        "INSERT INTO customers (name, code, phone, address) VALUES (?,?,?,?)",
        (name.strip(), code.strip(), phone.strip(), address.strip())
    )
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid

def update_customer(cid, name, code, phone, address, active=1):
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET name=?, code=?, phone=?, address=?, active=? WHERE id=?",
        (name.strip(), code.strip(), phone.strip(), address.strip(), int(active), cid)
    )
    conn.commit(); conn.close()

def delete_customer(cid):
    conn = get_connection()
    conn.execute("DELETE FROM customers WHERE id=?", (cid,))
    conn.commit(); conn.close()

def import_customers_bulk(records):
    """records: [{"name":..., "code":..., "phone":..., "address":...}]"""
    conn = get_connection()
    c = conn.cursor()
    for r in records:
        name = r.get("name","").strip()
        if not name: continue
        c.execute(
            "INSERT OR IGNORE INTO customers (name, code, phone, address) VALUES (?,?,?,?)",
            (name, r.get("code",""), r.get("phone",""), r.get("address",""))
        )
    conn.commit(); conn.close()


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
    """Lokasyonda aktif stok kaydı varsa silinemez — stoklar korunur."""
    conn = get_connection()
    row = conn.execute("SELECT name FROM locations WHERE id=?", (loc_id,)).fetchone()
    if row:
        cnt = conn.execute(
            "SELECT COUNT(*) c FROM fabrics WHERE location=? AND deleted_at IS NULL",
            (row["name"],)).fetchone()["c"]
        if cnt > 0:
            conn.close()
            raise ValueError(
                f"'{row['name']}' lokasyonunda {cnt} stok kaydı var. "
                f"Önce stokları başka lokasyona taşıyın, sonra silebilirsiniz.")
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


def _generate_lot(conn):
    """Tarih bazlı benzersiz lot numarası: LOT-20260610-001, -002, ..."""
    from datetime import date
    prefix = f"LOT-{date.today().strftime('%Y%m%d')}-"
    row = conn.execute(
        "SELECT lot FROM fabrics WHERE lot LIKE ? ORDER BY lot DESC LIMIT 1",
        (prefix + "%",)
    ).fetchone()
    if row:
        try:
            seq = int(row["lot"].rsplit("-", 1)[1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def add_fabric(product_name, product_code, color, location, meter, kg,
               piece_count, birim_fiyat, fabric_type, lot, description, user_name=""):
    conn = get_connection()
    c = conn.cursor()
    if not (lot or "").strip():
        lot = _generate_lot(conn)
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
    """Son hareketi geri al: GİRİŞ → ÇIKIŞ kadar düş, ÇIKIŞ → GİRİŞ kadar ekle.
    Transfer ise (linked_movement_id dolu) karşı taraftaki hareket de geri alınır."""
    conn = get_connection()
    m = conn.execute("SELECT * FROM movements WHERE id=?", (movement_id,)).fetchone()
    if not m:
        conn.close()
        return
    to_reverse = [m]
    linked_id = m["linked_movement_id"] if "linked_movement_id" in m.keys() else 0
    if linked_id:
        lm = conn.execute("SELECT * FROM movements WHERE id=?", (linked_id,)).fetchone()
        if lm:
            to_reverse.append(lm)

    for mv in to_reverse:
        fabric = conn.execute("SELECT meter, kg, piece_count FROM fabrics WHERE id=?",
                              (mv["fabric_id"],)).fetchone()
        if fabric:
            if mv["movement_type"] == "GİRİŞ":
                new_meter = max(0, (fabric["meter"] or 0) - (mv["meter"] or 0))
                new_kg    = max(0, (fabric["kg"] or 0) - (mv["kg"] or 0))
                new_pieces = _apply_piece_delta(fabric["piece_count"], mv["piece_count"], -1)
            else:
                new_meter = (fabric["meter"] or 0) + (mv["meter"] or 0)
                new_kg    = (fabric["kg"] or 0) + (mv["kg"] or 0)
                new_pieces = _apply_piece_delta(fabric["piece_count"], mv["piece_count"], +1)
            if new_pieces is None:
                new_pieces = fabric["piece_count"] or ""
            conn.execute("UPDATE fabrics SET meter=?, kg=?, piece_count=?, updated_at=datetime('now','localtime') WHERE id=?",
                         (new_meter, new_kg, new_pieces, mv["fabric_id"]))
        conn.execute("DELETE FROM movements WHERE id=?", (mv["id"],))
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

def _pieces(val):
    """piece_count sayısal ise int döner, değilse None ('HURDA VERİLDİ' gibi)."""
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


def _apply_piece_delta(current, delta, sign):
    """Mevcut top sayısına deltayı uygula. Sayısal değilse dokunma (None döner)."""
    d = _pieces(delta)
    if d is None or d == 0:
        return None
    cur = _pieces(current) or 0
    return str(max(0, cur + sign * d))


def add_movement(fabric_id, movement_type, meter, kg, piece_count, notes,
                 user_name="", destination="", destination_type="",
                 deduct_meter=None, deduct_kg=None,
                 out_color="", lab_no="", parti_no=""):
    """deduct_meter/deduct_kg: ÇIKIŞ'ta stoktan düşülecek miktar, hareketteki
    miktardan farklıysa (fire: çıkış öncesi miktar düşülür) kullanılır."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count,
                               notes, user_name, destination, destination_type,
                               out_color, lab_no, parti_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fabric_id, movement_type, meter or 0, kg or 0, piece_count,
          notes, user_name, destination, destination_type,
          out_color, lab_no, parti_no))
    mid = c.lastrowid
    fabric = conn.execute("SELECT * FROM fabrics WHERE id=?", (fabric_id,)).fetchone()
    if fabric:
        if movement_type == "GİRİŞ":
            new_meter = (fabric["meter"] or 0) + (meter or 0)
            new_kg    = (fabric["kg"] or 0) + (kg or 0)
            new_pieces = _apply_piece_delta(fabric["piece_count"], piece_count, +1)
        else:
            d_meter = deduct_meter if deduct_meter is not None else (meter or 0)
            d_kg    = deduct_kg    if deduct_kg    is not None else (kg or 0)
            new_meter = max(0, (fabric["meter"] or 0) - d_meter)
            new_kg    = max(0, (fabric["kg"] or 0) - d_kg)
            new_pieces = _apply_piece_delta(fabric["piece_count"], piece_count, -1)
        if new_pieces is None:
            new_pieces = fabric["piece_count"] or ""
        conn.execute("""
            UPDATE fabrics SET meter=?, kg=?, piece_count=?, updated_at=datetime('now','localtime') WHERE id=?
        """, (new_meter, new_kg, new_pieces, fabric_id))

        # Lokasyona çıkış = transfer: miktarları hedef lokasyondaki kayda ekle
        if movement_type == "ÇIKIŞ" and destination_type == "Lokasyon" and destination:
            _transfer_in(conn, fabric, destination, meter, kg, piece_count, user_name, mid)
    conn.commit()
    conn.close()
    return mid


def _transfer_in(conn, src_fabric, dest_location, meter, kg, piece_count, user_name, src_mid):
    """Lokasyona yapılan çıkışı hedef lokasyondaki aynı kaliteye giriş olarak işle."""
    dest = conn.execute("""
        SELECT * FROM fabrics
        WHERE product_code=? AND color=? AND IFNULL(fabric_type,'')=? AND IFNULL(lot,'')=?
              AND location=? AND deleted_at IS NULL
    """, (src_fabric["product_code"], src_fabric["color"],
          src_fabric["fabric_type"] or "", src_fabric["lot"] or "",
          dest_location)).fetchone()

    if dest:
        dest_id = dest["id"]
        new_meter = (dest["meter"] or 0) + (meter or 0)
        new_kg    = (dest["kg"] or 0) + (kg or 0)
        new_pieces = _apply_piece_delta(dest["piece_count"], piece_count, +1)
        if new_pieces is None:
            new_pieces = dest["piece_count"] or ""
        conn.execute("""
            UPDATE fabrics SET meter=?, kg=?, piece_count=?, updated_at=datetime('now','localtime') WHERE id=?
        """, (new_meter, new_kg, new_pieces, dest_id))
    else:
        cur = conn.execute("""
            INSERT INTO fabrics (product_name, product_code, color, location, meter, kg,
                                 piece_count, description, birim_fiyat, fabric_type, lot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (src_fabric["product_name"] or "", src_fabric["product_code"],
              src_fabric["color"] or "", dest_location, meter or 0, kg or 0,
              str(_pieces(piece_count) or "") if _pieces(piece_count) else "",
              src_fabric["description"] or "", src_fabric["birim_fiyat"] or 0,
              src_fabric["fabric_type"] or "", src_fabric["lot"] or ""))
        dest_id = cur.lastrowid

    # Hedef tarafta GİRİŞ hareketi kaydet ve iki hareketi birbirine bağla
    cur = conn.execute("""
        INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count,
                               notes, user_name, destination, destination_type, linked_movement_id)
        VALUES (?, 'GİRİŞ', ?, ?, ?, ?, ?, ?, 'Transfer', ?)
    """, (dest_id, meter or 0, kg or 0, piece_count,
          f"Transfer: {src_fabric['location']} → {dest_location}",
          user_name, src_fabric["location"] or "", src_mid))
    conn.execute("UPDATE movements SET linked_movement_id=? WHERE id=?", (cur.lastrowid, src_mid))


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


def get_movements_by_range(start_date, end_date):
    """start_date ve end_date dahil, 'YYYY-MM-DD' formatında."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.*, f.product_code, f.product_name, f.color, f.location
        FROM movements m
        LEFT JOIN fabrics f ON m.fabric_id = f.id
        WHERE date(m.movement_date) BETWEEN ? AND ?
        ORDER BY m.movement_date DESC
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows


# ── Boyahane Fire Kayıtları ─────────────────────────────────────

def add_fire_record(fabric_id, movement_id, product_code, color, lot, boyahane,
                    customer, pre_meter, pre_kg, out_meter, out_kg, fire_pct,
                    manual_pct=False, record_type="ÇIKIŞ", user_name="",
                    out_color="", lab_no="", parti_no=""):
    conn = get_connection()
    c = conn.execute("""
        INSERT INTO fire_records (fabric_id, movement_id, product_code, color, lot,
                                  boyahane, customer, pre_meter, pre_kg, out_meter,
                                  out_kg, fire_pct, manual_pct, record_type, user_name,
                                  out_color, lab_no, parti_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fabric_id, movement_id, product_code, color, lot, boyahane, customer,
          pre_meter or 0, pre_kg or 0, out_meter or 0, out_kg or 0, fire_pct or 0,
          1 if manual_pct else 0, record_type, user_name,
          out_color, lab_no, parti_no))
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid


def get_fire_records():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM fire_records ORDER BY created_at DESC, id DESC"
    ).fetchall()
    conn.close()
    return rows


def _insert_lot_total(conn, fabric, extra_fire_meter=0, extra_fire_kg=0, user_name=""):
    """Lotun tüm ÇIKIŞ fire kayıtlarını toplayıp 'LOT TOPLAMI' satırı ekler.
    extra_*: sıfırlamada fire sayılan kalan stok."""
    sums = conn.execute("""
        SELECT SUM(pre_meter) pm, SUM(pre_kg) pk, SUM(out_meter) om, SUM(out_kg) ok,
               MAX(manual_pct) anymanual
        FROM fire_records
        WHERE product_code=? AND color=? AND IFNULL(lot,'')=? AND boyahane=?
              AND record_type='ÇIKIŞ'
    """, (fabric["product_code"], fabric["color"] or "", fabric["lot"] or "",
          fabric["location"])).fetchone()
    pre_m = (sums["pm"] or 0) + (extra_fire_meter or 0)
    pre_k = (sums["pk"] or 0) + (extra_fire_kg or 0)
    out_m = sums["om"] or 0
    out_k = sums["ok"] or 0
    if pre_m <= 0 and pre_k <= 0:
        return None
    base = pre_m if pre_m > 0 else pre_k
    out  = out_m if pre_m > 0 else out_k
    pct = max(0.0, (base - out) / base * 100) if base > 0 else 0.0
    c = conn.execute("""
        INSERT INTO fire_records (fabric_id, movement_id, product_code, color, lot,
                                  boyahane, customer, pre_meter, pre_kg, out_meter,
                                  out_kg, fire_pct, manual_pct, record_type, user_name)
        VALUES (?, 0, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, 'LOT TOPLAMI', ?)
    """, (fabric["id"], fabric["product_code"], fabric["color"] or "",
          fabric["lot"] or "", fabric["location"], pre_m, pre_k, out_m, out_k,
          pct, sums["anymanual"] or 0, user_name))
    return c.lastrowid


def lot_total_exists(product_code, color, lot, boyahane):
    """Bu lot için LOT TOPLAMI satırı (kapanış) var mı?"""
    conn = get_connection()
    row = conn.execute("""
        SELECT id FROM fire_records
        WHERE product_code=? AND color=? AND IFNULL(lot,'')=? AND boyahane=?
              AND record_type='LOT TOPLAMI'
    """, (product_code, color or "", lot or "", boyahane)).fetchone()
    conn.close()
    return row is not None


def finalize_lot_if_consumed(fabric_id, user_name=""):
    """Lot tükendiyse (metre ve kilo ~0) ve fire kaydı varsa LOT TOPLAMI satırı ekle.
    Aynı lot için ikinci kez eklenmez."""
    conn = get_connection()
    fabric = conn.execute("SELECT * FROM fabrics WHERE id=?", (fabric_id,)).fetchone()
    done = None
    if fabric and (fabric["meter"] or 0) < 0.01 and (fabric["kg"] or 0) < 0.01:
        already = conn.execute("""
            SELECT id FROM fire_records
            WHERE product_code=? AND color=? AND IFNULL(lot,'')=? AND boyahane=?
                  AND record_type='LOT TOPLAMI'
        """, (fabric["product_code"], fabric["color"] or "", fabric["lot"] or "",
              fabric["location"])).fetchone()
        if not already:
            done = _insert_lot_total(conn, fabric, user_name=user_name)
            conn.commit()
    conn.close()
    return done is not None


def reset_lot_fire(fabric_id, user_name=""):
    """İsteğe bağlı sıfırlama: kalan stok fire sayılır, lot kapatılır,
    LOT TOPLAMI satırı eklenir. Kalan miktarlar döner."""
    conn = get_connection()
    fabric = conn.execute("SELECT * FROM fabrics WHERE id=?", (fabric_id,)).fetchone()
    if not fabric:
        conn.close()
        return None
    rem_m = fabric["meter"] or 0
    rem_k = fabric["kg"] or 0
    if rem_m > 0 or rem_k > 0:
        conn.execute("""
            INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count,
                                   notes, user_name, destination, destination_type)
            VALUES (?, 'ÇIKIŞ', ?, ?, '', 'Lot sıfırlama — kalan stok fire yazıldı', ?, '', '')
        """, (fabric_id, rem_m, rem_k, user_name))
        conn.execute("""
            UPDATE fabrics SET meter=0, kg=0, piece_count='0',
            updated_at=datetime('now','localtime') WHERE id=?
        """, (fabric_id,))
    _insert_lot_total(conn, fabric, extra_fire_meter=rem_m, extra_fire_kg=rem_k,
                      user_name=user_name)
    conn.commit()
    conn.close()
    return {"meter": rem_m, "kg": rem_k}


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
