"""
Otomatik yedekleme sistemi.
- Her program açılışında günlük yedek alır
- Son 30 yedeği saklar, eskilerini siler
- Yedek durumunu raporlar
"""
import shutil
import os
import glob
from datetime import datetime, date

DB_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stok.db")
BACKUP_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yedekler")
MAX_BACKUPS = 30   # son 30 gün sakla
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def _load_config():
    import json
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_config(data):
    import json
    cfg = _load_config()
    cfg.update(data)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def take_backup(force=False):
    """
    Günlük yedek al. Bugün zaten alındıysa atlar (force=True ile zorla).
    Döner: (başarılı: bool, mesaj: str)
    """
    if not os.path.exists(DB_PATH):
        return False, "Veritabanı bulunamadı"

    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Bugün yedek alındı mı?
    today = date.today().isoformat()
    cfg = _load_config()
    if not force and cfg.get("last_backup") == today:
        return True, f"Bugün ({today}) yedek zaten alınmış"

    # Yedek dosya adı
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = os.path.join(BACKUP_DIR, f"stok_{ts}.db")

    try:
        shutil.copy2(DB_PATH, dest)
        _save_config({"last_backup": today, "last_backup_file": dest})
        _cleanup_old_backups()
        return True, f"Yedek alındı: yedekler/stok_{ts}.db"
    except Exception as e:
        return False, f"Yedekleme hatası: {e}"


def _cleanup_old_backups():
    """En eski yedekleri sil, MAX_BACKUPS kadar tut."""
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "stok_*.db")))
    while len(files) > MAX_BACKUPS:
        try:
            os.remove(files.pop(0))
        except Exception:
            break


def get_backup_status():
    """
    Döner: dict {
        last_backup: str,       # "2026-06-09" veya ""
        backup_count: int,
        backup_size_mb: float,
        is_today: bool,
        oldest: str,
        newest: str,
    }
    """
    cfg = _load_config()
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "stok_*.db")))
    total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
    last = cfg.get("last_backup", "")
    return {
        "last_backup":    last,
        "backup_count":   len(files),
        "backup_size_mb": round(total_size / 1024 / 1024, 2),
        "is_today":       last == date.today().isoformat(),
        "oldest":         os.path.basename(files[0])  if files else "",
        "newest":         os.path.basename(files[-1]) if files else "",
        "backup_dir":     BACKUP_DIR,
    }


def restore_backup(backup_file_path):
    """
    Belirtilen yedek dosyasından geri yükle.
    Önce mevcut DB'yi .before_restore olarak saklar.
    """
    if not os.path.exists(backup_file_path):
        raise FileNotFoundError(f"Yedek dosyası bulunamadı: {backup_file_path}")
    # Önce mevcut DB'yi sakla
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe = DB_PATH + f".before_restore_{ts}"
    shutil.copy2(DB_PATH, safe)
    shutil.copy2(backup_file_path, DB_PATH)
    return safe
