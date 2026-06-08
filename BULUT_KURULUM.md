# Bulut Kurulum — Mac Kapalıyken de Çalışır

Toplam süre: ~20 dakika
Maliyet: ~$7/ay (Render.com)

---

## ADIM 1 — GitHub Hesabı (ücretsiz)

1. https://github.com → **Sign Up**
2. E-posta ve şifre gir → hesap aç
3. E-postayı doğrula

---

## ADIM 2 — Kodu GitHub'a Yükle

Mac'te **Terminal** aç (Spotlight → Terminal):

```bash
cd /Users/aykut/tekstil-stok

git init
git add .
git commit -m "Bursa Knitted Depo ilk yükleme"
```

GitHub'da yeni repo oluştur:
- https://github.com → **"+"** → **New repository**
- Repository name: `bursaknitted-depo`
- **Private** seç → **Create repository**

Sonra terminale:
```bash
git remote add origin https://github.com/SENIN_KULLANICI_ADIN/bursaknitted-depo.git
git branch -M main
git push -u origin main
```
(GitHub kullanıcı adı ve şifre sorabilir)

---

## ADIM 3 — Render.com'da Hesap Aç

1. https://render.com → **Get Started for Free**
2. **GitHub ile giriş yap** (en kolay yol)

---

## ADIM 4 — PostgreSQL Veritabanı Oluştur

1. Render Dashboard → **New +** → **PostgreSQL**
2. Şu bilgileri gir:
   - **Name:** `bursaknitted-db`
   - **Plan:** Free (90 gün ücretsiz, sonra $7/ay)
3. **Create Database** → Oluşmasını bekle (1-2 dk)
4. Açılan sayfada **"Internal Database URL"** yi kopyala → not al

---

## ADIM 5 — Web Servisi Oluştur

1. Render Dashboard → **New +** → **Web Service**
2. **Connect a repository** → GitHub repo'nu seç → `bursaknitted-depo`
3. Şu bilgileri gir:
   - **Name:** `bursaknitted-depo`
   - **Runtime:** Python
   - **Build Command:** `pip install -r cloud/requirements.txt`
   - **Start Command:** `python cloud/server.py`
   - **Plan:** Starter ($7/ay)
4. **Environment Variables** bölümüne ekle:
   - Key: `DATABASE_URL`  → Value: (4. adımda kopyaladığın URL)
5. **Create Web Service** → Deploy başlar (3-5 dk)
6. Deploy tamamlanınca URL görünür:
   `https://bursaknitted-depo.onrender.com`

---

## ADIM 6 — Mevcut Verileri Aktar

Mac'te Terminal'de:
```bash
cd /Users/aykut/tekstil-stok
DATABASE_URL="postgresql://ADRESIN" python3 cloud/migrate.py
```
(DATABASE_URL'yi 4. adımdaki URL ile değiştir)

---

## ADIM 7 — Programı Buluta Bağla

Masaüstü programı aç → Giriş ekranında:
- **"🌐 Sunucuya Bağlan"** seç
- Sunucu adresi: `https://bursaknitted-depo.onrender.com`
- admin / admin123 ile giriş

**Bu adresi tüm bilgisayarlara ver.**

---

## Sonuç

```
Render.com (7/24 açık)
    └── PostgreSQL veritabanı
         ├── Ana Mac masaüstü programı
         ├── PC-1
         ├── PC-2
         └── Telefon (mobil web arayüzü)
```

Mac açık/kapalı fark etmez.
Herkes kendi şifresiyle girer.
Tüm veriler bulutta güvende.

---

## Aylık Maliyet

| Servis | Plan | Ücret |
|--------|------|-------|
| Web Service | Starter | $7/ay |
| PostgreSQL | Free→Paid | $0→$7/ay |
| **Toplam** | | **~$7-14/ay** |

(İlk 90 gün PostgreSQL ücretsiz = ilk 90 gün $7/ay)
