# Bulut Kurulum — Mac Kapalıyken de Herkes Çalışır

Sunucu (server.py) Render.com'da 7/24 çalışır; tüm bilgisayarlar
hangi WiFi'de olursa olsun internetten bağlanır.

- Süre: ~15 dakika
- Maliyet: ~$7/ay (Render Starter) + ~$0.25/ay (1 GB kalıcı disk)
- Kod zaten GitHub'da olduğu için ek yükleme gerekmez.

---

## ADIM 1 — Render Hesabı

1. https://render.com → **Get Started** → **GitHub ile giriş yap**
2. Render'a GitHub erişim izni ver (bursaknitted-depo reposunu seç)

## ADIM 2 — Servisi Oluştur

1. Render panelinde **New +** → **Web Service**
2. `bursaknitted-depo` reposunu seç
3. Render, repodaki `render.yaml` dosyasını otomatik tanır →
   **"Apply"** / onayla de. (Tanımazsa elle gir:
   - Build Command: `echo ok`
   - Start Command: `python server.py`
   - Plan: **Starter**
   - Disks: Add Disk → Mount Path `/var/data`, Size 1 GB
   - Environment → `STOK_DB_PATH` = `/var/data/stok.db`)
4. Kart bilgisi isteyebilir → Starter planı için gerekli
5. **Deploy** → 2-3 dakika bekle

## ADIM 3 — Adresi Al ve Test Et

Deploy bitince üstte adres görünür, örnek:

    https://bursaknitted-depo.onrender.com

Tarayıcıdan test: `https://....onrender.com/ping` →
`{"ok": true, "data": "pong"}` görünmeli.

## ADIM 4 — Bilgisayarları Bağla

**Tüm bilgisayarlarda** (Mac dahil):
1. Programı aç → giriş ekranında **"🌐 Sunucuya Bağlan"**
2. Sunucu adresi: `https://bursaknitted-depo.onrender.com`
3. Kullanıcı: `admin` / Şifre: `admin123`
4. **İlk girişte mutlaka şifreyi değiştirin!**
   (👤 Kullanıcılar menüsünden)

Artık:
- Mac kapalıyken herkes çalışmaya devam eder
- Her bilgisayar farklı WiFi'de / 4G'de olabilir
- Veri tek yerde (bulutta) tutulur, çakışma olmaz

---

## Notlar

- **Yedek:** Render panel → servis → Disks → Snapshots ile disk
  yedeği alınabilir. Ayrıca arada bir programdan Excel'e dışa
  aktarmak ucuz bir ek güvencedir.
- **Yerel sunucu artık gerekmez:** `sunucu_baslat.sh` ve ngrok
  kullanımı bulut devredeyken gereksizdir.
- **Güncelleme:** Koda yeni özellik eklenip GitHub'a push edilince
  Render otomatik yeniden deploy eder (Auto-Deploy açık olmalı).
  Veritabanı kalıcı diskte olduğu için veriler korunur.
