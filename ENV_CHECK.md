# 🔍 Environment Variables Kontrolü

## ❌ Sorun

Log'larda `sqlite3.OperationalError: no such table: students` hatası görülüyor. Bu, uygulamanın SQLite kullandığını ve Supabase'e bağlanamadığını gösteriyor.

## ✅ Çözüm

### 1. Environment Variables'ı Kontrol Edin

Render.com/Railway Dashboard → **Environment Variables** bölümünde şunlar olmalı:

```
SUPABASE_URL=https://glduuxixobpdkvczkbxn.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdsZHV1eGl4b2JwZGt2Y3prYnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MTUxNjEsImV4cCI6MjA3OTA5MTE2MX0.eTcOuKD3s1OPrCsf5h2Kesd3K8hFf0fLzDFtL0T2NpU
SUPABASE_DB_URL=postgresql://postgres.glduuxixobpdkvczkbxn:E%21ZHUR45pRf56%2EG@aws-1-eu-central-2.pooler.supabase.com:5432/postgres
SECRET_KEY=fe4d0a6157e83f6f61e0610eff8ccbb9467daeeec59adaf60d7060c34b99ec06
```

### 2. Deploy'u Yeniden Başlatın

Environment variables'ı ekledikten sonra:
- **Render.com**: "Manual Deploy" → "Deploy latest commit"
- **Railway**: "Redeploy"

### 3. Log'ları Kontrol Edin

Deploy sonrası log'larda şunu görmelisiniz:

```
🔄 Veritabanı başlatılıyor...
✅ Veritabanı hazır.
📁 Veritabanı: Supabase PostgreSQL
```

Eğer `📁 Veritabanı: SQLite (Local)` görüyorsanız, environment variables doğru yüklenmemiş demektir.

### 4. Environment Variables Formatı

**ÖNEMLİ:** Her variable'ı ayrı ayrı ekleyin:
- Variable Name: `SUPABASE_URL`
- Value: `https://glduuxixobpdkvczkbxn.supabase.co`

**Dikkat:**
- Boşluk olmamalı
- Tırnak işareti olmamalı
- Her satır bir variable

### 5. Test

Deploy sonrası siteyi açın. Artık çalışmalı!

## 🐛 Hala Çalışmıyorsa

1. Log'larda "📁 Veritabanı: Supabase PostgreSQL" mesajını görüyor musunuz?
2. Environment variables'ı tek tek kontrol edin
3. Deploy'u yeniden başlatın
4. Log'ları paylaşın




