# 🔍 Supabase Bağlantı Kontrolü

## ❌ Sorun: DNS Çözümleme Hatası

Connection string'deki hostname çözümlenemiyor. Bu genellikle şu nedenlerden olur:

1. **Supabase projesi henüz tam deploy edilmemiş** (2-3 dakika bekleyin)
2. **Yanlış connection string** (Dashboard'dan tekrar kopyalayın)
3. **İnternet bağlantısı sorunu**

## ✅ Çözüm Adımları

### 1. Supabase Dashboard'dan Connection String'i Tekrar Alın

1. [Supabase Dashboard](https://supabase.com/dashboard) → Projenizi seçin
2. **Settings** > **Database**
3. **Connection string** bölümüne gidin
4. **URI** sekmesine tıklayın
5. Connection string'i **tam olarak** kopyalayın

**ÖNEMLİ:** Connection string formatı şöyle olmalı:
```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

veya

```
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### 2. Connection String Formatını Kontrol Edin

Mevcut connection string'iniz:
```
postgresql://postgres:E!ZHUR45pRf56.G@db.glduuxixobpdkvczkbxn.supabase.co:5432/postgres
```

**Dikkat:** Şifrede özel karakterler (`!`, `.`) var. Bu karakterler URL encoding gerektirebilir.

### 3. Şifreyi URL Encode Edin

Eğer şifrede özel karakterler varsa, bunları encode etmeniz gerekebilir:

- `!` → `%21`
- `.` → `%2E`

Veya Supabase Dashboard'dan **Connection pooling** kullanın (önerilen).

### 4. Connection Pooling Kullanın (Önerilen)

Supabase Dashboard > Settings > Database > Connection string > **Session mode** veya **Transaction mode** seçin.

Bu genellikle daha güvenilir bir bağlantı sağlar.

### 5. Alternatif: Direct Connection

Eğer pooler çalışmıyorsa, direct connection deneyin:

1. Dashboard > Settings > Database
2. **Connection string** > **Direct connection** seçin
3. Yeni connection string'i kopyalayın

## 🧪 Test

Connection string'i güncelledikten sonra:

```bash
cd /Users/alico/Downloads/student_tracker_system
source venv/bin/activate
python -c "
from dotenv import load_dotenv
load_dotenv()
from database import get_db, USE_SUPABASE
print('USE_SUPABASE:', USE_SUPABASE)
if USE_SUPABASE:
    try:
        with get_db() as conn:
            print('✅ Bağlantı başarılı!')
    except Exception as e:
        print(f'❌ Hata: {e}')
"
```

## 📝 Notlar

- Supabase projesi oluşturulduktan sonra 2-3 dakika bekleyin
- Connection string'deki şifreyi doğru kopyaladığınızdan emin olun
- Özel karakterler varsa URL encoding gerekebilir
- Connection pooling genellikle daha güvenilirdir

