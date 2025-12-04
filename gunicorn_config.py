"""
Gunicorn configuration file
"""

import os
from database import init_db, USE_SUPABASE

def on_starting(server):
    """Gunicorn başlatılırken çalışır"""
    print("=" * 60)
    print("🚀 Gunicorn başlatılıyor...")
    print("=" * 60)
    
    try:
        print("🔄 Veritabanı başlatılıyor...")
        # init_db() sadece tabloları oluşturur, mevcut verilere dokunmaz
        init_db()
        print("✅ Veritabanı hazır.")
        if USE_SUPABASE:
            print("📁 Veritabanı: Supabase PostgreSQL")
            # Veri kontrolü
            try:
                from database import get_db
                from psycopg2.extras import RealDictCursor
                with get_db() as conn:
                    c = conn.cursor(cursor_factory=RealDictCursor)
                    c.execute('SELECT COUNT(*) as count FROM students')
                    result = c.fetchone()
                    if result:
                        count = result.get('count', 0) if isinstance(result, dict) else result[0]
                        print(f"📊 Mevcut öğrenci sayısı: {count}")
                        if count == 0:
                            print("⚠️  UYARI: Veritabanında öğrenci bulunamadı!")
            except Exception as check_err:
                print(f"⚠️  Veri kontrolü hatası: {check_err}")
        else:
            print("📁 Veritabanı: SQLite (Local)")
    except Exception as e:
        print(f"⚠️  Veritabanı başlatma uyarısı: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

# Gunicorn ayarları
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 2
worker_class = "sync"
timeout = 120
keepalive = 5




