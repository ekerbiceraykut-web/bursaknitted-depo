# Bursa Knitted Depo Takip — Kurulum Kılavuzu
## Diğer Bilgisayarlara Kurulum

---

## HAZIRLIK (Ana Mac'te bir kez yapılır)

Program hazır olduktan sonra `tekstil-stok` klasörünü USB veya ağ üzerinden diğer bilgisayara kopyalayın.

---

## WINDOWS BİLGİSAYAR KURULUMU

### Adım 1 — Python Kurulumu

1. Tarayıcıda şu adrese gidin: **https://python.org/downloads**
2. Sarı **"Download Python 3.x.x"** butonuna tıklayın
3. İndirilen `.exe` dosyasını çalıştırın
4. ⚠️ **ÖNEMLİ:** Kurulum ekranının en altındaki **"Add Python to PATH"** kutucuğunu **mutlaka** işaretleyin
5. **"Install Now"** butonuna tıklayın
6. Kurulum bitince **"Close"** butonuna basın

**Doğrulama:** Komut İstemi (CMD) açın, şunu yazın:
```
python --version
```
`Python 3.x.x` yazıyorsa kurulum başarılı.

---

### Adım 2 — Git Kurulumu

1. Tarayıcıda: **https://git-scm.com/download/win**
2. Otomatik indirme başlar, `.exe` dosyasını çalıştırın
3. Tüm seçenekleri varsayılan bırakın, sadece **"Next"** butonuna basın
4. **"Install"** → **"Finish"**

**Doğrulama:** CMD'de:
```
git --version
```
`git version 2.x.x` yazıyorsa tamam.

---

### Adım 3 — Programı Kopyala

USB veya ağ paylaşımından `tekstil-stok` klasörünü kopyalayın:
- Hedef: `C:\BursaKnitted\tekstil-stok\`

---

### Adım 4 — Gereksinimleri Kur

Komut İstemi (CMD) açın:
```
cd C:\BursaKnitted\tekstil-stok
pip install -r requirements.txt
```
İnternet bağlantısı gereklidir. 2-5 dakika sürebilir.

---

### Adım 5 — Programı Çalıştır

`run.bat` dosyasına **çift tıklayın**.

İlk açılışta giriş ekranı gelir:
- **"🌐 Sunucuya Bağlan"** seçin
- Sunucu adresi: `https://bursaknitted-depo.onrender.com`
- Kullanıcı adı ve şifrenizi girin

---

### Adım 6 — Masaüstü Kısayolu Oluştur

1. `run.bat` dosyasına **sağ tıklayın**
2. **"Kısayol Oluştur"**
3. Kısayolu masaüstüne taşıyın
4. Kısayola sağ tıklayın → **"Yeniden Adlandır"** → `Bursa Knitted Depo`

---

## MAC BİLGİSAYAR KURULUMU

### Adım 1 — Xcode Araçları (Terminal gerekiyorsa)

Terminal açın (Spotlight → Terminal):
```bash
xcode-select --install
```
Zaten kuruluysa hata verir, sorun değil.

---

### Adım 2 — Programı Kopyala

USB veya AirDrop ile `tekstil-stok` klasörünü şuraya kopyalayın:
```
/Users/KULLANICI_ADI/tekstil-stok/
```

---

### Adım 3 — Gereksinimleri Kur

Terminal'de:
```bash
cd ~/tekstil-stok
pip3 install -r requirements.txt
```

---

### Adım 4 — Programı Çalıştır

Terminal'de:
```bash
python3 main.py
```

Veya `run.sh` dosyasına çift tıklayın.

---

### Adım 5 — Masaüstü Kısayolu

Mevcut programdaki `run.sh` yerine masaüstüne `.app` kısayolu oluşturulur:
```bash
osacompile -o ~/Desktop/"Bursa\ Knitted\ Depo.app" << 'EOF'
do shell script "/usr/bin/python3 /Users/KULLANICI_ADI/tekstil-stok/main.py > /tmp/depo.log 2>&1 &"
EOF
xattr -cr ~/Desktop/"Bursa Knitted Depo.app"
```
⚠️ `KULLANICI_ADI` kısmını o bilgisayarın kullanıcı adıyla değiştirin.

---

## SUNUCU AYARI (Her bilgisayarda)

Giriş ekranında:

| Alan | Değer |
|------|-------|
| Bağlantı | 🌐 Sunucuya Bağlan |
| Sunucu Adresi | `https://bursaknitted-depo.onrender.com` |
| Kullanıcı Adı | (size verilen kullanıcı adı) |
| Şifre | (size verilen şifre) |

---

## KULLANICI EKLEME

Yeni bilgisayar için yeni kullanıcı oluşturmak gerekirse:

1. Ana Mac'te programı açın
2. **Dashboard** → **👤 Kullanıcı Yönetimi** → **+ Yeni Kullanıcı**
3. Kullanıcı adı, ad soyad ve şifre belirleyin
4. Rol: `kullanici` (sadece stok giriş/çıkış) veya `admin` (tam yetki)

---

## SORUN GİDERME

### "Sunucuya bağlanılamadı" hatası
- İnternet bağlantısını kontrol edin
- Sunucu adresi doğru mu: `https://bursaknitted-depo.onrender.com`
- Render.com'da servisin çalışıp çalışmadığını kontrol edin

### "pip install" hata veriyor (Windows)
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Program açılmıyor (Windows)
- Python PATH'e eklenmiş mi? CMD'de `python --version` deneyin
- Antivirüs yazılımı engelliyor olabilir — `tekstil-stok` klasörünü istisna listesine ekleyin

### "Module not found" hatası
```
pip install PyQt6 openpyxl pandas pyngrok
```

---

## GÜNCELLEME

Program her açılışta otomatik güncelleme kontrolü yapar.

**"🔄 Güncelleme Mevcut"** bildirimi çıkarsa:
- **"Evet"** butonuna basın
- Program kendini güncelleyip yeniden başlar

Manuel güncelleme (CMD/Terminal):
```
cd tekstil-stok
git pull origin main
```

---

## ÖZET KONTROL LİSTESİ

### Windows için:
- [ ] Python 3.x kuruldu ("Add to PATH" işaretli)
- [ ] Git kuruldu
- [ ] `tekstil-stok` klasörü kopyalandı
- [ ] `pip install -r requirements.txt` çalıştırıldı
- [ ] `run.bat` ile program açıldı
- [ ] Sunucu adresi girildi ve giriş yapıldı
- [ ] Masaüstü kısayolu oluşturuldu

### Mac için:
- [ ] `tekstil-stok` klasörü kopyalandı
- [ ] `pip3 install -r requirements.txt` çalıştırıldı
- [ ] Program açıldı ve giriş yapıldı
- [ ] Masaüstü kısayolu oluşturuldu
