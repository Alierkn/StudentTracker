# 🔧 Internal Server Error - Sorun Giderme

## ❌ Hata

Deploy sonrası "Internal Server Error" alıyorsunuz.

## 🔍 Olası Nedenler ve Çözümler

### 1. Environment Variables Eksik

**Kontrol:** Render.com/Railway Dashboard → Environment Variables

**Gerekli Variables:**
```
SUPABASE_URL=https://glduuxixobpdkvczkbxn.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdsZHV1eGl4b2JwZGt2Y3prYnhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1MTUxNjEsImV4cCI6MjA3OTA5MTE2MX0.eTcOuKD3s1OPrCsf5h2Kesd3K8hFf0fLzDFtL0T2NpU
SUPABASE_DB_URL=postgresql://postgres.glduuxixobpdkvczkbxn:E%21ZHUR45pRf56%2EG@aws-1-eu-central-2.pooler.supabase.com:5432/postgres
SECRET_KEY=fe4d0a6157e83f6f61e0610eff8ccbb9467daeeec59adaf60d7060c34b99ec06
```

**Çözüm:** Tüm environment variables'ı ekleyin ve deploy'u yeniden başlatın.

### 2. Veritabanı Bağlantı Hatası

**Kontrol:** Log'larda "could not translate host name" veya "connection refused" hatası var mı?

**Çözüm:**
- `SUPABASE_DB_URL` formatını kontrol edin
- Connection string'deki şifreyi doğru URL encode ettiğinizden emin olun
- Supabase projenizin aktif olduğundan emin olun

### 3. Import Hatası

**Kontrol:** Log'larda "ModuleNotFoundError" veya "ImportError" var mı?

**Çözüm:**
- `requirements.txt` dosyasının doğru olduğundan emin olun
- Build log'larını kontrol edin
- Tüm bağımlılıkların yüklendiğinden emin olun

### 4. Debug Mode Açın (Geçici)

Hata mesajlarını görmek için:

**Render.com:**
1. Dashboard → Environment Variables
2. Yeni variable ekle: `FLASK_DEBUG=True`
3. Deploy'u yeniden başlat

**Railway:**
1. Variables sekmesi
2. `FLASK_DEBUG=True` ekle
3. Redeploy

**⚠️ Dikkat:** Production'da debug mode'u açık bırakmayın!

### 5. Log'ları Kontrol Edin

**Render.com:**
- Dashboard → Logs sekmesi
- Hata mesajlarını okuyun

**Railway:**
- Deployments → Logs
- Hata mesajlarını okuyun

### 6. Veritabanı Tabloları Oluşturulmamış

**Kontrol:** İlk çalıştırmada tablolar otomatik oluşturulmalı.

**Çözüm:** Eğer tablolar yoksa, Supabase SQL Editor'dan manuel oluşturun veya uygulamayı bir kez çalıştırın.

## 🧪 Test Adımları

1. ✅ Environment variables'ı kontrol edin
2. ✅ Log'ları okuyun
3. ✅ Supabase bağlantısını test edin
4. ✅ Build log'larını kontrol edin
5. ✅ Deploy'u yeniden başlatın

## 📝 Hata Mesajını Paylaşın

Eğer sorun devam ederse, lütfen şu bilgileri paylaşın:

1. **Platform:** Render.com / Railway.app / Diğer?
2. **Log mesajları:** Hata detayları
3. **Environment variables:** Hangi variables eklendi?
4. **Build log:** Build başarılı mı?

Bu bilgilerle daha hızlı çözüm bulabiliriz!

