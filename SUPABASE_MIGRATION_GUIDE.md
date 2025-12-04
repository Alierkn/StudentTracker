# 🔄 Supabase Migration Kılavuzu - Streak Kolonları

## 📋 Migration İçeriği

Bu migration, `students` tablosuna şu kolonları ekler:
- `current_streak`: Mevcut üst üste çalışma günü sayısı (INTEGER, DEFAULT 0)
- `longest_streak`: En uzun üst üste çalışma günü sayısı (INTEGER, DEFAULT 0)
- `last_study_date`: Son çalışma tarihi (DATE, NULL)

## 🚀 Migration Adımları

### Yöntem 1: Supabase SQL Editor (Önerilen)

1. **Supabase Dashboard'a gidin:**
   - https://supabase.com/dashboard
   - Projenizi seçin: `glduuxixobpdkvczkbxn`

2. **SQL Editor'ı açın:**
   - Sol menüden **SQL Editor** → **New Query**

3. **Migration SQL'ini çalıştırın:**
   - `supabase_migration.sql` dosyasındaki tüm SQL'i kopyalayın
   - SQL Editor'a yapıştırın
   - **Run** butonuna tıklayın

4. **Sonucu kontrol edin:**
   - "✅ current_streak kolonu eklendi" mesajlarını görmelisiniz
   - En alttaki SELECT sorgusu kolonları gösterecek

### Yöntem 2: Migration Script (Alternatif)

Eğer Railway/Render'da terminal erişiminiz varsa:

```bash
python add_streak_columns.py --auto
```

## ✅ Migration Sonrası Kontrol

### 1. Kolonların Varlığını Kontrol Edin

Supabase SQL Editor'dan:

```sql
SELECT 
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns
WHERE table_name = 'students'
AND column_name IN ('current_streak', 'longest_streak', 'last_study_date')
ORDER BY column_name;
```

**Beklenen Sonuç:**
```
column_name      | data_type | column_default
-----------------+-----------+---------------
current_streak   | integer   | 0
last_study_date  | date      | null
longest_streak   | integer   | 0
```

### 2. Mevcut Öğrencileri Güncelleyin (Opsiyonel)

Eğer mevcut öğrencilerin streak'lerini hesaplamak isterseniz:

```sql
-- Mevcut öğrenciler için streak hesaplama (opsiyonel)
UPDATE students s
SET 
    current_streak = COALESCE((
        SELECT COUNT(DISTINCT date)
        FROM study_sessions ss
        WHERE ss.student_id = s.id
        AND ss.date >= CURRENT_DATE - INTERVAL '30 days'
    ), 0),
    longest_streak = COALESCE((
        SELECT COUNT(DISTINCT date)
        FROM study_sessions ss
        WHERE ss.student_id = s.id
    ), 0),
    last_study_date = (
        SELECT MAX(date)
        FROM study_sessions ss
        WHERE ss.student_id = s.id
    )
WHERE EXISTS (
    SELECT 1 FROM study_sessions ss WHERE ss.student_id = s.id
);
```

## 🐛 Sorun Giderme

### Hata: "column already exists"

**Çözüm:** Kolonlar zaten eklenmiş. Migration'ı tekrar çalıştırmaya gerek yok.

### Hata: "permission denied"

**Çözüm:** Supabase Dashboard'dan SQL Editor'ı kullanın (doğru yetkilere sahipsiniz).

### Kolonlar görünmüyor

**Çözüm:**
1. Sayfayı yenileyin
2. Table Editor'dan `students` tablosunu kontrol edin
3. Migration'ı tekrar çalıştırın

## 📝 Notlar

- Migration **idempotent**'tir (birden fazla kez çalıştırılabilir)
- Mevcut veriler korunur
- Yeni kolonlar varsayılan değerlerle eklenir (0 veya NULL)
- Migration sadece bir kez yapılmalıdır

## ✅ Migration Tamamlandı mı?

Migration başarılı olduysa:
- ✅ 3 kolon eklendi
- ✅ Varsayılan değerler ayarlandı
- ✅ Mevcut veriler korundu
- ✅ Uygulama streak özelliklerini kullanabilir

---

**Son Güncelleme:** 2025-12-04

