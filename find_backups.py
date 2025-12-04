#!/usr/bin/env python3
"""Yedek veritabanı dosyalarını bul"""

import os
import sqlite3
from datetime import datetime

def find_db_files(search_paths):
    """Veritabanı dosyalarını bul"""
    db_files = []
    
    for path in search_paths:
        if not os.path.exists(path):
            continue
            
        for root, dirs, files in os.walk(path):
            # .git ve venv gibi klasörleri atla
            dirs[:] = [d for d in dirs if d not in ['.git', 'venv', '__pycache__', '.venv']]
            
            for file in files:
                if file.endswith('.db') or 'backup' in file.lower() or 'bak' in file.lower():
                    full_path = os.path.join(root, file)
                    try:
                        # Dosya boyutu ve tarih bilgisi
                        stat = os.stat(full_path)
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        
                        # SQLite dosyası mı kontrol et
                        is_sqlite = False
                        student_count = 0
                        try:
                            conn = sqlite3.connect(full_path)
                            c = conn.cursor()
                            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
                            if c.fetchone():
                                is_sqlite = True
                                c.execute('SELECT COUNT(*) FROM students')
                                student_count = c.fetchone()[0]
                            conn.close()
                        except:
                            pass
                        
                        db_files.append({
                            'path': full_path,
                            'size': size,
                            'mtime': mtime,
                            'is_sqlite': is_sqlite,
                            'student_count': student_count
                        })
                    except:
                        pass
    
    return db_files

if __name__ == '__main__':
    print("🔍 Yedek veritabanı dosyaları aranıyor...")
    print("=" * 60)
    
    # Arama yolları
    search_paths = [
        os.path.expanduser('~/Downloads'),
        os.path.expanduser('~/Desktop'),
        os.path.expanduser('~/Documents'),
        os.path.dirname(os.path.abspath(__file__))
    ]
    
    db_files = find_db_files(search_paths)
    
    if not db_files:
        print("❌ Hiç veritabanı dosyası bulunamadı.")
        print("\n💡 İpuçları:")
        print("   - Başka bir bilgisayarda yedek var mı kontrol edin")
        print("   - Time Machine yedeğiniz varsa oradan geri yükleyebilirsiniz")
        print("   - Eğer export edilmiş bir dosya varsa onu kullanabilirsiniz")
    else:
        print(f"✅ {len(db_files)} dosya bulundu:\n")
        
        # SQLite dosyalarını önce göster
        sqlite_files = [f for f in db_files if f['is_sqlite']]
        other_files = [f for f in db_files if not f['is_sqlite']]
        
        if sqlite_files:
            print("📊 SQLite Veritabanı Dosyaları:")
            print("-" * 60)
            for f in sorted(sqlite_files, key=lambda x: x['mtime'], reverse=True):
                print(f"\n📁 {f['path']}")
                print(f"   📅 Tarih: {f['mtime'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   💾 Boyut: {f['size']:,} bytes")
                print(f"   👥 Öğrenci sayısı: {f['student_count']}")
                print(f"\n   💡 Geri yüklemek için:")
                if f['student_count'] > 1:  # Admin hariç öğrenci varsa
                    print(f"      python restore_from_backup.py restore \"{f['path']}\"")
                else:
                    print(f"      python restore_from_backup.py import \"{f['path']}\"")
        
        if other_files:
            print("\n\n📄 Diğer Dosyalar (SQLite olmayan):")
            print("-" * 60)
            for f in sorted(other_files, key=lambda x: x['mtime'], reverse=True):
                print(f"   {f['path']} ({f['size']:,} bytes)")

