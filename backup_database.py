#!/usr/bin/env python3
"""
Otomatik veritabanı yedekleme scripti
Bu script'i cron job veya zamanlayıcı ile çalıştırabilirsiniz.
"""

import os
import shutil
import sqlite3
from datetime import datetime

def backup_database(db_file='student_tracker.db', backup_dir='backups'):
    """Veritabanını yedekle"""
    
    if not os.path.exists(db_file):
        print(f"❌ Veritabanı dosyası bulunamadı: {db_file}")
        return False
    
    # Yedek klasörü oluştur
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Yedek dosya adı
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'student_tracker_{timestamp}.db')
    
    try:
        # Dosyayı kopyala
        shutil.copy2(db_file, backup_file)
        
        # Eski yedekleri temizle (30 günden eski)
        cleanup_old_backups(backup_dir, days=30)
        
        print(f"✅ Yedek oluşturuldu: {backup_file}")
        
        # Veri kontrolü
        conn = sqlite3.connect(backup_file)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM students')
        student_count = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM study_sessions')
        session_count = c.fetchone()[0]
        conn.close()
        
        print(f"   👥 Öğrenci sayısı: {student_count}")
        print(f"   📚 Çalışma kaydı sayısı: {session_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Yedek oluşturulurken hata: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_old_backups(backup_dir, days=30):
    """Eski yedekleri temizle"""
    import time
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath) and filename.startswith('student_tracker_'):
            if os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    print(f"   🗑️  Eski yedek silindi: {filename}")
                except:
                    pass

if __name__ == '__main__':
    print("💾 Veritabanı Yedekleme Scripti")
    print("=" * 60)
    
    success = backup_database()
    
    if success:
        print("\n🎉 Yedekleme tamamlandı!")
        print("\n💡 Otomatik yedekleme için:")
        print("   - Cron job ekleyin: 0 2 * * * cd /path/to/project && python backup_database.py")
        print("   - Veya sistem zamanlayıcısı kullanın")
    else:
        print("\n❌ Yedekleme başarısız oldu.")

