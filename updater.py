"""
Otomatik güncelleme — GitHub'dan son sürümü kontrol eder.
git pull ile günceller, programı yeniden başlatır.
"""
import subprocess, os, sys, threading

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

# Windows'ta git komutları konsol penceresi parlatmasın
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _run(cmd):
    return subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True,
                          creationflags=_NO_WINDOW)


def check_update():
    """
    Güncelleme var mı kontrol et.
    Döner: (var_mi: bool, mesaj: str)
    """
    try:
        # Remote'u güncelle
        _run(["git", "fetch", "origin", "main"])
        # Kaç commit geride?
        r = _run(["git", "rev-list", "HEAD..origin/main", "--count"])
        count = int(r.stdout.strip() or "0")
        if count > 0:
            # Son commit mesajını al
            log = _run(["git", "log", "origin/main", "-1", "--pretty=%s"])
            msg = log.stdout.strip()
            return True, f"{count} güncelleme mevcut\nSon değişiklik: {msg}"
        return False, "Program güncel"
    except Exception as e:
        return False, f"Kontrol edilemedi: {e}"


def apply_update():
    """
    Güncellemeyi uygula.
    Döner: (başarılı: bool, mesaj: str)
    """
    try:
        r = _run(["git", "pull", "origin", "main"])
        if r.returncode == 0:
            return True, "Güncelleme tamamlandı. Program yeniden başlatılıyor..."
        return False, r.stderr or r.stdout
    except Exception as e:
        return False, str(e)


def restart():
    """Programı yeniden başlat."""
    os.execv(sys.executable, [sys.executable] + sys.argv)


def check_in_background(callback):
    """Arka planda kontrol et, sonuç hazır olunca callback(var_mi, mesaj) çağır."""
    def _run():
        var_mi, msg = check_update()
        callback(var_mi, msg)
    threading.Thread(target=_run, daemon=True).start()
