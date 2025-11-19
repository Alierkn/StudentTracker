# 🔧 Environment Variables Kurulumu

Supabase projeniz hazır! Şimdi `.env` dosyasını oluşturmanız gerekiyor.

## Adımlar

### 1. .env Dosyası Oluşturun

Terminal'de şu komutu çalıştırın:

```bash
cd /Users/alico/Downloads/student_tracker_system
cp env.example .env
```

### 2. .env Dosyasını Düzenleyin

`.env` dosyasını açın ve şu bilgileri doldurun:

```env
# Supabase Bağlantı Bilgileri
SUPABASE_URL=https://glduuxixobpdkvczkbxn.supabase.co
SUPABASE_KEY=YOUR_ANON_KEY_HERE

# PostgreSQL Connection String
# Supabase Dashboard > Settings > Database > Connection string > URI
# [YOUR-PASSWORD] kısmını proje oluştururken girdiğiniz database şifresi ile değiştirin
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.glduuxixobpdkvczkbxn.supabase.co:5432/postgres

# Flask Secret Key (güvenli bir random string)
# Terminal'de şu komutu çalıştırarak oluşturabilirsiniz:
# python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-random-secret-key-here

# Port
PORT=5002
```

### 3. Eksik Bilgileri Bulun

#### SUPABASE_KEY (Anon Key)

1. [Supabase Dashboard](https://supabase.com/dashboard) → Projenizi seçin
2. Sol menüden **Settings** > **API**
3. **anon public** key'i kopyalayın (uzun bir string, `eyJhbGc...` ile başlar)

#### SUPABASE_DB_URL (Database Connection String)

1. Supabase Dashboard → **Settings** > **Database**
2. **Connection string** bölümüne gidin
3. **URI** sekmesine tıklayın
4. Connection string'i kopyalayın:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.glduuxixobpdkvczkbxn.supabase.co:5432/postgres
   ```
5. `[YOUR-PASSWORD]` kısmını proje oluştururken girdiğiniz **database password** ile değiştirin

#### SECRET_KEY

Terminal'de şu komutu çalıştırın:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Çıkan string'i `SECRET_KEY` olarak kullanın.

### 4. Test Edin

```bash
# Virtual environment'ı aktif edin
source venv/bin/activate

# Bağımlılıkları yükleyin (eğer yüklemediyseniz)
pip install -r requirements.txt

# Uygulamayı başlatın
python student_tracker.py
```

Başarılı olursa şu mesajı görmelisiniz:
```
📚 Öğrenci Çalışma Takip Sistemi - EducationalTR
============================================================
🌐 Uygulama başlatılıyor: http://0.0.0.0:5002
📁 Veritabanı: Supabase PostgreSQL
============================================================
```

### 5. Tarayıcıda Test

1. `http://localhost:5002` adresini açın
2. Admin hesabı ile giriş yapın:
   - Username: `admin`
   - Password: `admin123`

## ✅ Başarı Kontrolü

- ✅ Uygulama başladığında "Veritabanı: Supabase PostgreSQL" mesajını görüyorsanız → Başarılı!
- ✅ Giriş yapabiliyorsanız → Bağlantı çalışıyor!
- ✅ Çalışma kaydı ekleyebiliyorsanız → Veritabanı hazır!

## 🐛 Sorun Giderme

**"USE_SUPABASE = False" görüyorum:**
- `.env` dosyasının doğru yerde olduğundan emin olun (`/Users/alico/Downloads/student_tracker_system/.env`)
- Environment variable'ların doğru yüklendiğini kontrol edin

**Bağlantı hatası:**
- `SUPABASE_DB_URL` formatını kontrol edin
- Database password'un doğru olduğundan emin olun
- Supabase projenizin aktif olduğundan emin olun

**Tablolar oluşmuyor:**
- Uygulamayı bir kez çalıştırın (otomatik oluşturur)
- Veya Supabase SQL Editor'dan manuel oluşturun

