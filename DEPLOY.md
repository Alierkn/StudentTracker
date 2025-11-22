# 🚀 EducationalTR Öğrenci Takip Sistemi - Deploy Kılavuzu

Bu kılavuz, uygulamayı Supabase ve cloud platformlara deploy etmek için adımları içerir.

## 📋 Ön Hazırlık

### 1. Supabase Projesi Oluşturma

1. [Supabase](https://supabase.com) hesabı oluşturun
2. Yeni bir proje oluşturun
3. Proje ayarlarından şu bilgileri alın:
   - **Project URL**: Settings > API > Project URL
   - **Anon Key**: Settings > API > anon public key
   - **Database Password**: Settings > Database > Database password
   - **Connection String**: Settings > Database > Connection string

### 2. Environment Variables Ayarlama

`.env.example` dosyasını `.env` olarak kopyalayın ve değerleri doldurun:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_DB_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
SECRET_KEY=your-secret-key-here
```

## 🌐 Deploy Seçenekleri

### ⚠️ ÖNEMLİ: Netlify Hakkında

**Netlify server-side Python uygulamalarını desteklemez.** Flask gibi backend framework'leri için Netlify uygun değildir.

**Önerilen Alternatifler:**
- ✅ **Render.com** (Ücretsiz tier mevcut)
- ✅ **Railway.app** (Ücretsiz tier mevcut)
- ✅ **Fly.io** (Ücretsiz tier mevcut)
- ✅ **Vercel** (Serverless functions ile)

### Seçenek 1: Render.com (Önerilen)

1. [Render.com](https://render.com) hesabı oluşturun
2. "New +" → "Web Service" seçin
3. GitHub repo'nuzu bağlayın
4. Ayarlar:
   - **Name**: `educationaltr-student-tracker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn student_tracker:app --bind 0.0.0.0:$PORT`
   - **Environment Variables**:
     - `SUPABASE_URL`: Supabase project URL
     - `SUPABASE_KEY`: Supabase anon key
     - `SUPABASE_DB_URL`: PostgreSQL connection string
     - `SECRET_KEY`: Güvenli bir random string
     - `PORT`: Render otomatik atar

5. "Create Web Service" butonuna tıklayın

### Seçenek 2: Railway.app

1. [Railway.app](https://railway.app) hesabı oluşturun
2. "New Project" → "Deploy from GitHub repo"
3. Repo'nuzu seçin
4. Railway otomatik olarak `Procfile`'ı kullanır
5. Environment Variables ekleyin:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_DB_URL`
   - `SECRET_KEY`

### Seçenek 3: Fly.io

1. [Fly.io](https://fly.io) CLI kurun
2. Terminal'de:
```bash
fly launch
fly secrets set SUPABASE_URL=your-url
fly secrets set SUPABASE_KEY=your-key
fly secrets set SUPABASE_DB_URL=your-connection-string
fly secrets set SECRET_KEY=your-secret-key
fly deploy
```

## 📝 GitHub'a Push

```bash
cd /Users/alico/Downloads/student_tracker_system
git init
git add .
git commit -m "EducationalTR Öğrenci Takip Sistemi - Supabase entegrasyonu"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## 🔧 Veritabanı Kurulumu

Deploy edildikten sonra, uygulama ilk çalıştığında otomatik olarak tabloları oluşturacak. Eğer manuel kurulum isterseniz:

1. Supabase Dashboard > SQL Editor'a gidin
2. `database.py` dosyasındaki CREATE TABLE komutlarını çalıştırın
3. Veya uygulamayı bir kez çalıştırın (otomatik oluşturur)

## ✅ Deploy Sonrası Kontrol

1. Uygulama URL'ini açın
2. Admin hesabı ile giriş yapın:
   - Username: `admin`
   - Password: `admin123`
3. İlk girişten sonra şifreyi değiştirmeyi unutmayın!

## 🔒 Güvenlik Notları

- `.env` dosyasını **ASLA** GitHub'a push etmeyin
- `.gitignore` dosyasında `.env` zaten var
- Production'da güçlü bir `SECRET_KEY` kullanın
- Supabase Row Level Security (RLS) politikalarını ayarlayın

## 📞 Sorun Giderme

**Veritabanı bağlantı hatası:**
- `SUPABASE_DB_URL` formatını kontrol edin
- Supabase dashboard'dan connection string'i kopyalayın

**Tablolar oluşmuyor:**
- Supabase SQL Editor'dan manuel oluşturun
- Veya uygulamayı bir kez çalıştırın

**Port hatası:**
- Cloud platformlar genelde `PORT` environment variable kullanır
- `Procfile` veya start command'da `$PORT` kullanın

---

**Geliştirici:** EducationalTR  
**Versiyon:** 2.0 (Supabase Edition)




