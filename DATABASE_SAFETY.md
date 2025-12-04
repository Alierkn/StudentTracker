# Veritabanı Güvenlik Dökümanı

## ⚠️ ÖNEMLİ: Veri Kaybı Önleme

Bu döküman, veritabanı verilerinin korunması için alınan güvenlik önlemlerini açıklar.

## 🔒 Güvenlik Önlemleri

### 1. `init_db()` Fonksiyonu Güvenliği

- ✅ **Sadece tablo oluşturur**: `CREATE TABLE IF NOT EXISTS` kullanır
- ✅ **Veri silmez**: Hiçbir `DELETE`, `DROP`, `TRUNCATE` işlemi yapılmaz
- ✅ **Mevcut veriler korunur**: Tablolar zaten varsa dokunmaz
- ✅ **Tekrar çağrı koruması**: Tablolar varsa gereksiz işlem yapmaz

### 2. Veri Kontrol Mekanizması

Her uygulama başlatıldığında:
- Mevcut öğrenci sayısı kontrol edilir
- Eğer öğrenci sayısı 0 ise uyarı verilir
- Veritabanı bağlantısı doğrulanır

### 3. Production Ortamı Kontrolleri

- Supabase bağlantısı her başlatmada kontrol edilir
- Veri durumu loglanır
- Hata durumunda uyarı verilir

## 🚨 Veri Kaybı Durumunda Kontrol Listesi

Eğer production'da veri kaybı yaşanıyorsa:

1. **Supabase Bağlantısını Kontrol Et**
   ```bash
   # .env dosyasındaki SUPABASE_DB_URL doğru mu?
   echo $SUPABASE_DB_URL
   ```

2. **Veritabanı Bağlantısını Test Et**
   ```python
   from database import get_db, USE_SUPABASE
   with get_db() as conn:
       c = conn.cursor()
       c.execute('SELECT COUNT(*) FROM students')
       print(c.fetchone())
   ```

3. **Log Dosyalarını İncele**
   - Uygulama başlatma loglarını kontrol et
   - "Mevcut öğrenci sayısı" mesajını ara
   - Hata mesajlarını kontrol et

4. **Supabase Dashboard'u Kontrol Et**
   - Supabase projesinde veriler var mı?
   - Doğru projeye bağlanıyor mu?
   - Connection string doğru mu?

## 📝 Kod Değişiklikleri

### `database.py`
- `init_db()` fonksiyonuna güvenlik notları eklendi
- Tablo kontrol mekanizması eklendi
- Tekrar çağrı koruması eklendi

### `student_tracker.py`
- Veri kontrol mekanizması eklendi
- Başlatma sırasında öğrenci sayısı kontrol edilir

### `gunicorn_config.py`
- Production başlatma sırasında veri kontrolü eklendi

## ⚡ Hızlı Çözüm

Eğer veri kaybı yaşanıyorsa:

1. **Supabase bağlantısını kontrol et**
2. **.env dosyasını doğrula**
3. **Supabase dashboard'da verileri kontrol et**
4. **Log dosyalarını incele**

## 🔍 Sorun Giderme

### Problem: Her build'de veriler kayboluyor

**Olası Nedenler:**
- Supabase bağlantı string'i yanlış
- Farklı bir Supabase projesine bağlanılıyor
- `.env` dosyası production'da yanlış yapılandırılmış

**Çözüm:**
1. Production ortamındaki `.env` dosyasını kontrol et
2. Supabase dashboard'da doğru projeyi kontrol et
3. Connection string'i doğrula

### Problem: init_db() verileri siliyor

**Açıklama:**
`init_db()` fonksiyonu **ASLA** veri silmez. Sadece tabloları oluşturur.

**Kontrol:**
- Kodda `DELETE`, `DROP`, `TRUNCATE` yok
- Sadece `CREATE TABLE IF NOT EXISTS` var
- Mevcut tablolara dokunmaz

## 📞 Destek

Sorun devam ederse:
1. Log dosyalarını paylaş
2. Supabase bağlantı bilgilerini kontrol et
3. Production ortamı yapılandırmasını gözden geçir

