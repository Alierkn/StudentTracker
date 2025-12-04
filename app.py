"""
Production-ready Flask app entry point
"""

from student_tracker import app
from database import init_db, USE_SUPABASE
import os

# Production'da veritabanını başlat
if __name__ == '__main__':
    try:
        # Veritabanını başlat
        # ÖNEMLİ: init_db() sadece tabloları oluşturur, mevcut verilere dokunmaz
        init_db()
        
        port = int(os.environ.get('PORT', 5002))
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        
        print("=" * 60)
        print("📚 Öğrenci Çalışma Takip Sistemi - EducationalTR")
        print("=" * 60)
        print(f"🌐 Uygulama başlatılıyor: http://0.0.0.0:{port}")
        if USE_SUPABASE:
            print("📁 Veritabanı: Supabase PostgreSQL")
        else:
            print("📁 Veritabanı: SQLite (Local)")
        print("=" * 60)
        
        app.run(debug=debug, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"❌ Uygulama başlatılırken hata: {e}")
        import traceback
        traceback.print_exc()
        raise




