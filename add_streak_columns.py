#!/usr/bin/env python3
"""
Streak kolonlarını students tablosuna ekle
Bu script sadece bir kez çalıştırılmalı
"""

import os
import sys

# .env dosyasını manuel oku
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from database import get_db, USE_SUPABASE

def add_streak_columns():
    """students tablosuna streak kolonlarını ekle"""
    try:
        with get_db() as conn:
            if USE_SUPABASE:
                # PostgreSQL (Supabase)
                cur = conn.cursor()
                
                # current_streak kolonu ekle (eğer yoksa)
                try:
                    cur.execute('''
                        ALTER TABLE students 
                        ADD COLUMN IF NOT EXISTS current_streak INTEGER DEFAULT 0
                    ''')
                    print("✅ current_streak kolonu eklendi (veya zaten var)")
                except Exception as e:
                    print(f"⚠️  current_streak kolonu: {e}")
                
                # longest_streak kolonu ekle (eğer yoksa)
                try:
                    cur.execute('''
                        ALTER TABLE students 
                        ADD COLUMN IF NOT EXISTS longest_streak INTEGER DEFAULT 0
                    ''')
                    print("✅ longest_streak kolonu eklendi (veya zaten var)")
                except Exception as e:
                    print(f"⚠️  longest_streak kolonu: {e}")
                
                # last_study_date kolonu ekle (eğer yoksa) - streak hesaplama için
                try:
                    cur.execute('''
                        ALTER TABLE students 
                        ADD COLUMN IF NOT EXISTS last_study_date DATE
                    ''')
                    print("✅ last_study_date kolonu eklendi (veya zaten var)")
                except Exception as e:
                    print(f"⚠️  last_study_date kolonu: {e}")
                
                conn.commit()
                print("\n✅ Tüm streak kolonları başarıyla eklendi!")
                
            else:
                # SQLite
                c = conn.cursor()
                
                # SQLite'da kolon eklemek için PRAGMA table_info ile kontrol et
                c.execute("PRAGMA table_info(students)")
                columns = [col[1] for col in c.fetchall()]
                
                if 'current_streak' not in columns:
                    c.execute('ALTER TABLE students ADD COLUMN current_streak INTEGER DEFAULT 0')
                    print("✅ current_streak kolonu eklendi")
                else:
                    print("ℹ️  current_streak kolonu zaten var")
                
                if 'longest_streak' not in columns:
                    c.execute('ALTER TABLE students ADD COLUMN longest_streak INTEGER DEFAULT 0')
                    print("✅ longest_streak kolonu eklendi")
                else:
                    print("ℹ️  longest_streak kolonu zaten var")
                
                if 'last_study_date' not in columns:
                    c.execute('ALTER TABLE students ADD COLUMN last_study_date DATE')
                    print("✅ last_study_date kolonu eklendi")
                else:
                    print("ℹ️  last_study_date kolonu zaten var")
                
                conn.commit()
                print("\n✅ Tüm streak kolonları başarıyla eklendi!")
                
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("🔥 Streak Kolonları Ekleme Script'i")
    print("=" * 60)
    print("\nBu script students tablosuna şu kolonları ekler:")
    print("  - current_streak: Mevcut üst üste çalışma günü sayısı")
    print("  - longest_streak: En uzun üst üste çalışma günü sayısı")
    print("  - last_study_date: Son çalışma tarihi")
    print("\n" + "=" * 60)
    
    # Otomatik çalıştır (non-interactive mode için)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        auto_mode = True
    else:
        try:
            response = input("\nDevam etmek istiyor musunuz? (E/H): ")
            auto_mode = response.upper() == 'E'
        except EOFError:
            # Non-interactive mode - otomatik devam et
            auto_mode = True
    
    if auto_mode:
        if add_streak_columns():
            print("\n🎉 Başarılı! Artık streak özelliğini kullanabilirsiniz.")
        else:
            print("\n❌ Hata oluştu. Lütfen log'ları kontrol edin.")
    else:
        print("\n❌ İşlem iptal edildi.")

