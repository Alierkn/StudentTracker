# 🚀 EducationalTR Öğrenci Takip Sistemi - Deploy Kılavuzu

## 📋 Özet

Bu sistem Supabase PostgreSQL veritabanı kullanarak cloud'da çalışacak şekilde hazırlanmıştır.

## ⚠️ ÖNEMLİ: Netlify Hakkında

**Netlify server-side Python uygulamalarını (Flask, Django vb.) desteklemez.** Netlify sadece:
- Static websites
- Serverless functions (Node.js, Go)
- JAMstack uygulamaları

için uygundur.

**Flask uygulamanız için önerilen platformlar:**
- ✅ **Render.com** (En kolay, ücretsiz tier)
- ✅ **Railway.app** (Kolay, ücretsiz tier)
- ✅ **Fly.io** (Hızlı, ücretsiz tier)
- ✅ **Heroku** (Ücretli olabilir)

## 🎯 Adım Adım Deploy

### Adım 1: Supabase Projesi Oluştur (10 dakika)

1. [supabase.com](https://supabase.com) → Hesap oluştur
2. "New Project" → Proje bilgilerini gir
3. **Settings > API** → URL ve Key'leri kopyala
4. **Settings > Database** → Connection string'i kopyala

Detaylı adımlar için: `SUPABASE_SETUP.md`

### Adım 2: Local Test (5 dakika)

```bash
# .env dosyası oluştur
cp env.example .env

# .env dosyasını düzenle
nano .env  # Supabase bilgilerini gir

# Bağımlılıkları yükle
source venv/bin/activate
pip install -r requirements.txt

# Test et
python student_tracker.py
```

### Adım 3: GitHub'a Push (3 dakika)

```bash
git init
git add .
git commit -m "EducationalTR Student Tracker"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

### Adım 4: Render.com'a Deploy (10 dakika) ⭐ ÖNERİLEN

1. [render.com](https://render.com) → Sign Up (GitHub ile)
2. "New +" → "Web Service"
3. GitHub repo'nuzu seçin
4. Ayarlar:
   - **Name**: `educationaltr-student-tracker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn student_tracker:app --bind 0.0.0.0:$PORT`
5. **Environment Variables** ekle:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGc...
   SUPABASE_DB_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
   SECRET_KEY=your-random-secret-key
   ```
6. "Create Web Service" → Deploy başlar!

**✅ Hazır!** Render size bir URL verecek: `https://your-app.onrender.com`

### Alternatif: Railway.app

1. [railway.app](https://railway.app) → Sign Up
2. "New Project" → "Deploy from GitHub repo"
3. Repo'yu seçin
4. Environment Variables ekleyin (Render ile aynı)
5. Railway otomatik deploy eder!

## 🔐 Güvenlik

- ✅ `.env` dosyası `.gitignore`'da (GitHub'a gitmez)
- ✅ Şifreler hash'leniyor
- ✅ Session-based authentication
- ⚠️ Production'da güçlü `SECRET_KEY` kullanın
- ⚠️ Supabase Row Level Security (RLS) ayarlayın

## 📊 Veritabanı

- Tablolar ilk çalıştırmada otomatik oluşturulur
- Veya Supabase SQL Editor'dan manuel oluşturabilirsiniz
- Admin kullanıcısı otomatik oluşturulur (admin/admin123)

## 🐛 Sorun Giderme

**"USE_SUPABASE = False" görüyorum:**
- `.env` dosyasının doğru yerde olduğundan emin olun
- Environment variable'ların doğru yüklendiğini kontrol edin

**Bağlantı hatası:**
- Connection string formatını kontrol edin
- Supabase projenizin aktif olduğundan emin olun

**Deploy hatası:**
- Build log'ları kontrol edin
- Environment variable'ların doğru eklendiğinden emin olun

---

**Detaylı kılavuzlar:**
- `SUPABASE_SETUP.md` - Supabase kurulumu
- `DEPLOY.md` - Detaylı deploy bilgileri
- `QUICK_START.md` - Hızlı başlangıç




