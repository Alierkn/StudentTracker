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
        init_db()
        print("✅ Veritabanı hazır.")
        if USE_SUPABASE:
            print("📁 Veritabanı: Supabase PostgreSQL")
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




