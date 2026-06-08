"""
Yerel SQLite → Bulut PostgreSQL veri aktarımı.

Kullanım:
  DATABASE_URL="postgresql://..." python3 cloud/migrate.py
"""
import os, sys, sqlite3, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SQLITE_PATH  = os.path.join(os.path.dirname(__file__), "..", "stok.db")

if not DATABASE_URL:
    print("❌  DATABASE_URL tanımlı değil.")
    print("Kullanım: DATABASE_URL='postgresql://...' python3 cloud/migrate.py")
    sys.exit(1)

import db as cloud_db   # cloud/db.py

def migrate():
    print("=" * 52)
    print("  Bursa Knitted — SQLite → PostgreSQL Aktarımı")
    print("=" * 52)

    if not os.path.exists(SQLITE_PATH):
        print(f"❌  Yerel veritabanı bulunamadı: {SQLITE_PATH}")
        sys.exit(1)

    # Önce cloud tablolarını oluştur
    cloud_db.init_db()
    print("✓ Bulut tabloları hazır")

    import psycopg2
    pg   = psycopg2.connect(DATABASE_URL, sslmode="require")
    pgc  = pg.cursor()
    lite = sqlite3.connect(SQLITE_PATH)
    lite.row_factory = sqlite3.Row

    def transfer(table, cols, pg_cols=None):
        pg_cols = pg_cols or cols
        rows = lite.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  {table}: boş, atlandı")
            return 0
        ph   = ",".join(["%s"] * len(cols))
        col_s= ",".join(pg_cols)
        ok   = 0
        for r in rows:
            try:
                vals = []
                for c in cols:
                    try:    vals.append(r[c])
                    except: vals.append(None)
                pgc.execute(
                    f"INSERT INTO {table} ({col_s}) VALUES ({ph}) ON CONFLICT DO NOTHING",
                    vals
                )
                ok += 1
            except Exception as e:
                print(f"    ⚠  Satır atlandı ({table}): {e}")
        pg.commit()
        print(f"  ✓ {table}: {ok}/{len(rows)} satır aktarıldı")
        return ok

    transfer("users",
        ["username","full_name","password_hash","role","active","created_at"])

    transfer("locations",
        ["name","group_name","description","active","sort_order"])

    transfer("fabrics",
        ["product_name","product_code","color","location","meter","kg",
         "piece_count","birim_fiyat","fabric_type","lot","description",
         "deleted_at","deleted_by","created_at","updated_at"])

    transfer("movements",
        ["fabric_id","movement_type","meter","kg","piece_count",
         "notes","user_name","movement_date"])

    lite.close()
    pg.close()
    print()
    print("✅  Aktarım tamamlandı!")
    print()
    print("Şimdi masaüstü programda sunucu adresi olarak")
    print("Render URL'nizi girin ve giriş yapın.")

if __name__ == "__main__":
    migrate()
