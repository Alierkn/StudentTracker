# 🔧 Supabase Kurulum Kılavuzu

## 1. Supabase Projesi Oluşturma

1. [Supabase.com](https://supabase.com) adresine gidin
2. "Start your project" butonuna tıklayın
3. GitHub ile giriş yapın (veya email ile kayıt olun)
4. "New Project" butonuna tıklayın
5. Proje bilgilerini doldurun:
   - **Name**: `educationaltr-student-tracker` (veya istediğiniz isim)
   - **Database Password**: Güçlü bir şifre seçin (SAKLAYIN!)
   - **Region**: Size en yakın bölgeyi seçin
6. "Create new project" butonuna tıklayın
7. Projenin oluşturulmasını bekleyin (2-3 dakika)

## 2. Supabase Bağlantı Bilgilerini Alma

### Project URL ve API Key

1. Supabase Dashboard'da sol menüden **Settings** > **API**'ye gidin
2. Şu bilgileri kopyalayın:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public** key: `eyJhbGc...` (uzun bir string)

### Database Connection String

1. Sol menüden **Settings** > **Database**'e gidin
2. **Connection string** bölümüne gidin
3. **URI** sekmesine tıklayın
4. Connection string'i kopyalayın:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
5. `[YOUR-PASSWORD]` kısmını proje oluştururken girdiğiniz şifre ile değiştirin

## 3. Local Environment Ayarlama

1. Proje klasöründe `.env` dosyası oluşturun:
```bash
cd /Users/alico/Downloads/student_tracker_system
cp env.example .env
```

2. `.env` dosyasını düzenleyin ve Supabase bilgilerinizi girin:
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
SUPABASE_DB_URL=postgresql://postgres:your-password@db.xxxxx.supabase.co:5432/postgres
SECRET_KEY=your-random-secret-key-here
PORT=5002
```

3. `SECRET_KEY` için güvenli bir random string oluşturun:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 4. Bağımlılıkları Yükleme

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Veritabanını Başlatma

Uygulamayı ilk kez çalıştırdığınızda tablolar otomatik oluşturulacak:

```bash
python student_tracker.py
```

Veya manuel olarak Supabase SQL Editor'dan oluşturabilirsiniz:

1. Supabase Dashboard > **SQL Editor**
2. `database.py` dosyasındaki CREATE TABLE komutlarını kopyalayıp çalıştırın

## 6. Test Etme

1. Uygulamayı başlatın: `python student_tracker.py`
2. Tarayıcıda açın: `http://localhost:5002`
3. Admin hesabı ile giriş yapın:
   - Username: `admin`
   - Password: `admin123`

## ✅ Başarı Kontrolü

- ✅ Uygulama başladığında "Veritabanı: Supabase PostgreSQL" mesajını görmelisiniz
- ✅ Giriş yapabiliyorsanız bağlantı başarılı
- ✅ Çalışma kaydı ekleyebiliyorsanız veritabanı çalışıyor

## 🐛 Sorun Giderme

**"USE_SUPABASE = False" görüyorum:**
- `.env` dosyasının doğru yerde olduğundan emin olun
- Environment variable'ların doğru yüklendiğini kontrol edin

**Bağlantı hatası:**
- `SUPABASE_DB_URL` formatını kontrol edin
- Şifrenin doğru olduğundan emin olun
- Supabase projenizin aktif olduğundan emin olun

**Tablolar oluşmuyor:**
- Supabase SQL Editor'dan manuel oluşturun
- Veya uygulamayı bir kez çalıştırın (otomatik oluşturur)

