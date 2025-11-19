# 📚 Öğrenci Çalışma Takip Sistemi

Modern, kullanıcı dostu ve görsel olarak çekici bir öğrenci çalışma takip sistemi. Öğrencilerin günlük çalışma verilerini, sınav sonuçlarını ve gelişimlerini takip eder.

## ✨ Özellikler

### Öğrenci Özellikleri
- ✅ **Günlük Çalışma Kaydı**: Ne çalıştığınızı, kaç saat çalıştığınızı ve verimliliğinizi kaydedin
- ✅ **Verimlilik Takibi**: Her çalışma için verimlilik değerlendirmesi (0-100%)
- ✅ **Zorluk Takibi**: Anlamadığınız yerleri not edin
- ✅ **Sınav Sonuçları**: Sınav notlarınızı kaydedin ve ortalamanızı takip edin
- ✅ **Grafiksel Gelişim**: 
  - Günlük çalışma saatleri grafiği
  - Ders bazında çalışma dağılımı
  - Verimlilik trendi
- ✅ **Ortalama Hesaplayıcı**: Hedef ortalamaya ulaşmak için gerekli notları hesaplayın
- ✅ **İstatistikler**: Toplam çalışma, saat, verimlilik ve sınav ortalaması

### Admin Özellikleri
- ✅ **Tüm Öğrencileri Görüntüleme**: Tüm öğrencilerin çalışma verilerini görüntüleyin
- ✅ **Detaylı Raporlar**: Her öğrencinin detaylı çalışma kayıtları ve sınav sonuçları
- ✅ **İstatistikler**: Öğrenci bazında toplam istatistikler

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+
- Supabase hesabı (cloud deploy için)
- SQLite3 (local development için - Python ile birlikte gelir)

### Local Development (SQLite)

1. **Virtual environment oluşturun ve aktif edin:**
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux için
```

2. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

3. **Uygulamayı başlatın:**
```bash
python student_tracker.py
```

4. **Tarayıcınızda açın:**
```
http://localhost:5002
```

### Supabase ile Kurulum (Production)

Detaylı kurulum için `SUPABASE_SETUP.md` dosyasına bakın.

**Hızlı Başlangıç:**
1. Supabase projesi oluşturun
2. `.env` dosyasını oluşturun ve Supabase bilgilerinizi girin
3. `pip install -r requirements.txt`
4. `python student_tracker.py`

## 👤 Varsayılan Admin Hesabı

İlk çalıştırmada otomatik olarak oluşturulur:
- **Kullanıcı Adı:** `admin`
- **Şifre:** `admin123`

⚠️ **Güvenlik için ilk girişten sonra şifreyi değiştirmeniz önerilir!**

## 📖 Kullanım

### Öğrenci Olarak Kayıt Olma

1. Ana sayfada "Kayıt Ol" butonuna tıklayın
2. Kullanıcı adı, ad soyad ve şifre bilgilerinizi girin
3. Giriş yapın

### Çalışma Kaydı Ekleme

1. Dashboard'dan "Çalışma Ekle" butonuna tıklayın
2. Formu doldurun:
   - **Tarih**: Çalışma tarihi
   - **Ders/Konu**: Çalıştığınız ders veya konu
   - **Süre**: Kaç saat çalıştığınız (örn: 2.5)
   - **Verimlilik**: Slider ile verimliliğinizi belirleyin (0-100%)
   - **Notlar**: Çalıştığınız konular, önemli noktalar
   - **Zorluklar**: Anlamadığınız yerler

### Sınav Sonucu Ekleme

1. Dashboard'dan "Sınav Ekle" butonuna tıklayın
2. Formu doldurun:
   - **Sınav Adı**: Örn: "Matematik Vize 1"
   - **Aldığınız Not**: Sınavdan aldığınız puan
   - **Maksimum Not**: Varsayılan 100
   - **Sınav Tarihi**: Opsiyonel

### Ortalama Hesaplayıcı

1. Dashboard'da "Ortalama Hesaplayıcı" bölümüne gidin
2. Hedef ortalamanızı girin (0-100)
3. Kalan sınav sayısını girin
4. "Hesapla" butonuna tıklayın
5. Sistem size kalan sınavlardan ortalama kaç almanız gerektiğini söyleyecek

### Admin Paneli

1. Admin hesabı ile giriş yapın
2. "Admin Panel" menüsüne tıklayın
3. Tüm öğrencilerin istatistiklerini görüntüleyin
4. Her öğrencinin detaylarını görmek için "Detayları Gör" butonuna tıklayın

## 📊 Grafikler

Dashboard'da 3 farklı grafik bulunur:

1. **Günlük Çalışma Saatleri**: Son 30 günün günlük çalışma saatleri
2. **Ders Bazında Çalışma**: Hangi derslere ne kadar zaman harcadığınız
3. **Verimlilik Trendi**: Haftalık verimlilik ortalamaları

## 🎨 Tasarım Özellikleri

- Modern ve genç tasarım
- Gradient arka planlar
- Smooth animasyonlar
- Responsive (mobil uyumlu)
- Kullanıcı dostu arayüz
- Renkli istatistik kartları
- İnteraktif grafikler (Chart.js)

## 🔒 Güvenlik

- Şifreler hash'lenerek saklanır (Werkzeug)
- Session tabanlı kimlik doğrulama
- Admin yetkisi kontrolü
- SQL injection koruması (parametreli sorgular)

## 📁 Dosya Yapısı

```
student_tracker_system/
├── student_tracker.py          # Ana Flask uygulaması
├── student_tracker.db          # SQLite veritabanı (otomatik oluşturulur)
├── requirements.txt            # Python bağımlılıkları
├── README.md                   # Bu dosya
├── templates/
│   ├── base.html              # Ana şablon
│   ├── login.html             # Giriş sayfası
│   ├── register.html          # Kayıt sayfası
│   ├── dashboard.html         # Öğrenci dashboard
│   ├── add_study.html         # Çalışma ekleme
│   ├── add_exam.html          # Sınav ekleme
│   ├── admin_dashboard.html   # Admin paneli
│   └── admin_student_detail.html # Öğrenci detay
└── static/
    ├── style.css              # CSS stilleri
    └── script.js               # JavaScript
```

## 🛠️ Geliştirme

### Veritabanı Yapısı

**students** tablosu:
- id, username, password, full_name, email, created_at, is_admin

**study_sessions** tablosu:
- id, student_id, date, subject, hours, efficiency, notes, difficulties, created_at

**exam_results** tablosu:
- id, student_id, exam_name, score, max_score, exam_date, created_at

### Port Değiştirme

Port'u değiştirmek için environment variable kullanın:
```bash
export PORT=5003
python student_tracker.py
```

Veya kod içinde `student_tracker.py` dosyasında port numarasını değiştirin.

## 📝 Notlar

- Veritabanı ilk çalıştırmada otomatik oluşturulur
- Tüm veriler SQLite veritabanında saklanır
- Grafikler Chart.js kütüphanesi ile oluşturulur
- Sistem tamamen Türkçe'dir

## 🐛 Sorun Giderme

**Veritabanı hatası:**
- `student_tracker.db` dosyasını silin ve uygulamayı yeniden başlatın

**Port zaten kullanılıyor:**
- Farklı bir port numarası kullanın veya çalışan uygulamayı durdurun

**Grafikler görünmüyor:**
- İnternet bağlantınızı kontrol edin (Chart.js CDN'den yüklenir)
- Tarayıcı konsolunu kontrol edin

---

**Geliştirici:** Ali Erkan Ocaklı  
**Versiyon:** 1.0  
**Lisans:** MIT

