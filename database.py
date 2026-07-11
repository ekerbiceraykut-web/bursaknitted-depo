import sqlite3
import os
import hashlib

# Bulut sunucuda kalıcı diske yazmak için STOK_DB_PATH ortam değişkeni kullanılır
DB_PATH = os.environ.get("STOK_DB_PATH") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "stok.db")


def get_connection():
    # timeout + WAL + busy_timeout: çok istemcili sunucuda 'database is locked' önler
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    try:
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
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
            print_type TEXT DEFAULT '',
            zemin_rengi TEXT DEFAULT '',
            baski_desen_no TEXT DEFAULT '',
            lot TEXT DEFAULT '',
            description TEXT DEFAULT '',
            deleted_at TEXT DEFAULT NULL,
            deleted_by TEXT DEFAULT '',
            numune_code TEXT DEFAULT '',
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
            tax_no TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            tax_no TEXT DEFAULT '',
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

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE NOT NULL,
            reference_code TEXT DEFAULT '',
            product_name TEXT DEFAULT '',
            composition TEXT DEFAULT '',
            width TEXT DEFAULT '',
            gramaj TEXT DEFAULT '',
            shrinkage TEXT DEFAULT '',
            price REAL DEFAULT 0,
            supplier TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            cozgu1 TEXT DEFAULT '',
            cozgu2 TEXT DEFAULT '',
            atki1 TEXT DEFAULT '',
            atki2 TEXT DEFAULT '',
            atki3 TEXT DEFAULT '',
            atki4 TEXT DEFAULT '',
            dokuma_tipi TEXT DEFAULT '',
            cozgu_sikligi TEXT DEFAULT '',
            tarak_no TEXT DEFAULT '',
            tarak_eni TEXT DEFAULT '',
            atki_sikligi TEXT DEFAULT '',
            orgu_desen TEXT DEFAULT '',
            maliyet_json TEXT DEFAULT '',
            teknik_aciklama TEXT DEFAULT '',
            price_currency TEXT DEFAULT 'USD',
            jakar_desen_ad TEXT DEFAULT '',
            jakar_desen_data TEXT DEFAULT '',
            jakar_jpeg_ad TEXT DEFAULT '',
            jakar_jpeg_data TEXT DEFAULT '',
            product_status TEXT DEFAULT 'AKTİF',
            numune_code TEXT DEFAULT '',
            iplik_json TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS armur_desenleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            satirlar INTEGER DEFAULT 8,
            sutunlar INTEGER DEFAULT 8,
            grid TEXT DEFAULT '[]',
            notes TEXT DEFAULT '',
            product_code TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            order_date TEXT DEFAULT (date('now','localtime')),
            customer_id INTEGER,
            customer_name TEXT DEFAULT '',
            customer_ref TEXT DEFAULT '',
            product_code TEXT DEFAULT '',
            product_name TEXT DEFAULT '',
            composition TEXT DEFAULT '',
            width TEXT DEFAULT '',
            gramaj TEXT DEFAULT '',
            fabric_type TEXT DEFAULT '',
            color TEXT DEFAULT '',
            lab_no TEXT DEFAULT '',
            meter REAL DEFAULT 0,
            kg REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            currency TEXT DEFAULT 'USD',
            payment_method TEXT DEFAULT '',
            delivery_terms TEXT DEFAULT '',
            delivery_address TEXT DEFAULT '',
            delivery_date TEXT DEFAULT '',
            contract_terms TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'PLANLAMA BEKLİYOR',
            created_by TEXT DEFAULT '',
            sales_rep TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            sort_order INTEGER DEFAULT 0,
            product_code TEXT DEFAULT '',
            product_name TEXT DEFAULT '',
            composition TEXT DEFAULT '',
            width TEXT DEFAULT '',
            gramaj TEXT DEFAULT '',
            fabric_type TEXT DEFAULT '',
            color TEXT DEFAULT '',
            lab_no TEXT DEFAULT '',
            print_type TEXT DEFAULT '',
            zemin_rengi TEXT DEFAULT '',
            baski_desen_no TEXT DEFAULT '',
            meter REAL DEFAULT 0,
            kg REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_no TEXT UNIQUE NOT NULL,
            po_date TEXT DEFAULT (date('now','localtime')),
            supplier_id INTEGER,
            supplier_name TEXT DEFAULT '',
            order_id INTEGER,
            order_no TEXT DEFAULT '',
            currency TEXT DEFAULT 'USD',
            payment_method TEXT DEFAULT '',
            delivery_terms TEXT DEFAULT '',
            expected_delivery TEXT DEFAULT '',
            status TEXT DEFAULT 'BEKLEMEDE',
            notes TEXT DEFAULT '',
            created_by TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            sort_order INTEGER DEFAULT 0,
            product_code TEXT DEFAULT '',
            product_name TEXT DEFAULT '',
            composition TEXT DEFAULT '',
            width TEXT DEFAULT '',
            gramaj TEXT DEFAULT '',
            fabric_type TEXT DEFAULT 'HAM',
            meter REAL DEFAULT 0,
            kg REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            description TEXT DEFAULT '',
            received_meter REAL DEFAULT 0,
            received_kg REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS purchase_order_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            po_item_id INTEGER NOT NULL,
            fabric_id INTEGER,
            product_code TEXT DEFAULT '',
            product_name TEXT DEFAULT '',
            fabric_type TEXT DEFAULT '',
            meter REAL DEFAULT 0,
            kg REAL DEFAULT 0,
            location TEXT NOT NULL DEFAULT '',
            location_group TEXT DEFAULT '',
            unit_price REAL DEFAULT 0,
            user_name TEXT DEFAULT '',
            status TEXT DEFAULT 'BEKLEMEDE',
            received_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_fabrics_code ON fabrics(product_code);
        CREATE INDEX IF NOT EXISTS idx_fabrics_location ON fabrics(location);
        CREATE INDEX IF NOT EXISTS idx_movements_fabric ON movements(fabric_id);
        CREATE INDEX IF NOT EXISTS idx_products_code ON products(product_code);
        CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name);
        CREATE INDEX IF NOT EXISTS idx_orders_no ON orders(order_no);
        CREATE INDEX IF NOT EXISTS idx_orders_code ON orders(product_code);
        CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
        CREATE INDEX IF NOT EXISTS idx_po_no ON purchase_orders(po_no);
        CREATE INDEX IF NOT EXISTS idx_po_items_po ON purchase_order_items(po_id);
        CREATE INDEX IF NOT EXISTS idx_receipts_po ON purchase_order_receipts(po_id);
        CREATE INDEX IF NOT EXISTS idx_receipts_item ON purchase_order_receipts(po_item_id);
    """)

    # Sevkiyat kayıtları
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            order_item_id INTEGER DEFAULT 0,
            product_code TEXT DEFAULT '',
            product_name TEXT DEFAULT '',
            fabric_type TEXT DEFAULT '',
            color TEXT DEFAULT '',
            lot TEXT DEFAULT '',
            meter REAL DEFAULT 0,
            kg REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            shipment_date TEXT DEFAULT (datetime('now','localtime')),
            created_by TEXT DEFAULT '',
            status TEXT DEFAULT 'HAZIRLANIYOR'
        );
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

    # ── CRM modülü (Excel: müşteri listesi / ziyaret / fiili satış / sipariş) ──
    c.executescript("""
        CREATE TABLE IF NOT EXISTS crm_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_turu TEXT DEFAULT '',
            pazarlamaci TEXT DEFAULT '',
            firma TEXT DEFAULT '',
            notlar TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS crm_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            durum TEXT DEFAULT 'GERÇEKLEŞEN',
            tarih TEXT DEFAULT '',
            pazarlamaci TEXT DEFAULT '',
            musteri TEXT DEFAULT '',
            musteri_tipi TEXT DEFAULT '',
            notlar TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS crm_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri TEXT DEFAULT '',
            metre REAL DEFAULT 0,
            tutar REAL DEFAULT 0,
            doviz TEXT DEFAULT 'USD',
            usd_tutar REAL DEFAULT 0,
            ay TEXT DEFAULT '',
            pazarlamaci TEXT DEFAULT '',
            musteri_tipi TEXT DEFAULT '',
            is_iade INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS crm_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri TEXT DEFAULT '',
            pazarlamaci TEXT DEFAULT '',
            musteri_tipi TEXT DEFAULT '',
            tarih TEXT DEFAULT '',
            kod TEXT DEFAULT '',
            renk TEXT DEFAULT '',
            miktar REAL DEFAULT 0,
            maliyet_fiyati REAL DEFAULT 0,
            satis_fiyati REAL DEFAULT 0,
            kar_orani REAL DEFAULT 0,
            teorik_kar_usd REAL DEFAULT 0,
            kar_tl REAL DEFAULT 0,
            vade TEXT DEFAULT '',
            ciro REAL DEFAULT 0,
            ciro_usd REAL DEFAULT 0,
            usd_kuru REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_crm_cust_paz ON crm_customers(pazarlamaci);
        CREATE INDEX IF NOT EXISTS idx_crm_visits_paz ON crm_visits(pazarlamaci);
        CREATE INDEX IF NOT EXISTS idx_crm_sales_paz ON crm_sales(pazarlamaci);
        CREATE INDEX IF NOT EXISTS idx_crm_orders_paz ON crm_orders(pazarlamaci);

        CREATE TABLE IF NOT EXISTS rejected_product_names (
            name TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS iplikler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT DEFAULT '',
            data_json TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS stock_snapshots (
            week_start TEXT PRIMARY KEY,
            captured_at TEXT DEFAULT (datetime('now','localtime')),
            total_items INTEGER DEFAULT 0,
            total_meter REAL DEFAULT 0,
            total_kg REAL DEFAULT 0,
            total_value REAL DEFAULT 0,
            hafta_giris_mt REAL DEFAULT 0,
            hafta_cikis_mt REAL DEFAULT 0
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
        "ALTER TABLE fabrics ADD COLUMN entry_location TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN location TEXT DEFAULT ''",
        "ALTER TABLE customers ADD COLUMN tax_no TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN reference_code TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN cozgu1 TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN cozgu2 TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN atki1 TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN atki2 TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN atki3 TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN atki4 TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN dokuma_tipi TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN cozgu_sikligi TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN tarak_no TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN tarak_eni TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN atki_sikligi TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN orgu_desen TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN maliyet_json TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN teknik_aciklama TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN price_currency TEXT DEFAULT 'USD'",
        "ALTER TABLE products ADD COLUMN jakar_desen_ad TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN jakar_desen_data TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN jakar_jpeg_ad TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN jakar_jpeg_data TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN product_status TEXT DEFAULT 'AKTİF'",
        "ALTER TABLE products ADD COLUMN numune_code TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN iplik_json TEXT DEFAULT ''",
        "ALTER TABLE fabrics ADD COLUMN numune_code TEXT DEFAULT ''",
        "ALTER TABLE armur_desenleri ADD COLUMN product_code TEXT DEFAULT ''",
        """CREATE TABLE IF NOT EXISTS armur_desenleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            satirlar INTEGER DEFAULT 8,
            sutunlar INTEGER DEFAULT 8,
            grid TEXT DEFAULT '[]',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",
        "ALTER TABLE fabrics ADD COLUMN lab_no TEXT DEFAULT ''",
        "ALTER TABLE orders ADD COLUMN currency TEXT DEFAULT 'USD'",
        "ALTER TABLE orders ADD COLUMN sales_rep TEXT DEFAULT ''",
        "ALTER TABLE fabrics ADD COLUMN print_type TEXT DEFAULT ''",
        "ALTER TABLE fabrics ADD COLUMN zemin_rengi TEXT DEFAULT ''",
        "ALTER TABLE fabrics ADD COLUMN baski_desen_no TEXT DEFAULT ''",
        "ALTER TABLE order_items ADD COLUMN print_type TEXT DEFAULT ''",
        "ALTER TABLE order_items ADD COLUMN zemin_rengi TEXT DEFAULT ''",
        "ALTER TABLE order_items ADD COLUMN baski_desen_no TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN out_fabric_type TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN out_print_type TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN out_zemin_rengi TEXT DEFAULT ''",
        "ALTER TABLE movements ADD COLUMN out_baski_desen_no TEXT DEFAULT ''",
        "ALTER TABLE suppliers ADD COLUMN email TEXT DEFAULT ''",
        "ALTER TABLE purchase_order_receipts ADD COLUMN lot TEXT DEFAULT ''",
        "ALTER TABLE purchase_order_items ADD COLUMN color TEXT DEFAULT ''",
        "ALTER TABLE purchase_order_items ADD COLUMN lab_no TEXT DEFAULT ''",
        "ALTER TABLE purchase_order_items ADD COLUMN zemin_rengi TEXT DEFAULT ''",
        "ALTER TABLE purchase_order_items ADD COLUMN baski_desen_no TEXT DEFAULT ''",
    ]
    for sql in migrations:
        try:
            c.execute(sql)
        except Exception:
            pass

    # Giriş lokasyonu boş olan mevcut kayıtlara şimdiki lokasyonunu yaz
    try:
        c.execute("UPDATE fabrics SET entry_location=location WHERE IFNULL(entry_location,'')=''")
    except Exception:
        pass

    # Mevcut numune kayıtlarına numune_code'u geriye dönük doldur (bir defalık)
    try:
        c.execute("UPDATE products SET numune_code=product_code "
                  "WHERE product_status='NUMUNE' AND IFNULL(numune_code,'')=''")
        c.execute("UPDATE fabrics SET numune_code=product_code "
                  "WHERE product_code LIKE 'NMN-%' AND IFNULL(numune_code,'')=''")
    except Exception:
        pass

    # Eski hareketlere, bağlı kumaşın şimdiki lokasyonunu işle (bir defalık doldurma)
    try:
        c.execute("""
            UPDATE movements SET location =
                COALESCE((SELECT location FROM fabrics WHERE fabrics.id = movements.fabric_id), '')
            WHERE IFNULL(location,'') = ''
        """)
    except Exception:
        pass

    # Eski 'İlk stok girişi' hareketlerini satın alma girişi olarak işaretle
    try:
        c.execute("""
            UPDATE movements SET movement_type='SATINALMA GİRİŞİ'
            WHERE movement_type='GİRİŞ' AND notes='İlk stok girişi'
        """)
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

def add_customer(name, code="", phone="", address="", tax_no=""):
    conn = get_connection()
    c = conn.execute(
        "INSERT INTO customers (name, code, phone, address, tax_no) VALUES (?,?,?,?,?)",
        (name.strip(), code.strip(), phone.strip(), address.strip(), tax_no.strip())
    )
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid

def update_customer(cid, name, code, phone, address, tax_no="", active=1):
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET name=?, code=?, phone=?, address=?, tax_no=?, active=? WHERE id=?",
        (name.strip(), code.strip(), phone.strip(), address.strip(), tax_no.strip(), int(active), cid)
    )
    conn.commit(); conn.close()

def delete_customer(cid):
    conn = get_connection()
    conn.execute("DELETE FROM customers WHERE id=?", (cid,))
    conn.commit(); conn.close()

def import_customers_bulk(records):
    """records: [{"name":..., "code":..., "phone":..., "address":..., "tax_no":...}]"""
    conn = get_connection()
    c = conn.cursor()
    for r in records:
        name = r.get("name","").strip()
        if not name: continue
        c.execute(
            "INSERT OR IGNORE INTO customers (name, code, phone, address, tax_no) VALUES (?,?,?,?,?)",
            (name, r.get("code",""), r.get("phone",""), r.get("address",""), r.get("tax_no",""))
        )
    conn.commit(); conn.close()


# ══ CRM modülü ══════════════════════════════════════════════════
# Pazarlamacı listesi (özet kolonları için sabit sıra; veride başkaları da olabilir)
CRM_PAZARLAMACILAR = ["AYKUT EKERBİÇER", "AHMET AYAT", "SEYHAN ZÜNBÜL", "İNAN ACAR", "SERTAÇ İŞLER"]
CRM_MUSTERI_TURLERI = ["MEVCUT MÜŞTERİ", "HEDEF MÜŞTERİ", "POTANSİYEL MÜŞTERİ"]
CRM_MUSTERI_TIPLERI = ["MEVCUT", "POTANSİYEL", "HEDEF"]
CRM_DOVIZLER = ["USD", "EUR", "TL", "GBP"]


# ── CRM: Müşteri Listesi ────────────────────────────────────────
def get_crm_customers(search="", pazarlamaci="", musteri_turu="", active_only=False):
    conn = get_connection()
    q = "SELECT * FROM crm_customers WHERE 1=1"
    p = []
    if active_only:
        q += " AND active=1"
    if pazarlamaci:
        q += " AND pazarlamaci=?"; p.append(pazarlamaci)
    if musteri_turu:
        q += " AND musteri_turu=?"; p.append(musteri_turu)
    if search:
        q += " AND (firma LIKE ? OR pazarlamaci LIKE ?)"
        s = f"%{search}%"; p.extend([s, s])
    q += " ORDER BY pazarlamaci, firma"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return rows

def add_crm_customer(musteri_turu="", pazarlamaci="", firma="", notlar=""):
    conn = get_connection()
    c = conn.execute(
        "INSERT INTO crm_customers (musteri_turu, pazarlamaci, firma, notlar) VALUES (?,?,?,?)",
        (musteri_turu.strip(), pazarlamaci.strip(), firma.strip(), notlar.strip()))
    conn.commit(); cid = c.lastrowid; conn.close()
    return cid

def update_crm_customer(cid, musteri_turu="", pazarlamaci="", firma="", notlar="", active=1):
    conn = get_connection()
    conn.execute(
        "UPDATE crm_customers SET musteri_turu=?, pazarlamaci=?, firma=?, notlar=?, active=? WHERE id=?",
        (musteri_turu.strip(), pazarlamaci.strip(), firma.strip(), notlar.strip(), int(active), cid))
    conn.commit(); conn.close()

def delete_crm_customer(cid):
    conn = get_connection()
    conn.execute("DELETE FROM crm_customers WHERE id=?", (cid,))
    conn.commit(); conn.close()


# ── CRM: Ziyaretler (gerçekleşen / planlanan) ───────────────────
def get_crm_visits(search="", durum="", pazarlamaci=""):
    conn = get_connection()
    q = "SELECT * FROM crm_visits WHERE 1=1"
    p = []
    if durum:
        q += " AND durum=?"; p.append(durum)
    if pazarlamaci:
        q += " AND pazarlamaci=?"; p.append(pazarlamaci)
    if search:
        q += " AND (musteri LIKE ? OR pazarlamaci LIKE ? OR notlar LIKE ?)"
        s = f"%{search}%"; p.extend([s, s, s])
    q += " ORDER BY tarih DESC, id DESC"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return rows

def add_crm_visit(durum="GERÇEKLEŞEN", tarih="", pazarlamaci="", musteri="", musteri_tipi="", notlar=""):
    conn = get_connection()
    c = conn.execute(
        "INSERT INTO crm_visits (durum, tarih, pazarlamaci, musteri, musteri_tipi, notlar) "
        "VALUES (?,?,?,?,?,?)",
        (durum, tarih.strip(), pazarlamaci.strip(), musteri.strip(), musteri_tipi.strip(), notlar.strip()))
    conn.commit(); vid = c.lastrowid; conn.close()
    return vid

def update_crm_visit(vid, durum="GERÇEKLEŞEN", tarih="", pazarlamaci="", musteri="", musteri_tipi="", notlar=""):
    conn = get_connection()
    conn.execute(
        "UPDATE crm_visits SET durum=?, tarih=?, pazarlamaci=?, musteri=?, musteri_tipi=?, notlar=? WHERE id=?",
        (durum, tarih.strip(), pazarlamaci.strip(), musteri.strip(), musteri_tipi.strip(), notlar.strip(), vid))
    conn.commit(); conn.close()

def delete_crm_visit(vid):
    conn = get_connection()
    conn.execute("DELETE FROM crm_visits WHERE id=?", (vid,))
    conn.commit(); conn.close()


# ── CRM: Fiili Satışlar ─────────────────────────────────────────
def get_crm_sales(search="", pazarlamaci="", year=""):
    conn = get_connection()
    q = "SELECT * FROM crm_sales WHERE 1=1"
    p = []
    if pazarlamaci:
        q += " AND pazarlamaci=?"; p.append(pazarlamaci)
    if year:
        q += " AND substr(ay,1,4)=?"; p.append(str(year))
    if search:
        q += " AND (musteri LIKE ? OR pazarlamaci LIKE ?)"
        s = f"%{search}%"; p.extend([s, s])
    q += " ORDER BY ay DESC, id DESC"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return rows

def add_crm_sale(musteri="", metre=0, tutar=0, doviz="USD", usd_tutar=0, ay="",
                 pazarlamaci="", musteri_tipi="", is_iade=0):
    conn = get_connection()
    c = conn.execute(
        "INSERT INTO crm_sales (musteri, metre, tutar, doviz, usd_tutar, ay, pazarlamaci, "
        "musteri_tipi, is_iade) VALUES (?,?,?,?,?,?,?,?,?)",
        (musteri.strip(), _to_float(metre), _to_float(tutar), doviz, _to_float(usd_tutar),
         ay.strip(), pazarlamaci.strip(), musteri_tipi.strip(), int(is_iade)))
    conn.commit(); sid = c.lastrowid; conn.close()
    return sid

def update_crm_sale(sid, musteri="", metre=0, tutar=0, doviz="USD", usd_tutar=0, ay="",
                    pazarlamaci="", musteri_tipi="", is_iade=0):
    conn = get_connection()
    conn.execute(
        "UPDATE crm_sales SET musteri=?, metre=?, tutar=?, doviz=?, usd_tutar=?, ay=?, "
        "pazarlamaci=?, musteri_tipi=?, is_iade=? WHERE id=?",
        (musteri.strip(), _to_float(metre), _to_float(tutar), doviz, _to_float(usd_tutar),
         ay.strip(), pazarlamaci.strip(), musteri_tipi.strip(), int(is_iade), sid))
    conn.commit(); conn.close()

def delete_crm_sale(sid):
    conn = get_connection()
    conn.execute("DELETE FROM crm_sales WHERE id=?", (sid,))
    conn.commit(); conn.close()


# ── CRM: Siparişler (kâr analizli) ──────────────────────────────
def get_crm_orders(search="", pazarlamaci="", year=""):
    conn = get_connection()
    q = "SELECT * FROM crm_orders WHERE 1=1"
    p = []
    if pazarlamaci:
        q += " AND pazarlamaci=?"; p.append(pazarlamaci)
    if year:
        q += " AND substr(tarih,1,4)=?"; p.append(str(year))
    if search:
        q += " AND (musteri LIKE ? OR pazarlamaci LIKE ? OR kod LIKE ?)"
        s = f"%{search}%"; p.extend([s, s, s])
    q += " ORDER BY tarih DESC, id DESC"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return rows

def add_crm_order(musteri="", pazarlamaci="", musteri_tipi="", tarih="", kod="", renk="",
                  miktar=0, maliyet_fiyati=0, satis_fiyati=0, kar_orani=0, teorik_kar_usd=0,
                  kar_tl=0, vade="", ciro=0, ciro_usd=0, usd_kuru=0):
    conn = get_connection()
    c = conn.execute(
        "INSERT INTO crm_orders (musteri, pazarlamaci, musteri_tipi, tarih, kod, renk, miktar, "
        "maliyet_fiyati, satis_fiyati, kar_orani, teorik_kar_usd, kar_tl, vade, ciro, ciro_usd, "
        "usd_kuru) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (musteri.strip(), pazarlamaci.strip(), musteri_tipi.strip(), tarih.strip(), kod.strip(),
         renk.strip(), _to_float(miktar), _to_float(maliyet_fiyati), _to_float(satis_fiyati),
         _to_float(kar_orani), _to_float(teorik_kar_usd), _to_float(kar_tl), vade.strip(),
         _to_float(ciro), _to_float(ciro_usd), _to_float(usd_kuru)))
    conn.commit(); oid = c.lastrowid; conn.close()
    return oid

def update_crm_order(oid, musteri="", pazarlamaci="", musteri_tipi="", tarih="", kod="", renk="",
                     miktar=0, maliyet_fiyati=0, satis_fiyati=0, kar_orani=0, teorik_kar_usd=0,
                     kar_tl=0, vade="", ciro=0, ciro_usd=0, usd_kuru=0):
    conn = get_connection()
    conn.execute(
        "UPDATE crm_orders SET musteri=?, pazarlamaci=?, musteri_tipi=?, tarih=?, kod=?, renk=?, "
        "miktar=?, maliyet_fiyati=?, satis_fiyati=?, kar_orani=?, teorik_kar_usd=?, kar_tl=?, "
        "vade=?, ciro=?, ciro_usd=?, usd_kuru=? WHERE id=?",
        (musteri.strip(), pazarlamaci.strip(), musteri_tipi.strip(), tarih.strip(), kod.strip(),
         renk.strip(), _to_float(miktar), _to_float(maliyet_fiyati), _to_float(satis_fiyati),
         _to_float(kar_orani), _to_float(teorik_kar_usd), _to_float(kar_tl), vade.strip(),
         _to_float(ciro), _to_float(ciro_usd), _to_float(usd_kuru), oid))
    conn.commit(); conn.close()

def delete_crm_order(oid):
    conn = get_connection()
    conn.execute("DELETE FROM crm_orders WHERE id=?", (oid,))
    conn.commit(); conn.close()


# ── CRM: Toplu içe aktarma (Excel) ──────────────────────────────
def crm_import_bulk(customers=None, visits=None, sales=None, orders=None, replace=False):
    """Excel'den okunan kayıtları toplu ekler. replace=True ise ilgili tabloları önce temizler."""
    conn = get_connection()
    c = conn.cursor()
    counts = {"customers": 0, "visits": 0, "sales": 0, "orders": 0}
    if replace and (customers is not None): c.execute("DELETE FROM crm_customers")
    if replace and (visits is not None):    c.execute("DELETE FROM crm_visits")
    if replace and (sales is not None):     c.execute("DELETE FROM crm_sales")
    if replace and (orders is not None):    c.execute("DELETE FROM crm_orders")
    for r in (customers or []):
        c.execute("INSERT INTO crm_customers (musteri_turu, pazarlamaci, firma, notlar) VALUES (?,?,?,?)",
                  (r.get("musteri_turu",""), r.get("pazarlamaci",""), r.get("firma",""), r.get("notlar","")))
        counts["customers"] += 1
    for r in (visits or []):
        c.execute("INSERT INTO crm_visits (durum, tarih, pazarlamaci, musteri, musteri_tipi, notlar) "
                  "VALUES (?,?,?,?,?,?)",
                  (r.get("durum","GERÇEKLEŞEN"), r.get("tarih",""), r.get("pazarlamaci",""),
                   r.get("musteri",""), r.get("musteri_tipi",""), r.get("notlar","")))
        counts["visits"] += 1
    for r in (sales or []):
        c.execute("INSERT INTO crm_sales (musteri, metre, tutar, doviz, usd_tutar, ay, pazarlamaci, "
                  "musteri_tipi, is_iade) VALUES (?,?,?,?,?,?,?,?,?)",
                  (r.get("musteri",""), _to_float(r.get("metre",0)), _to_float(r.get("tutar",0)),
                   r.get("doviz","USD"), _to_float(r.get("usd_tutar",0)), r.get("ay",""),
                   r.get("pazarlamaci",""), r.get("musteri_tipi",""), int(r.get("is_iade",0))))
        counts["sales"] += 1
    for r in (orders or []):
        c.execute("INSERT INTO crm_orders (musteri, pazarlamaci, musteri_tipi, tarih, kod, renk, miktar, "
                  "maliyet_fiyati, satis_fiyati, kar_orani, teorik_kar_usd, kar_tl, vade, ciro, ciro_usd, "
                  "usd_kuru) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (r.get("musteri",""), r.get("pazarlamaci",""), r.get("musteri_tipi",""), r.get("tarih",""),
                   r.get("kod",""), r.get("renk",""), _to_float(r.get("miktar",0)),
                   _to_float(r.get("maliyet_fiyati",0)), _to_float(r.get("satis_fiyati",0)),
                   _to_float(r.get("kar_orani",0)), _to_float(r.get("teorik_kar_usd",0)),
                   _to_float(r.get("kar_tl",0)), r.get("vade",""), _to_float(r.get("ciro",0)),
                   _to_float(r.get("ciro_usd",0)), _to_float(r.get("usd_kuru",0))))
        counts["orders"] += 1
    conn.commit(); conn.close()
    return counts


# ── CRM: Analiz (5 Ways — Pazarlamacı × Ay) ─────────────────────
def get_crm_years():
    conn = get_connection()
    years = set()
    for tbl, col in (("crm_sales", "ay"), ("crm_orders", "tarih"), ("crm_visits", "tarih")):
        for row in conn.execute(f"SELECT DISTINCT substr({col},1,4) y FROM {tbl} WHERE {col}!=''"):
            if row["y"]:
                years.add(row["y"])
    conn.close()
    return sorted(years, reverse=True)

def get_crm_analysis(year=""):
    """Pazarlamacı bazında aylık (1-12) ve yıllık KPI'ları döner.
    Dönüş: {pazarlamaci: {"months": {ay: {metrikler}}, "yearly": {metrikler}}}"""
    conn = get_connection()
    yflt = str(year) if year else None

    def _empty():
        return {"visit_yeni": 0, "visit_mevcut": 0, "yeni_sip_adet": 0, "yeni_sip_metre": 0.0,
                "fiili_metre": 0.0, "fiili_usd": 0.0, "sip_adet": 0, "sip_metre": 0.0,
                "sip_ciro_usd": 0.0, "teorik_kar_usd": 0.0, "kar_orani_top": 0.0}

    data = {}
    def _paz(name):
        name = name or "—"
        if name not in data:
            data[name] = {"months": {m: _empty() for m in range(1, 13)}, "yearly": _empty()}
        return data[name]

    def _ym(s):
        # 'YYYY-MM-DD' veya 'YYYY-MM...' -> (year, month)
        if not s or len(s) < 7:
            return None, None
        return s[0:4], int(s[5:7]) if s[5:7].isdigit() else None

    # 1) Ziyaretler — gerçekleşen, distinct müşteri (yeni=POTANSİYEL/HEDEF, mevcut=MEVCUT)
    visit_sets = {}  # (paz, m, tip_grup) -> set(musteri)
    for r in conn.execute("SELECT pazarlamaci, tarih, musteri, musteri_tipi FROM crm_visits "
                          "WHERE durum='GERÇEKLEŞEN' AND tarih!=''"):
        y, m = _ym(r["tarih"])
        if not m or (yflt and y != yflt):
            continue
        grup = "mevcut" if (r["musteri_tipi"] or "").upper().startswith("MEVCUT") else "yeni"
        visit_sets.setdefault((r["pazarlamaci"], m, grup), set()).add((r["musteri"] or "").strip().upper())
    for (paz, m, grup), musteriler in visit_sets.items():
        d = _paz(paz)
        key = "visit_mevcut" if grup == "mevcut" else "visit_yeni"
        d["months"][m][key] += len(musteriler)
        d["yearly"][key] += len(musteriler)

    # 2) Fiili satışlar — net (iade her zaman düşülür; veride iade işareti karışık olabilir)
    for r in conn.execute("SELECT pazarlamaci, ay, metre, usd_tutar, is_iade FROM crm_sales WHERE ay!=''"):
        y, m = _ym(r["ay"])
        if not m or (yflt and y != yflt):
            continue
        d = _paz(r["pazarlamaci"])
        metre = r["metre"] or 0
        usd = r["usd_tutar"] or 0
        if r["is_iade"]:
            metre = -abs(metre); usd = -abs(usd)
        for scope in (d["months"][m], d["yearly"]):
            scope["fiili_metre"] += metre
            scope["fiili_usd"]   += usd

    # 3) Siparişler — adet/metre/ciro/kâr
    order_rows = {}  # (paz,m) -> list of (ciro_usd, kar_orani)
    for r in conn.execute("SELECT pazarlamaci, tarih, musteri_tipi, miktar, ciro_usd, "
                          "teorik_kar_usd, kar_orani FROM crm_orders WHERE tarih!=''"):
        y, m = _ym(r["tarih"])
        if not m or (yflt and y != yflt):
            continue
        d = _paz(r["pazarlamaci"])
        for scope in (d["months"][m], d["yearly"]):
            scope["sip_adet"] += 1
            scope["sip_metre"] += (r["miktar"] or 0)
            scope["sip_ciro_usd"] += (r["ciro_usd"] or 0)
            scope["teorik_kar_usd"] += (r["teorik_kar_usd"] or 0)
            scope["kar_orani_top"] += (r["kar_orani"] or 0)
        tip = (r["musteri_tipi"] or "").upper()
        if tip and not tip.startswith("MEVCUT"):
            for scope in (d["months"][m], d["yearly"]):
                scope["yeni_sip_adet"] += 1
                scope["yeni_sip_metre"] += (r["miktar"] or 0)
    conn.close()

    # Ortalama alanları türet: ort sipariş tutarı = ciro/adet,
    # ort kâr oranı = ağırlıklı (toplam teorik kâr / toplam ciro)
    for paz, d in data.items():
        for scope in list(d["months"].values()) + [d["yearly"]]:
            adet = scope["sip_adet"]
            ciro = scope["sip_ciro_usd"]
            scope["ort_ciro_usd"] = (ciro / adet) if adet else 0.0
            scope["ort_kar_orani"] = (scope["teorik_kar_usd"] / ciro) if ciro else 0.0
    return data


# ── Tedarikçiler ────────────────────────────────────────────────

def get_all_suppliers(search="", active_only=True):
    conn = get_connection()
    q = "SELECT * FROM suppliers WHERE 1=1"
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

def get_supplier(sid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM suppliers WHERE id=?", (sid,)).fetchone()
    conn.close()
    return row

def add_supplier(name, code="", phone="", address="", tax_no="", email=""):
    conn = get_connection()
    c = conn.execute(
        "INSERT INTO suppliers (name, code, phone, address, tax_no, email) VALUES (?,?,?,?,?,?)",
        (name.strip(), code.strip(), phone.strip(), address.strip(), tax_no.strip(), email.strip())
    )
    conn.commit()
    sid = c.lastrowid
    conn.close()
    return sid

def update_supplier(sid, name, code, phone, address, tax_no="", active=1, email=""):
    conn = get_connection()
    conn.execute(
        "UPDATE suppliers SET name=?, code=?, phone=?, address=?, tax_no=?, active=?, email=? WHERE id=?",
        (name.strip(), code.strip(), phone.strip(), address.strip(), tax_no.strip(), int(active), email.strip(), sid)
    )
    conn.commit(); conn.close()

def delete_supplier(sid):
    conn = get_connection()
    conn.execute("DELETE FROM suppliers WHERE id=?", (sid,))
    conn.commit(); conn.close()

def import_suppliers_bulk(records):
    """records: [{"name":..., "code":..., "phone":..., "address":..., "tax_no":...}]"""
    conn = get_connection()
    c = conn.cursor()
    for r in records:
        name = r.get("name","").strip()
        if not name: continue
        c.execute(
            "INSERT OR IGNORE INTO suppliers (name, code, phone, address, tax_no) VALUES (?,?,?,?,?)",
            (name, r.get("code",""), r.get("phone",""), r.get("address",""), r.get("tax_no",""))
        )
    conn.commit(); conn.close()


# ── Ürün Kataloğu ──────────────────────────────────────────────

def _to_float(val):
    """'636.86 USD', '1.234,56', '%92' gibi birim/etiket içeren değerlerden sayıyı ayıklar."""
    import re
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(val).strip())
    if not m:
        return 0
    try:
        return float(m.group(0).replace(",", "."))
    except Exception:
        return 0

def get_all_products(search="", active_only=True, status_filter=""):
    conn = get_connection()
    q = "SELECT * FROM products WHERE 1=1"
    params = []
    if active_only:
        q += " AND active=1"
    if status_filter:
        q += " AND product_status=?"
        params.append(status_filter)
    if search:
        q += " AND (product_code LIKE ? OR product_name LIKE ? OR reference_code LIKE ? OR numune_code LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    q += " ORDER BY product_code"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows


# Ürün adı havuzu — dağ / şehir / nehir / çiçek / meyve / deniz canlısı / taş / ağaç…
# EN/IT/ES ama Türkçe okunuşu/söylenişi kolay TEK kelimeler. Çekirdek gerçek
# kelimeler + Türkçe'de kolay okunan üretilmiş tek kelimelerle 2000'e tamamlanır.
_CURATED_NAMES = [
    # Çiçekler
    "Lotus", "Iris", "Lavanta", "Kamelya", "Jasmin", "Dalya", "Freesia", "Mimoza",
    "Manolya", "Orkide", "Petunya", "Begonya", "Gardenya", "Lilyum", "Nergis",
    "Fulya", "Açelya", "Zambak", "Yasemin", "Sardunya", "Peony", "Tulip",
    "Lila", "Menekşe", "Papatya", "Gül", "Karanfil", "Sümbül", "Zakkum", "Glayöl",
    "Krizantem", "Kardelen", "Şebboy", "Ortanca", "Fesleğen", "Salkım", "Yonca",
    # Meyveler
    "Mango", "Papaya", "Kivi", "Ananas", "Mandalina", "Kavun", "Bergamot", "Guava",
    "Nektarin", "Portakal", "Vişne", "Kiraz", "Kayısı", "Şeftali", "Nar", "İncir",
    "Ayva", "Limon", "Erik", "Karpuz", "Melon", "Cherry", "Böğürtlen", "Ahududu",
    "Çilek", "Dut", "Greyfurt", "Hurma", "Kestane", "Badem", "Fındık", "Ceviz",
    # Şehirler (IT/ES + genel)
    "Milano", "Verona", "Roma", "Torino", "Siena", "Toskana", "Sevilla", "Cordoba",
    "Malaga", "Granada", "Valencia", "Segovia", "Ronda", "Pisa", "Como", "Napoli",
    "Palermo", "Genova", "Lucca", "Modena", "Parma", "Bilbao", "Murcia", "Girona",
    "Ravenna", "Bologna", "Rimini", "Sorrento", "Capri", "Amalfi", "Toledo",
    "Marbella", "Zaragoza", "Cadiz", "Alicante", "Salerno", "Padova", "Treviso",
    # Nehirler
    "Arno", "Ebro", "Tiber", "Duero", "Tajo", "Adige", "Mino", "Segura",
    "Tevere", "Piave", "Sele", "Serchio", "Ombrone", "Guadiana", "Genil",
    # Dağlar
    "Etna", "Toros", "Sierra", "Andes", "Vezuv", "Alper", "Nevada", "Olimpos",
    "Erciyes", "Uludağ", "Kazdağ", "Aneto", "Teide", "Mulhacen", "Gennargentu",
    # Deniz / deniz canlıları
    "Delfin", "Marlin", "Medusa", "Mercan", "Sedef", "Yunus", "Nautilus", "Coral",
    "Laguna", "Marina", "Perla", "Onda", "Reef", "Kaya", "Foka", "Vatoz", "Orfoz",
    "Levrek", "Çipura", "Lagos", "Yakamoz", "Deniz", "Kumsal", "Dalga", "Sahil",
    # Değerli taş / renk
    "Safir", "Yakut", "Zümrüt", "Opal", "Kehribar", "Turkuaz", "Ametist", "Kuvars",
    "Jade", "Topaz", "Oniks", "İnci", "Kristal", "Lapis", "Mercan", "Firuze",
    # Doğa / gökyüzü (IT/ES)
    "Aurora", "Luna", "Sole", "Estrella", "Cielo", "Vento", "Terra", "Neve",
    "Fiore", "Bella", "Verde", "Azul", "Oro", "Rosa", "Stella", "Nube", "Brisa",
    "Rocio", "Sereno", "Alba", "Sole", "Monte", "Valle", "Bosco", "Prato",
    # Ağaç / bitki / baharat
    "Sedir", "Çınar", "Ladin", "Köknar", "Zeytin", "Defne", "Mersin", "Kekik",
    "Adaçayı", "Nane", "Vanilya", "Tarçın", "Safran", "Zencefil", "Karabiber",
    "Rezene", "Anason", "Kimyon", "Sumak", "Biberiye",
]


def _build_name_pool(target=2000):
    """Çekirdek gerçek kelimelere, Türkçe'de kolay okunan üretilmiş tek kelimeler
    ekleyerek `target` adet benzersiz tek kelimelik ad havuzu oluşturur.
    Sabit seed → her kurulumda/makinede aynı havuz."""
    import random
    rnd = random.Random(20260701)
    cons = ["b", "c", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "y", "z"]
    vowels = ["a", "e", "i", "o", "u"]
    pool, seen = [], set()
    for w in _CURATED_NAMES:
        if w.upper() not in seen:
            seen.add(w.upper()); pool.append(w)
    # 2-3 heceli, ünsüz+ünlü kalıbıyla kolay okunan tek kelimeler üret
    while len(pool) < target:
        w = "".join(rnd.choice(cons) + rnd.choice(vowels) for _ in range(rnd.choice([2, 3])))
        w = w.capitalize()
        if w.upper() not in seen:
            seen.add(w.upper()); pool.append(w)
    return pool


PRODUCT_NAME_POOL = _build_name_pool(2000)


# ── İplik cinsi master listesi (sonradan eklenebilir) ───────────
IPLIK_CINSLERI_BASE = [
    "PES", "Pamuk", "Tencel", "Lyocell", "Rayon", "Viskon", "Asetat", "Akrilik",
    "Nylon", "Sim", "Yün", "Kesik Elyaf", "Keten", "Elastan", "Şönil", "Cupro", "Modal",
]

def get_iplik_cinsleri():
    """Temel + kullanıcı eklemesi iplik cinsleri (benzersiz, sıralı)."""
    import json as _json
    extra = []
    try:
        extra = _json.loads(get_setting("iplik_cinsleri_custom", "[]")) or []
    except Exception:
        extra = []
    out, seen = [], set()
    for c in IPLIK_CINSLERI_BASE + list(extra):
        k = (c or "").strip()
        if k and k.upper() not in seen:
            seen.add(k.upper()); out.append(k)
    return out

def add_iplik_cinsi(name):
    """Yeni iplik cinsini kalıcı listeye ekler."""
    import json as _json
    name = (name or "").strip()
    if not name:
        return
    if name.upper() in {c.upper() for c in get_iplik_cinsleri()}:
        return
    try:
        extra = _json.loads(get_setting("iplik_cinsleri_custom", "[]")) or []
    except Exception:
        extra = []
    extra.append(name)
    set_setting("iplik_cinsleri_custom", _json.dumps(extra, ensure_ascii=False))


# ── İplik Kataloğu ──────────────────────────────────────────────
def get_iplikler(search=""):
    conn = get_connection()
    q = "SELECT * FROM iplikler WHERE 1=1"
    p = []
    if search:
        q += " AND (ad LIKE ? OR data_json LIKE ?)"
        s = f"%{search}%"; p.extend([s, s])
    q += " ORDER BY ad, id"
    rows = conn.execute(q, p).fetchall()
    conn.close()
    return rows

def get_iplik(iid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM iplikler WHERE id=?", (iid,)).fetchone()
    conn.close()
    return row

def add_iplik(ad="", data_json=""):
    conn = get_connection()
    c = conn.execute("INSERT INTO iplikler (ad, data_json) VALUES (?, ?)",
                     (ad.strip(), data_json))
    conn.commit(); iid = c.lastrowid; conn.close()
    return iid

def update_iplik(iid, ad="", data_json=""):
    conn = get_connection()
    conn.execute("UPDATE iplikler SET ad=?, data_json=? WHERE id=?",
                 (ad.strip(), data_json, iid))
    conn.commit(); conn.close()

def delete_iplik(iid):
    conn = get_connection()
    conn.execute("DELETE FROM iplikler WHERE id=?", (iid,))
    conn.commit(); conn.close()


def _unique_product_name(conn, name, exclude_id=None):
    """Ürün adını benzersiz yapar; aynısı varsa sonuna ' 2', ' 3' … ekler."""
    name = (name or "").strip()
    if not name:
        return name
    base = name
    i = 1
    while True:
        q = "SELECT 1 FROM products WHERE UPPER(product_name)=UPPER(?)"
        params = [name]
        if exclude_id:
            q += " AND id<>?"; params.append(exclude_id)
        if not conn.execute(q, params).fetchone():
            return name
        i += 1
        name = f"{base} {i}"


def reject_product_name(name):
    """Kullanıcının onaylamadığı adı kalıcı kara listeye alır (bir daha önerilmez)."""
    name = (name or "").strip()
    if not name:
        return
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO rejected_product_names (name) VALUES (?)", (name.upper(),))
    conn.commit(); conn.close()


def generate_product_name():
    """Havuzdan; hiçbir üründe kullanılmamış VE reddedilmemiş benzersiz tek kelime üretir."""
    import random
    conn = get_connection()
    used = {(r[0] or "").strip().upper() for r in
            conn.execute("SELECT product_name FROM products")}
    used |= {(r[0] or "").strip().upper() for r in
             conn.execute("SELECT name FROM rejected_product_names")}
    conn.close()
    pool = PRODUCT_NAME_POOL[:]
    random.shuffle(pool)

    # Tek kelime — 2000'lik havuzdan kullanılmamış ilk ad
    for name in pool:
        if name.upper() not in used:
            return name

    # Havuz tümüyle tükenirse (çok düşük ihtimal) sayı ekle
    i = 2
    while True:
        for name in pool:
            cand = f"{name} {i}"
            if cand.upper() not in used:
                return cand
        i += 1


def _generate_numune_code(conn):
    # Aktife dönüşmüş numuneler de sayılmalı (numune_code'ta saklı) ki kod tekrar etmesin
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(code,5) AS INTEGER)) FROM ("
        "  SELECT product_code AS code FROM products WHERE product_code LIKE 'NMN-%'"
        "  UNION ALL"
        "  SELECT numune_code AS code FROM products WHERE numune_code LIKE 'NMN-%'"
        ")"
    ).fetchone()
    return f"NMN-{(row[0] or 0) + 1:03d}"


def convert_numune_to_aktif(pid, new_code):
    new_code = new_code.strip().upper()
    conn = get_connection()
    row = conn.execute("SELECT product_code, numune_code FROM products WHERE id=?", (pid,)).fetchone()
    if not row:
        conn.close()
        return
    old_code = row["product_code"]
    nmn_code = row["numune_code"] or old_code   # eski kayıtlarda numune_code boşsa eski kodu kullan

    # Ürün kataloğu: kod gerçek koda döner, numune_code geriye dönük korunur
    conn.execute(
        "UPDATE products SET product_code=?, product_status='AKTİF', numune_code=? WHERE id=?",
        (new_code, nmn_code, pid)
    )
    # Stoktaki kayıtlar: o numune koduyla girilmiş tüm kumaşlar gerçek koda döner,
    # numune_code korunur (hareketler fabric_id ile bağlı olduğundan otomatik takip edilir)
    conn.execute(
        "UPDATE fabrics SET product_code=?, "
        "numune_code=CASE WHEN IFNULL(numune_code,'')='' THEN ? ELSE numune_code END "
        "WHERE product_code=?",
        (new_code, nmn_code, old_code)
    )
    conn.commit()
    conn.close()

def get_product(pid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    conn.close()
    return row

def get_product_by_code(code):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE product_code=?", (code.strip().upper(),)).fetchone()
    conn.close()
    return row

def add_product(product_code, product_name="", composition="", width="", gramaj="", shrinkage="", price=0, supplier="", reference_code="",
                cozgu1="", cozgu2="", atki1="", atki2="", atki3="", atki4="",
                dokuma_tipi="", cozgu_sikligi="", tarak_no="", tarak_eni="",
                atki_sikligi="", orgu_desen="", maliyet_json="", teknik_aciklama="", price_currency="USD",
                jakar_desen_ad="", jakar_desen_data="",
                jakar_jpeg_ad="", jakar_jpeg_data="", product_status="AKTİF", iplik_json=""):
    conn = get_connection()
    numune_code = ""
    if product_status == "NUMUNE":
        product_code = _generate_numune_code(conn)
        numune_code = product_code
    product_name = _unique_product_name(conn, product_name)   # ürün adı benzersiz olsun
    c = conn.execute(
        """INSERT INTO products (product_code, reference_code, product_name, composition, width, gramaj, shrinkage, price, supplier,
           cozgu1, cozgu2, atki1, atki2, atki3, atki4, dokuma_tipi,
           cozgu_sikligi, tarak_no, tarak_eni, atki_sikligi, orgu_desen, maliyet_json, teknik_aciklama, price_currency,
           jakar_desen_ad, jakar_desen_data, jakar_jpeg_ad, jakar_jpeg_data, product_status, numune_code, iplik_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (product_code.strip().upper(), reference_code.strip(), product_name.strip(), composition.strip(), width.strip(),
         gramaj.strip(), shrinkage.strip(), _to_float(price), supplier.strip(),
         cozgu1.strip(), cozgu2.strip(), atki1.strip(), atki2.strip(), atki3.strip(), atki4.strip(),
         dokuma_tipi.strip(), cozgu_sikligi, tarak_no.strip(), tarak_eni, atki_sikligi, orgu_desen.strip(), maliyet_json,
         teknik_aciklama.strip(), price_currency, jakar_desen_ad.strip(), jakar_desen_data,
         jakar_jpeg_ad.strip(), jakar_jpeg_data, product_status, numune_code, iplik_json)
    )
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid

def update_product(pid, product_code, product_name, composition, width, gramaj, shrinkage, price, supplier, active=1, reference_code="",
                   cozgu1="", cozgu2="", atki1="", atki2="", atki3="", atki4="",
                   dokuma_tipi="", cozgu_sikligi="", tarak_no="", tarak_eni="",
                   atki_sikligi="", orgu_desen="", maliyet_json="", teknik_aciklama="", price_currency="USD",
                   jakar_desen_ad="", jakar_desen_data="",
                   jakar_jpeg_ad="", jakar_jpeg_data="", product_status="AKTİF", iplik_json=""):
    conn = get_connection()
    product_name = _unique_product_name(conn, product_name, exclude_id=pid)   # ürün adı benzersiz
    conn.execute(
        """UPDATE products SET product_code=?, reference_code=?, product_name=?, composition=?, width=?, gramaj=?, shrinkage=?,
           price=?, supplier=?, active=?,
           cozgu1=?, cozgu2=?, atki1=?, atki2=?, atki3=?, atki4=?, dokuma_tipi=?,
           cozgu_sikligi=?, tarak_no=?, tarak_eni=?, atki_sikligi=?, orgu_desen=?, maliyet_json=?, teknik_aciklama=?, price_currency=?,
           jakar_desen_ad=?, jakar_desen_data=?, jakar_jpeg_ad=?, jakar_jpeg_data=?, product_status=?, iplik_json=?
           WHERE id=?""",
        (product_code.strip().upper(), reference_code.strip(), product_name.strip(), composition.strip(), width.strip(),
         gramaj.strip(), shrinkage.strip(), _to_float(price), supplier.strip(), int(active),
         cozgu1.strip(), cozgu2.strip(), atki1.strip(), atki2.strip(), atki3.strip(), atki4.strip(),
         dokuma_tipi.strip(), cozgu_sikligi, tarak_no.strip(), tarak_eni, atki_sikligi, orgu_desen.strip(), maliyet_json,
         teknik_aciklama.strip(), price_currency, jakar_desen_ad.strip(), jakar_desen_data,
         jakar_jpeg_ad.strip(), jakar_jpeg_data, product_status, iplik_json, pid)
    )
    conn.commit(); conn.close()

def delete_product(pid):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit(); conn.close()

# ── Armür Desenleri ────────────────────────────────────────────────────────────

def get_all_armur_desenleri(product_code=None):
    """product_code verilirse yalnız o ürün koduna ait desenler; None ise tümü."""
    conn = get_connection()
    if product_code is not None:
        rows = conn.execute(
            "SELECT * FROM armur_desenleri WHERE IFNULL(product_code,'')=? ORDER BY name",
            (product_code,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM armur_desenleri ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_armur_desen(did):
    conn = get_connection()
    row = conn.execute("SELECT * FROM armur_desenleri WHERE id=?", (did,)).fetchone()
    conn.close()
    return dict(row) if row else None

def add_armur_desen(name, satirlar=8, sutunlar=8, grid="[]", notes="", product_code=""):
    conn = get_connection()
    c = conn.execute(
        "INSERT INTO armur_desenleri (name, satirlar, sutunlar, grid, notes, product_code) VALUES (?,?,?,?,?,?)",
        (name.strip(), satirlar, sutunlar, grid, notes.strip(), (product_code or "").strip())
    )
    conn.commit()
    did = c.lastrowid
    conn.close()
    return did

def update_armur_desen(did, name, satirlar, sutunlar, grid, notes=""):
    conn = get_connection()
    conn.execute(
        "UPDATE armur_desenleri SET name=?, satirlar=?, sutunlar=?, grid=?, notes=? WHERE id=?",
        (name.strip(), satirlar, sutunlar, grid, notes.strip(), did)
    )
    conn.commit(); conn.close()

def delete_armur_desen(did):
    conn = get_connection()
    conn.execute("DELETE FROM armur_desenleri WHERE id=?", (did,))
    conn.commit(); conn.close()

def import_products_bulk(records):
    """records: [{"product_code":..., "reference_code":..., "product_name":..., "composition":..., "width":..., "gramaj":..., "shrinkage":..., "price":..., "supplier":...}]
    Var olan ürün kodları güncellenir, yeni kodlar eklenir."""
    conn = get_connection()
    c = conn.cursor()
    count = 0
    for r in records:
        code = str(r.get("product_code","")).strip().upper()
        if not code: continue
        c.execute("""
            INSERT INTO products (product_code, reference_code, product_name, composition, width, gramaj, shrinkage, price, supplier)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(product_code) DO UPDATE SET
                reference_code=excluded.reference_code,
                product_name=excluded.product_name,
                composition=excluded.composition,
                width=excluded.width,
                gramaj=excluded.gramaj,
                shrinkage=excluded.shrinkage,
                price=excluded.price,
                supplier=excluded.supplier
        """, (
            code, str(r.get("reference_code","")).strip(), str(r.get("product_name","")).strip(), str(r.get("composition","")).strip(),
            str(r.get("width","")).strip(), str(r.get("gramaj","")).strip(), str(r.get("shrinkage","")).strip(),
            _to_float(r.get("price",0)), str(r.get("supplier","")).strip(),
        ))
        count += 1
    conn.commit(); conn.close()
    return count
    return count


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


def update_user(user_id, full_name, role):
    conn = get_connection()
    conn.execute("UPDATE users SET full_name=?, role=? WHERE id=?",
                 (full_name, role, user_id))
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
        query += " AND (product_name LIKE ? OR product_code LIKE ? OR color LIKE ? OR description LIKE ? OR numune_code LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s, s])
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
               piece_count, birim_fiyat, fabric_type, lot, description, user_name="",
               entry_location="", lab_no="", print_type="", zemin_rengi="", baski_desen_no=""):
    conn = get_connection()
    c = conn.cursor()
    if not (lot or "").strip():
        lot = _generate_lot(conn)
    if not (entry_location or "").strip():
        entry_location = location   # belirtilmediyse ilk lokasyonu = giriş lokasyonu
    # Numune koduyla girilen stok için numune_code'u otomatik doldur
    numune_code = product_code.strip().upper() if str(product_code).strip().upper().startswith("NMN-") else ""
    c.execute("""
        INSERT INTO fabrics (product_name, product_code, color, location,
                             meter, kg, piece_count, birim_fiyat, fabric_type, lot,
                             description, entry_location, lab_no, print_type,
                             zemin_rengi, baski_desen_no, numune_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (product_name, product_code, color, location,
          meter or 0, kg or 0, piece_count, birim_fiyat or 0, fabric_type, lot,
          description, entry_location, lab_no, print_type, zemin_rengi, baski_desen_no, numune_code))
    fabric_id = c.lastrowid
    if meter or kg:
        c.execute("""
            INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count,
                                   notes, user_name, location)
            VALUES (?, 'SATINALMA GİRİŞİ', ?, ?, ?, 'Satın alma girişi', ?, ?)
        """, (fabric_id, meter or 0, kg or 0, piece_count, user_name, location))
    conn.commit()
    conn.close()
    return fabric_id


def update_fabric(fabric_id, product_name, product_code, color, location,
                  meter, kg, piece_count, birim_fiyat, fabric_type, lot, description,
                  entry_location=None, lab_no=None, print_type=None, zemin_rengi=None,
                  baski_desen_no=None):
    """entry_location/lab_no/print_type/zemin_rengi/baski_desen_no None ise mevcut değer korunur."""
    conn = get_connection()
    # Numune koduysa numune_code'u set et; değilse mevcut değeri koru (dönüşüm sonrası izi kaybetme)
    is_nmn = str(product_code).strip().upper().startswith("NMN-")
    new_nmn = product_code.strip().upper() if is_nmn else None
    conn.execute("""
        UPDATE fabrics SET product_name=?, product_code=?, color=?, location=?,
        meter=?, kg=?, piece_count=?, birim_fiyat=?, fabric_type=?, lot=?, description=?,
        entry_location=COALESCE(?, entry_location),
        lab_no=COALESCE(?, lab_no),
        print_type=COALESCE(?, print_type),
        zemin_rengi=COALESCE(?, zemin_rengi),
        baski_desen_no=COALESCE(?, baski_desen_no),
        numune_code=COALESCE(?, numune_code),
        updated_at=datetime('now','localtime')
        WHERE id=?
    """, (product_name, product_code, color, location,
          meter or 0, kg or 0, piece_count, birim_fiyat or 0, fabric_type, lot, description,
          entry_location, lab_no, print_type, zemin_rengi, baski_desen_no, new_nmn, fabric_id))
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
            if mv["movement_type"] in ("GİRİŞ", "SATINALMA GİRİŞİ"):
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


def is_fabric_linked_to_order(fabric_id):
    """Kumaş bir sipariş PO'suna bağlıysa True döner."""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM purchase_order_receipts WHERE fabric_id=? LIMIT 1",
        (fabric_id,)
    ).fetchone()
    conn.close()
    return row is not None


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
            INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count,
                                   notes, user_name, location)
            VALUES (?, 'SİLME', ?, ?, ?, 'Stoktan silindi', ?, ?)
        """, (fabric_id, fabric["meter"] or 0, fabric["kg"] or 0,
              fabric["piece_count"] or "", user_name, fabric["location"] or ""))
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
                 out_color="", lab_no="", parti_no="",
                 out_fabric_type="", out_print_type="",
                 out_zemin_rengi="", out_baski_desen_no=""):
    """deduct_meter/deduct_kg: ÇIKIŞ'ta stoktan düşülecek miktar, hareketteki
    miktardan farklıysa (fire: çıkış öncesi miktar düşülür) kullanılır."""
    conn = get_connection()
    c = conn.cursor()
    fabric = conn.execute("SELECT * FROM fabrics WHERE id=?", (fabric_id,)).fetchone()
    mv_location = (fabric["location"] or "") if fabric else ""
    c.execute("""
        INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count,
                               notes, user_name, destination, destination_type,
                               out_color, lab_no, parti_no, location,
                               out_fabric_type, out_print_type, out_zemin_rengi, out_baski_desen_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fabric_id, movement_type, meter or 0, kg or 0, piece_count,
          notes, user_name, destination, destination_type,
          out_color, lab_no, parti_no, mv_location,
          out_fabric_type, out_print_type, out_zemin_rengi, out_baski_desen_no))
    mid = c.lastrowid
    if fabric:
        if movement_type in ("GİRİŞ", "SATINALMA GİRİŞİ"):
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
            _transfer_in(conn, fabric, destination, meter, kg, piece_count, user_name, mid,
                          out_fabric_type=out_fabric_type, out_color=out_color,
                          out_print_type=out_print_type, out_zemin_rengi=out_zemin_rengi,
                          out_baski_desen_no=out_baski_desen_no, out_lab_no=lab_no)
    conn.commit()
    conn.close()
    return mid


def _transfer_in(conn, src_fabric, dest_location, meter, kg, piece_count, user_name, src_mid,
                  out_fabric_type="", out_color="", out_print_type="",
                  out_zemin_rengi="", out_baski_desen_no="", out_lab_no=""):
    """Lokasyona yapılan çıkışı hedef lokasyondaki aynı kaliteye giriş olarak işle.

    out_* parametreleri verilirse (ör. HAM kumaş fasona BASKILI olarak
    gönderildiğinde), hedef kayıt bu değerlerle oluşturulur/eşleştirilir;
    boş geçilirse kaynak kumaşın değerlerine düşülür (geriye dönük uyumlu)."""
    dest_fabric_type    = out_fabric_type    or (src_fabric["fabric_type"]    or "")
    dest_color          = out_color          or (src_fabric["color"]         or "")
    dest_print_type     = out_print_type     or (src_fabric["print_type"]    or "")
    dest_zemin_rengi    = out_zemin_rengi    or (src_fabric["zemin_rengi"]   or "")
    dest_baski_desen_no = out_baski_desen_no or (src_fabric["baski_desen_no"] or "")
    dest_lab_no         = out_lab_no         or (src_fabric["lab_no"]        or "")

    dest = conn.execute("""
        SELECT * FROM fabrics
        WHERE product_code=? AND color=? AND IFNULL(fabric_type,'')=? AND IFNULL(lot,'')=?
              AND location=? AND deleted_at IS NULL
    """, (src_fabric["product_code"], dest_color, dest_fabric_type,
          src_fabric["lot"] or "", dest_location)).fetchone()

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
        src_entry = ""
        if "entry_location" in src_fabric.keys():
            src_entry = src_fabric["entry_location"] or ""
        cur = conn.execute("""
            INSERT INTO fabrics (product_name, product_code, color, location, meter, kg,
                                 piece_count, description, birim_fiyat, fabric_type, lot,
                                 entry_location, lab_no, print_type, zemin_rengi, baski_desen_no)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (src_fabric["product_name"] or "", src_fabric["product_code"],
              dest_color, dest_location, meter or 0, kg or 0,
              str(_pieces(piece_count) or "") if _pieces(piece_count) else "",
              src_fabric["description"] or "", src_fabric["birim_fiyat"] or 0,
              dest_fabric_type, src_fabric["lot"] or "",
              src_entry or src_fabric["location"] or "", dest_lab_no,
              dest_print_type, dest_zemin_rengi, dest_baski_desen_no))
        dest_id = cur.lastrowid

    # Hedef tarafta GİRİŞ hareketi kaydet ve iki hareketi birbirine bağla
    cur = conn.execute("""
        INSERT INTO movements (fabric_id, movement_type, meter, kg, piece_count,
                               notes, user_name, destination, destination_type,
                               linked_movement_id, location)
        VALUES (?, 'GİRİŞ', ?, ?, ?, ?, ?, ?, 'Transfer', ?, ?)
    """, (dest_id, meter or 0, kg or 0, piece_count,
          f"Transfer: {src_fabric['location']} → {dest_location}",
          user_name, src_fabric["location"] or "", src_mid, dest_location))
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
        SELECT m.*, f.product_code, f.product_name, f.color,
               f.location AS fabric_location, f.entry_location AS entry_location,
               f.fabric_type AS fabric_type, f.lot AS lot
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
        SELECT m.*, f.product_code, f.product_name, f.color,
               f.location AS fabric_location, f.entry_location AS entry_location,
               f.fabric_type AS fabric_type, f.lot AS lot
        FROM movements m
        LEFT JOIN fabrics f ON m.fabric_id = f.id
        WHERE date(m.movement_date) BETWEEN ? AND ?
        ORDER BY m.movement_date DESC
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows


def get_movement_destinations():
    """Hareketlerde geçen tüm benzersiz hedef lokasyonları (müşteri/dış depo) döndürür."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT destination FROM movements "
        "WHERE IFNULL(destination,'') != '' ORDER BY destination"
    ).fetchall()
    conn.close()
    return [r["destination"] for r in rows]


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
                                   notes, user_name, destination, destination_type, location)
            VALUES (?, 'ÇIKIŞ', ?, ?, '', 'Lot sıfırlama — kalan stok fire yazıldı', ?, '', '', ?)
        """, (fabric_id, rem_m, rem_k, user_name, fabric["location"] or ""))
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


# ── Haftalık stok anlık görüntüleri (dashboard trend) ───────────
def _week_start(d=None):
    """Verilen tarihin (yoksa bugünün) ait olduğu haftanın Pazartesi'sini ISO döndürür."""
    import datetime as _dt
    d = d or _dt.date.today()
    return (d - _dt.timedelta(days=d.weekday())).isoformat()

def capture_stock_snapshot():
    """İçinde bulunulan haftanın stok anlık görüntüsünü kaydeder/günceller (idempotent)."""
    conn = get_connection()
    ws = _week_start()
    s = conn.execute("""
        SELECT COUNT(*) items, IFNULL(SUM(meter),0) mt, IFNULL(SUM(kg),0) kg,
               IFNULL(SUM(CASE WHEN birim_fiyat>0 AND meter>0 THEN meter*birim_fiyat
                               WHEN birim_fiyat>0 AND kg>0    THEN kg*birim_fiyat
                               ELSE 0 END),0) val
        FROM fabrics WHERE deleted_at IS NULL
    """).fetchone()
    flow = conn.execute("""
        SELECT IFNULL(SUM(CASE WHEN movement_type LIKE '%GİRİŞ%' THEN meter ELSE 0 END),0) giris,
               IFNULL(SUM(CASE WHEN movement_type LIKE '%ÇIKIŞ%' OR movement_type LIKE '%SEVK%'
                               THEN meter ELSE 0 END),0) cikis
        FROM movements WHERE date(movement_date) >= ?
    """, (ws,)).fetchone()
    conn.execute("""
        INSERT INTO stock_snapshots (week_start, captured_at, total_items, total_meter, total_kg,
                                     total_value, hafta_giris_mt, hafta_cikis_mt)
        VALUES (?, datetime('now','localtime'), ?, ?, ?, ?, ?, ?)
        ON CONFLICT(week_start) DO UPDATE SET
            captured_at=datetime('now','localtime'), total_items=excluded.total_items,
            total_meter=excluded.total_meter, total_kg=excluded.total_kg,
            total_value=excluded.total_value, hafta_giris_mt=excluded.hafta_giris_mt,
            hafta_cikis_mt=excluded.hafta_cikis_mt
    """, (ws, s["items"], s["mt"], s["kg"], s["val"], flow["giris"], flow["cikis"]))
    conn.commit(); conn.close()
    return ws

def get_stock_snapshots(limit=12):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM stock_snapshots ORDER BY week_start DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return list(reversed(rows))   # eskiden yeniye


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


# ── Siparişler ───────────────────────────────────────────────────

def _generate_order_no(conn):
    """Tarih bazlı benzersiz sipariş numarası: SIP-20260610-001, -002, ..."""
    from datetime import date
    prefix = f"SIP-{date.today().strftime('%Y%m%d')}-"
    row = conn.execute(
        "SELECT order_no FROM orders WHERE order_no LIKE ? ORDER BY order_no DESC LIMIT 1",
        (prefix + "%",)
    ).fetchone()
    if row:
        try:
            seq = int(row["order_no"].rsplit("-", 1)[1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def get_all_orders(search="", status=""):
    conn = get_connection()
    query = """
        SELECT o.*,
            (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id=o.id) AS item_count,
            (SELECT COALESCE(SUM(oi.meter*oi.sale_price),0) FROM order_items oi
                WHERE oi.order_id=o.id) AS total_amount
        FROM orders o WHERE 1=1
    """
    params = []
    if search:
        query += """ AND (o.order_no LIKE ? OR o.customer_name LIKE ? OR o.customer_ref LIKE ?
                  OR EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id=o.id
                             AND (oi.product_code LIKE ? OR oi.color LIKE ? OR oi.lab_no LIKE ?)))"""
        s = f"%{search}%"
        params.extend([s, s, s, s, s, s])
    if status:
        if isinstance(status, (list, tuple)):
            placeholders = ",".join("?" * len(status))
            query += f" AND o.status IN ({placeholders})"
            params.extend(status)
        else:
            query += " AND o.status = ?"
            params.append(status)
    query += " ORDER BY o.id DESC"
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]

    items_by_order = {}
    if rows:
        ids = [r["id"] for r in rows]
        placeholders = ",".join("?" * len(ids))
        item_rows = conn.execute(
            f"SELECT * FROM order_items WHERE order_id IN ({placeholders}) ORDER BY order_id, sort_order, id",
            ids
        ).fetchall()
        for ir in item_rows:
            items_by_order.setdefault(ir["order_id"], []).append(dict(ir))

    conn.close()
    for r in rows:
        r["items"] = items_by_order.get(r["id"], [])
    return rows


def get_order(order_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not row:
        conn.close()
        return None
    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id=? ORDER BY sort_order, id",
        (order_id,)
    ).fetchall()
    conn.close()
    return {**dict(row), "items": [dict(i) for i in items]}


_ORDER_ITEM_FIELDS = ["product_code", "product_name", "composition", "width", "gramaj",
                      "fabric_type", "color", "lab_no", "print_type", "zemin_rengi",
                      "baski_desen_no", "meter", "kg", "sale_price", "description"]


def _insert_order_items(conn, order_id, items):
    for i, item in enumerate(items):
        conn.execute(f"""
            INSERT INTO order_items (order_id, sort_order, {", ".join(_ORDER_ITEM_FIELDS)})
            VALUES (?, ?, {", ".join("?" * len(_ORDER_ITEM_FIELDS))})
        """, (order_id, i, *[item.get(f) for f in _ORDER_ITEM_FIELDS]))


def add_order(customer_id, customer_name, customer_ref, currency, payment_method,
               delivery_terms, delivery_address, delivery_date, order_date,
               notes, items, created_by="", sales_rep=""):
    conn = get_connection()
    order_no = _generate_order_no(conn)
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders (order_no, order_date, customer_id, customer_name, customer_ref,
                            currency, payment_method, delivery_terms, delivery_address,
                            delivery_date, notes, created_by, sales_rep, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ONAYDA')
    """, (order_no, order_date, customer_id, customer_name, customer_ref,
          currency, payment_method, delivery_terms, delivery_address,
          delivery_date, notes, created_by, sales_rep))
    oid = c.lastrowid
    _insert_order_items(conn, oid, items)
    conn.commit()
    conn.close()
    return oid, order_no


def update_order(order_id, customer_id, customer_name, customer_ref, currency,
                 payment_method, delivery_terms, delivery_address, delivery_date,
                 order_date, notes, items, sales_rep=""):
    conn = get_connection()
    conn.execute("""
        UPDATE orders SET customer_id=?, customer_name=?, customer_ref=?, currency=?,
                          payment_method=?, delivery_terms=?, delivery_address=?,
                          delivery_date=?, order_date=?, notes=?, sales_rep=?
        WHERE id=?
    """, (customer_id, customer_name, customer_ref, currency,
          payment_method, delivery_terms, delivery_address,
          delivery_date, order_date, notes, sales_rep, order_id))
    conn.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
    _insert_order_items(conn, order_id, items)
    conn.commit()
    conn.close()


def delete_order(order_id):
    conn = get_connection()
    conn.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
    conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()


def update_order_status(order_id, status):
    conn = get_connection()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()


def get_fabric_stock_in_depo(product_code, fabric_type="HAM"):
    """DEPO grubu lokasyonlardaki toplam metre/kg (silinmemiş kayıtlar)."""
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM(f.meter),0) AS meter, COALESCE(SUM(f.kg),0) AS kg
        FROM fabrics f
        JOIN locations l ON l.name = f.location
        WHERE f.product_code=? AND IFNULL(f.fabric_type,'')=?
              AND l.group_name='DEPO' AND f.deleted_at IS NULL
    """, (product_code, fabric_type)).fetchone()
    conn.close()
    return {"meter": row["meter"] or 0, "kg": row["kg"] or 0}


# ── Satınalma Siparişleri ──────────────────────────────────────────

def _generate_po_no(conn):
    """Tarih bazlı benzersiz PO numarası: PO-20260614-001, -002, ..."""
    from datetime import date
    prefix = f"PO-{date.today().strftime('%Y%m%d')}-"
    row = conn.execute(
        "SELECT po_no FROM purchase_orders WHERE po_no LIKE ? ORDER BY po_no DESC LIMIT 1",
        (prefix + "%",)
    ).fetchone()
    if row:
        try:
            seq = int(row["po_no"].rsplit("-", 1)[1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


_PO_ITEM_FIELDS = ["product_code", "product_name", "composition", "width", "gramaj",
                   "fabric_type", "meter", "kg", "unit_price", "description"]


def _insert_po_items(conn, po_id, items):
    for i, item in enumerate(items):
        conn.execute(f"""
            INSERT INTO purchase_order_items (po_id, sort_order, {", ".join(_PO_ITEM_FIELDS)})
            VALUES (?, ?, {", ".join("?" * len(_PO_ITEM_FIELDS))})
        """, (po_id, i, *[item.get(f) for f in _PO_ITEM_FIELDS]))


def add_purchase_order(supplier_id, supplier_name, order_id, order_no, currency,
                       payment_method, delivery_terms, expected_delivery, notes,
                       items, created_by=""):
    conn = get_connection()
    po_no = _generate_po_no(conn)
    c = conn.cursor()
    c.execute("""
        INSERT INTO purchase_orders (po_no, supplier_id, supplier_name, order_id, order_no,
                                      currency, payment_method, delivery_terms,
                                      expected_delivery, notes, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (po_no, supplier_id, supplier_name, order_id, order_no,
          currency, payment_method, delivery_terms, expected_delivery, notes, created_by))
    po_id = c.lastrowid
    _insert_po_items(conn, po_id, items)
    conn.commit()
    conn.close()
    return po_id, po_no


def get_purchase_order(po_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM purchase_orders WHERE id=?", (po_id,)).fetchone()
    if not row:
        conn.close()
        return None
    items = conn.execute(
        "SELECT * FROM purchase_order_items WHERE po_id=? ORDER BY sort_order, id",
        (po_id,)
    ).fetchall()
    conn.close()
    return {**dict(row), "items": [dict(i) for i in items]}


def get_all_purchase_orders(search="", status="", order_id=None):
    conn = get_connection()
    query = """
        SELECT po.*,
            (SELECT COUNT(*) FROM purchase_order_items pi WHERE pi.po_id=po.id) AS item_count,
            (SELECT COALESCE(SUM(pi.meter*pi.unit_price),0) FROM purchase_order_items pi
                WHERE pi.po_id=po.id) AS total_amount
        FROM purchase_orders po WHERE 1=1
    """
    params = []
    if search:
        query += " AND (po.po_no LIKE ? OR po.supplier_name LIKE ? OR po.order_no LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
    if status:
        query += " AND po.status = ?"
        params.append(status)
    if order_id:
        query += " AND po.order_id = ?"
        params.append(order_id)
    query += " ORDER BY po.id DESC"
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    return rows


def update_purchase_order_status(po_id, status):
    conn = get_connection()
    conn.execute("UPDATE purchase_orders SET status=? WHERE id=?", (status, po_id))
    conn.commit()
    conn.close()


def delete_purchase_order(po_id):
    conn = get_connection()
    conn.execute("DELETE FROM purchase_order_items WHERE po_id=?", (po_id,))
    conn.execute("DELETE FROM purchase_orders WHERE id=?", (po_id,))
    conn.commit()
    conn.close()


def receive_purchase_order_item(po_item_id, meter, kg, location, user_name="",
                                location_group="", lot=""):
    """Mal geldi: stok girişi kaydı. Her çağrı ayrı purchase_order_receipts satırı."""
    conn = get_connection()
    item = conn.execute("SELECT * FROM purchase_order_items WHERE id=?", (po_item_id,)).fetchone()
    if not item:
        conn.close()
        return
    po_id = item["po_id"]
    new_rm = (item["received_meter"] or 0) + (meter or 0)
    new_rk = (item["received_kg"] or 0) + (kg or 0)
    conn.execute("UPDATE purchase_order_items SET received_meter=?, received_kg=? WHERE id=?",
                 (new_rm, new_rk, po_item_id))

    all_items = conn.execute(
        "SELECT meter, kg, received_meter, received_kg FROM purchase_order_items WHERE po_id=?",
        (po_id,)
    ).fetchall()
    any_received = any((r["received_meter"] or 0) > 0 or (r["received_kg"] or 0) > 0 for r in all_items)
    fully_received = all(
        (r["received_meter"] or 0) >= (r["meter"] or 0) and (r["received_kg"] or 0) >= (r["kg"] or 0)
        for r in all_items
    )
    new_status = "TAMAMLANDI" if fully_received else ("KISMİ GELDİ" if any_received else "BEKLEMEDE")
    conn.execute("UPDATE purchase_orders SET status=? WHERE id=?", (new_status, po_id))
    po_row = conn.execute(
        "SELECT order_no, po_no FROM purchase_orders WHERE id=?", (po_id,)
    ).fetchone()
    conn.commit()
    conn.close()

    # Lot otomatik üret
    if not lot:
        fabric_type_short = (item["fabric_type"] or "HAM").split()[0][:3].upper()
        import datetime as _dt2
        date_str = _dt2.date.today().strftime("%Y%m%d")
        conn_lot = get_connection()
        existing = conn_lot.execute(
            "SELECT COUNT(*) FROM purchase_order_receipts WHERE received_at LIKE ?",
            (f"{_dt2.date.today().isoformat()}%",)
        ).fetchone()[0]
        conn_lot.close()
        lot = f"{fabric_type_short}-{date_str}-{existing+1:03d}"

    order_no_tag = f"SİPARİŞ:{po_row['order_no']} | PO:{po_row['po_no']} | " if po_row else ""
    fabric_id = add_fabric(
        product_name=item["product_name"] or "", product_code=item["product_code"],
        color=dict(item).get("color","") or "", location=location,
        meter=meter or 0, kg=kg or 0,
        piece_count="", birim_fiyat=item["unit_price"] or 0,
        fabric_type=item["fabric_type"] or "HAM", lot=lot,
        lab_no=dict(item).get("lab_no","") or "",
        description=f"{order_no_tag}{item['description'] or ''}",
        user_name=user_name, entry_location=location,
    )

    conn3 = get_connection()
    conn3.execute("""
        INSERT INTO purchase_order_receipts
            (po_id, po_item_id, fabric_id, product_code, product_name, fabric_type,
             meter, kg, location, location_group, unit_price, user_name, status, lot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (po_id, po_item_id, fabric_id,
          item["product_code"] or "", item["product_name"] or "",
          item["fabric_type"] or "HAM",
          meter or 0, kg or 0, location, location_group or "",
          item["unit_price"] or 0, user_name,
          "BEKLEMEDE" if (location_group or "") != "DEPO" else "DEPODA",
          lot))
    conn3.commit()

    # Sipariş durumunu otomatik güncelle (boyahane sevk varsa)
    if (location_group or "") not in ("DEPO", ""):
        po_row2 = conn3.execute("SELECT order_id FROM purchase_orders WHERE id=?", (po_id,)).fetchone()
        if po_row2 and po_row2["order_id"]:
            oid2 = po_row2["order_id"]
            cur = conn3.execute("SELECT status FROM orders WHERE id=?", (oid2,)).fetchone()
            cur_status = cur["status"] if cur else ""
            if cur_status in ("PLANLANDI", "PLANLAMA - GÖRDÜ"):
                # İlk boyahane sevki
                conn3.execute("UPDATE orders SET status='BOYAHANAYA SEVKLER BAŞLADI' WHERE id=?", (oid2,))
            elif cur_status == "BOYAHANAYA SEVKLER BAŞLADI":
                # Tüm PO miktarı geldi mi kontrol et
                total_needed = conn3.execute(
                    "SELECT COALESCE(SUM(oi.meter),0) FROM order_items oi WHERE oi.order_id=?", (oid2,)
                ).fetchone()[0]
                total_boyahane = conn3.execute("""
                    SELECT COALESCE(SUM(r.meter),0)
                    FROM purchase_order_receipts r
                    JOIN purchase_orders po ON po.id=r.po_id
                    WHERE po.order_id=? AND r.location_group != 'DEPO' AND r.location_group != ''
                """, (oid2,)).fetchone()[0]
                if float(total_boyahane) >= float(total_needed) * 0.99:
                    conn3.execute("UPDATE orders SET status='TÜM KUMAŞLAR BOYAHANEDE' WHERE id=?", (oid2,))
            conn3.commit()
    conn3.close()


def get_po_items_for_order(order_id):
    """Bir siparişe bağlı tüm PO kalemlerini döner (PO bilgisiyle birlikte)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT pi.*,
               po.po_no, po.supplier_name, po.supplier_id, po.status AS po_status,
               po.id AS po_id_ref
        FROM purchase_order_items pi
        JOIN purchase_orders po ON po.id = pi.po_id
        WHERE po.order_id = ?
        ORDER BY po.id, pi.sort_order, pi.id
    """, (order_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_po_receipts(po_id):
    """Bir PO'ya ait tüm mal girişi kayıtları (ayrı kalem ayrı satır)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.*,
               po.order_no, po.po_no
        FROM purchase_order_receipts r
        LEFT JOIN purchase_orders po ON po.id = r.po_id
        WHERE r.po_id = ?
        ORDER BY r.received_at
    """, (po_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_boyahane_queue(status_filter=""):
    """Dış depoya gönderilen ve boyahane planlaması bekleyen kayıtlar."""
    conn = get_connection()
    q = """
        SELECT r.*,
               po.order_no, po.po_no, po.supplier_name
        FROM purchase_order_receipts r
        LEFT JOIN purchase_orders po ON po.id = r.po_id
        WHERE r.location_group != 'DEPO' AND r.location_group != ''
    """
    params = []
    if status_filter:
        q += " AND r.status = ?"
        params.append(status_filter)
    q += " ORDER BY r.received_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_boyahane_receipt_status(receipt_id, status):
    conn = get_connection()
    conn.execute("UPDATE purchase_order_receipts SET status=? WHERE id=?",
                 (status, receipt_id))
    conn.commit()
    conn.close()


def update_boyahane_receipt(receipt_id, meter, kg, lot, location, location_group,
                             user_name=""):
    """Mal girişi kaydını ve bağlı kumaş kaydını günceller, PO kalemine yansıtır."""
    conn = get_connection()
    r = conn.execute("SELECT * FROM purchase_order_receipts WHERE id=?",
                     (receipt_id,)).fetchone()
    if not r:
        conn.close()
        return

    old_m = float(r["meter"] or 0)
    old_k = float(r["kg"] or 0)
    po_item_id = r["po_item_id"]
    fabric_id  = r["fabric_id"]

    # Makbuz güncelle
    conn.execute("""
        UPDATE purchase_order_receipts
        SET meter=?, kg=?, lot=?, location=?, location_group=?
        WHERE id=?
    """, (meter, kg, lot, location, location_group, receipt_id))

    # Bağlı kumaşı güncelle
    if fabric_id:
        conn.execute("""
            UPDATE fabrics
            SET meter=?, kg=?, lot=?, location=?,
                updated_at=datetime('now','localtime')
            WHERE id=?
        """, (meter, kg, lot, location, fabric_id))

    # PO kaleminin received toplamını yeniden hesapla
    totals = conn.execute("""
        SELECT COALESCE(SUM(meter),0) AS sm, COALESCE(SUM(kg),0) AS sk
        FROM purchase_order_receipts WHERE po_item_id=?
    """, (po_item_id,)).fetchone()
    conn.execute("""
        UPDATE purchase_order_items
        SET received_meter=?, received_kg=?
        WHERE id=?
    """, (totals["sm"], totals["sk"], po_item_id))

    conn.commit()
    conn.close()


def delete_boyahane_receipt(receipt_id, user_name=""):
    """Mal girişi kaydını siler, bağlı kumaşı soft-delete yapar, PO kalemini günceller."""
    conn = get_connection()
    r = conn.execute("SELECT * FROM purchase_order_receipts WHERE id=?",
                     (receipt_id,)).fetchone()
    if not r:
        conn.close()
        return

    po_item_id = r["po_item_id"]
    po_id      = r["po_id"]
    fabric_id  = r["fabric_id"]

    # Makbuzu sil
    conn.execute("DELETE FROM purchase_order_receipts WHERE id=?", (receipt_id,))

    # Bağlı kumaşı soft-delete
    if fabric_id:
        fabric = conn.execute("SELECT * FROM fabrics WHERE id=?", (fabric_id,)).fetchone()
        if fabric:
            conn.execute("""
                UPDATE fabrics
                SET deleted_at=datetime('now','localtime'), deleted_by=?,
                    updated_at=datetime('now','localtime')
                WHERE id=?
            """, (user_name, fabric_id))
            conn.execute("""
                INSERT INTO movements
                    (fabric_id, movement_type, meter, kg, piece_count, notes, user_name, location)
                VALUES (?, 'SİLME', ?, ?, '', ?, ?, ?)
            """, (fabric_id, fabric["meter"] or 0, fabric["kg"] or 0,
                  "Boyahane girişi silindi", user_name, fabric["location"] or ""))

    # PO kalemine kalan toplamı yaz
    totals = conn.execute("""
        SELECT COALESCE(SUM(meter),0) AS sm, COALESCE(SUM(kg),0) AS sk
        FROM purchase_order_receipts WHERE po_item_id=?
    """, (po_item_id,)).fetchone()
    conn.execute("""
        UPDATE purchase_order_items SET received_meter=?, received_kg=? WHERE id=?
    """, (totals["sm"], totals["sk"], po_item_id))

    # PO genel durumunu güncelle
    all_items = conn.execute(
        "SELECT meter, kg, received_meter, received_kg FROM purchase_order_items WHERE po_id=?",
        (po_id,)
    ).fetchall()
    any_recv = any((x["received_meter"] or 0) > 0 for x in all_items)
    fully    = all((x["received_meter"] or 0) >= (x["meter"] or 0) for x in all_items)
    new_st   = "TAMAMLANDI" if fully else ("KISMİ GELDİ" if any_recv else "BEKLEMEDE")
    conn.execute("UPDATE purchase_orders SET status=? WHERE id=?", (new_st, po_id))

    conn.commit()
    conn.close()


# ── Sipariş Onay ─────────────────────────────────────────────────

def approve_order(order_id, admin_name=""):
    conn = get_connection()
    conn.execute(
        "UPDATE orders SET status='ONAYLANDI - PLANLAMADA', created_by=COALESCE(NULLIF(created_by,''),?) WHERE id=?",
        (admin_name, order_id))
    conn.commit()
    conn.close()


def get_pending_approval_orders():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM orders WHERE status='ONAYDA' ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Sevkiyat ─────────────────────────────────────────────────────

def add_order_shipment(order_id, items, created_by=""):
    """items: list of {product_code, product_name, fabric_type, color, lot, meter, kg, notes}"""
    conn = get_connection()
    for it in items:
        conn.execute("""
            INSERT INTO order_shipments
                (order_id, order_item_id, product_code, product_name, fabric_type,
                 color, lot, meter, kg, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id,
              it.get("order_item_id", 0),
              it.get("product_code", ""),
              it.get("product_name", ""),
              it.get("fabric_type", ""),
              it.get("color", ""),
              it.get("lot", ""),
              it.get("meter", 0),
              it.get("kg", 0),
              it.get("notes", ""),
              created_by))

    # Sipariş durumunu otomatik güncelle
    cur = conn.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
    cur_status = cur["status"] if cur else ""
    if cur_status not in ("MÜŞTERİYE SEVKLER BAŞLADI", "SİPARİŞ TAMAMLANDI", "İPTAL"):
        conn.execute("UPDATE orders SET status='MÜŞTERİYE SEVKLER BAŞLADI' WHERE id=?", (order_id,))

    # Toplam sipariş metresi vs toplam sevk metresi
    total_ordered = conn.execute(
        "SELECT COALESCE(SUM(meter),0) FROM order_items WHERE order_id=?", (order_id,)
    ).fetchone()[0]
    total_shipped = conn.execute(
        "SELECT COALESCE(SUM(meter),0) FROM order_shipments WHERE order_id=?", (order_id,)
    ).fetchone()[0]
    if float(total_ordered) > 0 and float(total_shipped) >= float(total_ordered) * 0.99:
        conn.execute("UPDATE orders SET status='SİPARİŞ TAMAMLANDI' WHERE id=?", (order_id,))

    conn.commit()
    conn.close()


def get_order_shipments(order_id=None):
    conn = get_connection()
    if order_id:
        rows = conn.execute(
            "SELECT * FROM order_shipments WHERE order_id=? ORDER BY shipment_date DESC",
            (order_id,)
        ).fetchall()
    else:
        rows = conn.execute("""
            SELECT s.*, o.order_no, o.customer_name
            FROM order_shipments s
            JOIN orders o ON o.id = s.order_id
            ORDER BY s.shipment_date DESC
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_shippable_orders():
    """Sevk edilebilir veya sevk sürecindeki siparişler."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.*,
            (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id=o.id) AS item_count,
            (SELECT COALESCE(SUM(oi.meter),0) FROM order_items oi WHERE oi.order_id=o.id) AS total_meter,
            (SELECT COALESCE(SUM(s.meter),0) FROM order_shipments s WHERE s.order_id=o.id) AS shipped_meter
        FROM orders o
        WHERE o.status IN (
            'TÜM KUMAŞLAR BOYAHANEDE','MÜŞTERİYE SEVKLER BAŞLADI',
            'PLANLANDI','BOYAHANAYA SEVKLER BAŞLADI'
        )
        ORDER BY o.id DESC
    """).fetchall()
    ids = [r["id"] for r in rows]
    items_by_order = {}
    if ids:
        placeholders = ",".join("?" * len(ids))
        for ir in conn.execute(
            f"SELECT * FROM order_items WHERE order_id IN ({placeholders}) ORDER BY order_id,sort_order,id", ids
        ).fetchall():
            items_by_order.setdefault(ir["order_id"], []).append(dict(ir))
    conn.close()
    result = [dict(r) for r in rows]
    for r in result:
        r["items"] = items_by_order.get(r["id"], [])
    return result


# ── Ayarlar ──────────────────────────────────────────────────────

_COMPANY_DEFAULTS = {
    "name": "BURSA KNITTED FABRIC TEKSTİL SANAYİ VE TİCARET LTD.ŞTİ.",
    "address": "Panayır Mah. 505. Sk. No:1/92 16100 Osmangazi/BURSA",
    "phone": "+90 504 05 16",
    "tax": "1911204932",
    "origin": "Turkey Republic",
    "website": "www.bursaknitted.com.tr",
    "email_info": "info@bursaknitted.com",
    "email_planlama": "planlama@bursaknitted.com",
    "bank_info": """GARANTI BANK
Swift: TGBATRISXXX
$ IBAN: TR18 0006 2000 4740 0009 0799 43
€ IBAN: TR88 0006 2000 4740 0009 0799 44
₺ IBAN: TR83 0006 2000 4740 0006 2922 54

KUVEYT TÜRK
Swift: KTEFTRISXXX
$ IBAN: TR96 0020 5000 0976 6553 7001 01
€ IBAN: TR69 0020 5000 0976 6553 7001 02
₺ IBAN: TR80 0020 5000 0976 6553 7000 01""",
    "contract_template": """1- BURSA KNITTED FABRIC TEKSTİL yukarıda belirtilen özelliklere uygun üretim yapacağını taahhüt eder
2- Sipariş Miktarı "+/- %10", teslim tarihi "+/- 7 gün" toleranslı olabilir. Alıcı bu hususu önceden kabul ve beyan eder.
3- Sipariş bedeli için taraflar dövize endeksli para birimiyle anlaştığı takdirde Fatura, sevkiyat tarihindeki Merkez Bankası döviz satış kuru üzerinden kesilir. Vadesi gelen ödemeler yapılırken fiili ödeme günündeki Merkez Bankasının belirlemiş olduğu döviz satış kuru üzerinden ödeme gerçekleştirilmesi gerekmektedir. Aksi takdirde oluşacak kur farkları tarafınızdan talep edilecektir. Fiyatlara KDV dahil değildir.
4- Dövize endeksli faturaya ilişkin Türk Lirası çek ile ödeme yapılması halinde çekin tahsil edildiği tarihteki kur ile vade (düzenlenme tarihi) arasında oluşacak kur farkı için ayrıca kur farkı faturası kesilir. Çek tesliminden sonra tahsilat makbuzuna çekince ibaresi eklenmek suretiyle Alıcı tarafından kaşe ve imza altına alınacaktır. Alıcı, kur farkı çekincesi yapılacağını sipariş formu ile kabul, beyan ve taahhüt eder.
5- İşbu sipariş sözleşmesi karşı tarafa iletildikten sonra 2 iş günü içerisinde sözleşmenin içeriğine ilişkin herhangi bir çekince veya itiraz bildirilmediği takdirde kabul edilmiş sayılır. İşbu sözleşme tarafınıza mail yoluyla gönderilecek olup 48 saat içerisinde tarafımıza dönüş yapılmadığı takdirde kabul edilmiş sayılacaktır.
6- Malın müşteriye tesliminden sonra TTK madde 23'e göre açık ayıplarda 2 gün, gizli ayıplarda 8 gün geçtikten sonra kalite itirazında bulunulamaz. Malın tahliyesi, depolanması ve kötü kullanımından kaynaklanan zararlardan Alıcı sorumludur.
7- Faturaların ödeme ve vade farkı hesabında irsaliye tarihi baz alınır.
8- İhraç kayıtlı satışlarda ayrıca protokol ve taahhütname düzenlenir.
9- Fatura bedelleri belirlenen vade ve şekilde; nakit, kabule bağlı çek veya banka havalesi ile ödenir. Vadesinde ödenmeyen faturalara aylık "%5" vade farkı uygulanır; vade farkı peşin tahsil edilir.
10- Müşteri, bu sipariş bedeli için yapacağı banka havalesini tam yapmaması veya verdiği çek/senetlerden birinin karşılıksız çıkması/protesto olması halinde tüm borcun muaccel hale geleceğini ve aleyhine icra takibi yapılmasını kabul eder.
11- Sözleşmenin alıcıya tesliminden itibaren 48 saat içinde içerik kabul edilmiş sayılır. Bu kabulden sonra Alıcı tarafından sözleşmenin haksız feshi halinde, sipariş bedelinin %30'una tekabül eden bedel + KDV, cezai şart olarak Alıcı'dan tahsil edilir.
12- Alıcının bu sözleşmedeki borçlarını gereği gibi ifa etmemesi halinde, mevcut siparişlerin teslim yetkisi BURSA KNITTED FABRIC TEKS. ÜR. SAN. TİC. A.Ş.'nin inisiyatifindedir.
13- Müşteriye 1'er aylık dönemler itibariyle cari hesap ekstresi gönderilir. 15 gün içinde yazılı itiraz olmazsa mutabakat sağlandığı kabul edilir.
14- İşbu satış sözleşmesinde TTK md. 87 ve müteakip maddeleri çerçevesinde cari hesap hükümleri uygulanır. Cari hesap üç ayda bir sona erer; feshi ihbar edilmedikçe kendiliğinden üçer aylık dönemler itibariyle yenilenir.
15- İhtilaf halinde yetkili merci İstanbul mahkeme ve icra daireleridir.
16- Kesilen veya daha sonradan işlem gören kumaşlarda iade veya reklamasyon kabul edilemez.""",
}


def get_setting(key, default=""):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_connection()
    conn.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_company_settings():
    return {k: get_setting(f"company_{k}", default) for k, default in _COMPANY_DEFAULTS.items()}


def save_company_settings(**kwargs):
    for k, v in kwargs.items():
        if k in _COMPANY_DEFAULTS:
            set_setting(f"company_{k}", v)
