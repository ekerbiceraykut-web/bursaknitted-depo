# Diğer Bilgisayarlara Kurulum

## Ana Mac'te Yapılacaklar (bir kez)

1. Terminal'i aç
2. Şunu çalıştır:
   ```
   bash /Users/aykut/tekstil-stok/sunucu_baslat.sh
   ```
3. Ekranda görünen IP adresini not al:
   ```
   Ağ adresi: http://192.168.1.36:5060
   ```
4. Bu terminal açık kaldığı sürece diğer bilgisayarlar bağlanabilir.

---

## Windows Bilgisayara Kurulum

### 1. Python Kur
- https://www.python.org/downloads/ → "Download Python 3.x.x"
- Kurulum sırasında **"Add Python to PATH"** seçeneğini işaretle!

### 2. Program Dosyalarını Kopyala
Ana Mac'teki `/Users/aykut/tekstil-stok/` klasörünün tamamını
Windows bilgisayara kopyala (USB veya ağ paylaşımı ile).

Örnek hedef: `C:\BursaKnitted\`

### 3. Gereksinimleri Kur
Komut İstemi (CMD) aç:
```
cd C:\BursaKnitted
pip install -r requirements.txt
```

### 4. Programı Çalıştır
`run.bat` dosyasına çift tıkla.

### 5. Giriş Ekranında
- **"🌐 Sunucuya Bağlan"** seçeneğini seç
- Sunucu adresi: `http://192.168.1.36:5060`
  (Ana Mac'te görünen IP adresi)
- Kullanıcı adı ve şifre gir

---

## Mac Bilgisayara Kurulum

### 1. Terminal'de:
```bash
cd /indirilen/klasör/tekstil-stok
pip3 install -r requirements.txt
python3 main.py
```

### 2. Giriş Ekranında
- **"🌐 Sunucuya Bağlan"** seçeneğini seç
- Sunucu adresi: `http://192.168.1.36:5060`

---

## Önemli Notlar

- Ana Mac **açık** olmalı ve `sunucu_baslat.sh` çalışıyor olmalı
- Tüm bilgisayarlar **aynı ağda** (WiFi veya kablo) olmalı
- Sunucu Mac kapatılırsa diğerleri bağlanamaz
  (Bu durumda önceki konuşmada anlatılan bulut çözümü kullanılabilir)

---

## Sorun Giderme

**"Bağlanılamadı" hatası:**
- Ana Mac'te sunucunun çalışıp çalışmadığını kontrol et
- IP adresinin doğru olduğunu kontrol et
- Güvenlik duvarı (Firewall) ayarlarını kontrol et:
  - Mac: Sistem Tercihleri → Güvenlik → Güvenlik Duvarı → 5060 portuna izin ver
  - Windows: Windows Defender Firewall → Port 5060 ekle

**Şifre unutuldu:**
Ana Mac'te terminal:
```bash
cd /Users/aykut/tekstil-stok
python3 -c "import database as db; db.update_user_password(1, 'yenisifre')"
```
