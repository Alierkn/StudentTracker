# Veritabanı Geri Yükleme Rehberi

## Durum
Öğrenci kayıtları ve çalışma verileri kaybolmuş görünüyor. Bu rehber ile verileri geri yükleyebilirsiniz.

## Seçenek 1: Yedek Dosyadan Geri Yükleme

Eğer bir yedek dosyanız varsa:

```bash
python restore_from_backup.py restore <yedek_dosya.db>
```

Örnek:
```bash
python restore_from_backup.py restore student_tracker.db.backup
```

## Seçenek 2: Başka Bir SQLite Dosyasından Import

Eğer veriler başka bir SQLite dosyasında varsa:

```bash
python restore_from_backup.py import <kaynak_dosya.db>
```

Örnek:
```bash
python restore_from_backup.py import old_database.db
```

## Seçenek 3: Supabase'den Geri Yükleme

Eğer Supabase'de veriler varsa (şu anda yok görünüyor), `migrate_to_supabase.py` script'ini tersine çalıştırabiliriz.

## Yedek Dosya Arama

Yedek dosyaları bulmak için:

```bash
# Downloads klasöründe .db dosyalarını ara
find ~/Downloads -name "*.db" -type f

# Tüm sistemde student_tracker ile ilgili dosyaları ara
find ~ -name "*student_tracker*" -type f 2>/dev/null
```

## Önemli Notlar

1. **Yedek Alın**: Geri yüklemeden önce mevcut veritabanı otomatik olarak yedeklenir.
2. **Admin Kullanıcısı**: Admin kullanıcısı korunur, sadece öğrenci verileri geri yüklenir.
3. **Veri Kontrolü**: Geri yükleme sonrası verileri kontrol edin.

## Eğer Yedek Yoksa

Eğer hiç yedek yoksa:
- Öğrencilerin yeniden kayıt olması gerekecek
- Çalışma kayıtları ve sınav sonuçları manuel olarak tekrar girilmeli

## Yardım

Sorun yaşıyorsanız, script'i çalıştırırken hata mesajlarını paylaşın.

