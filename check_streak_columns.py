#!/usr/bin/env python3
"""Supabase'de streak kolonlarının varlığını kontrol et"""

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

def check_streak_columns():
    """Supabase'de streak kolonlarını kontrol et"""
    if not USE_SUPABASE:
        print("❌ Bu script sadece Supabase için çalışır!")
        return False
    
    try:
        with get_db() as conn:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # students tablosundaki kolonları kontrol et
            cur.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'students'
                AND column_name IN ('current_streak', 'longest_streak', 'last_study_date')
                ORDER BY column_name
            """)
            
            columns = cur.fetchall()
            
            print("=" * 60)
            print("🔍 SUPABASE STREAK KOLONLARI KONTROLÜ")
            print("=" * 60)
            
            required_columns = ['current_streak', 'longest_streak', 'last_study_date']
            found_columns = [col['column_name'] for col in columns]
            
            for col_name in required_columns:
                if col_name in found_columns:
                    col_info = next(c for c in columns if c['column_name'] == col_name)
                    print(f"✅ {col_name}: {col_info['data_type']} (Default: {col_info['column_default'] or 'NULL'})")
                else:
                    print(f"❌ {col_name}: BULUNAMADI - EKLENMELİ!")
            
            print("=" * 60)
            
            if len(found_columns) == len(required_columns):
                print("✅ Tüm streak kolonları mevcut!")
                return True
            else:
                print("⚠️  Eksik kolonlar var. Migration yapılmalı!")
                return False
                
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_streak_columns()

