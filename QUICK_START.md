# ⚡ Hızlı Başlangıç - Supabase Deploy

## 1️⃣ Supabase Projesi Oluştur (5 dakika)

1. [supabase.com](https://supabase.com) → Sign Up
2. New Project → Proje adı ve şifre gir
3. Settings > API → URL ve Key'leri kopyala
4. Settings > Database → Connection string'i kopyala

## 2️⃣ Local Test (2 dakika)

```bash
# .env dosyası oluştur
cp env.example .env

# .env dosyasını düzenle (Supabase bilgilerini gir)
nano .env  # veya istediğiniz editör

# Bağımlılıkları yükle
source venv/bin/activate
pip install -r requirements.txt

# Çalıştır
python student_tracker.py
```

## 3️⃣ GitHub'a Push (3 dakika)

```bash
git init
git add .
git commit -m "EducationalTR Student Tracker - Supabase"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## 4️⃣ Render.com'a Deploy (5 dakika)

1. [render.com](https://render.com) → Sign Up
2. New + → Web Service
3. GitHub repo'yu bağla
4. Ayarlar:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn student_tracker:app --bind 0.0.0.0:$PORT`
5. Environment Variables ekle:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_DB_URL`
   - `SECRET_KEY`
6. Create Web Service

## ✅ Hazır!

Uygulamanız canlıda! Render size bir URL verecek (örn: `https://your-app.onrender.com`)

---

**Not:** Netlify Flask uygulamalarını desteklemez. Render, Railway veya Fly.io kullanın.

