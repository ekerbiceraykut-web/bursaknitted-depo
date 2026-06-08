# Bulut Kurulum Kılavuzu — Bursa Knitted Depo

## Ne Yapıyoruz?
Mac kapalı olsa bile herkesin sisteme girebilmesi için
uygulamayı internette 7/24 çalışan bir sunucuya taşıyoruz.

Maliyet: ~$7/ay (Render.com)

---

## Adım 1 — GitHub Hesabı Aç
1. https://github.com → Sign Up
2. E-posta ile kayıt ol

---

## Adım 2 — Kodu GitHub'a Yükle
1. https://github.com → New Repository → "bursaknitted-depo"
2. Bilgisayarda Terminal aç:

```bash
cd /Users/aykut/tekstil-stok
git init
git add .
git commit -m "ilk yükleme"
git remote add origin https://github.com/KULLANICI_ADI/bursaknitted-depo.git
git push -u origin main
```

---

## Adım 3 — Render.com'a Deploy Et
1. https://render.com → Sign Up (GitHub ile giriş yap)
2. "New +" → "Web Service"
3. GitHub reposunu seç → "bursaknitted-depo"
4. Şu ayarları gir:
   - **Name:** bursaknitted-depo
   - **Build Command:** `pip install -r cloud/requirements.txt`
   - **Start Command:** `gunicorn --chdir cloud app:application --bind 0.0.0.0:$PORT`
   - **Plan:** Starter ($7/ay)

5. "New +" → "PostgreSQL"
   - **Name:** bursaknitted-db
   - **Plan:** Free (90 gün ücretsiz, sonra $7/ay)

6. Web Service → Environment → DATABASE_URL:
   - PostgreSQL sayfasından "Internal Database URL" kopyala
   - Buraya yapıştır

7. "Deploy" butonuna bas → 3-5 dakika bekle

---

## Adım 4 — Mevcut Verileri Aktar
```bash
DATABASE_URL="postgresql://..." python cloud/migrate.py
```
(DATABASE_URL'yi Render'daki PostgreSQL sayfasından al)

---

## Adım 5 — Kullanıma Al
Render deploy tamamlanınca adres gelir:
`https://bursaknitted-depo.onrender.com`

Bu adresi tüm bilgisayar ve telefonlara verin.
Giriş: admin / admin123 (ilk girişte şifre değiştirin!)

---

## Masaüstü Uygulama Nasıl Çalışır?
- Mac'teki program yerel SQLite'ı kullanmaya devam eder
- Buluttaki web uygulama PostgreSQL kullanır
- İkisi bağımsız çalışır

İsterseniz masaüstü uygulamada "Buluta Aktar" butonu ekleriz,
böylece masaüstünde yapılan değişiklikler buluta da yansır.
