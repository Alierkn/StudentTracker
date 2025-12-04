#!/usr/bin/env python3
"""Supabase'deki verileri kontrol et"""

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
from db_utils import get_cursor

if USE_SUPABASE:
    print("✅ Supabase bağlantısı aktif")
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Students kontrolü
            c.execute('SELECT COUNT(*) as count FROM students')
            result = c.fetchone()
            student_count = result['count'] if isinstance(result, dict) else result[0]
            print(f"\n👥 Supabase'de öğrenci sayısı: {student_count}")
            
            if student_count > 0:
                c.execute('SELECT id, username, full_name FROM students LIMIT 10')
                students = c.fetchall()
                print("\n📝 Öğrenciler:")
                for s in students:
                    s_dict = dict(s) if not isinstance(s, dict) else s
                    print(f"  - ID: {s_dict['id']}, Username: {s_dict['username']}, Ad: {s_dict['full_name']}")
            
            # Study sessions kontrolü
            c.execute('SELECT COUNT(*) as count FROM study_sessions')
            result = c.fetchone()
            session_count = result['count'] if isinstance(result, dict) else result[0]
            print(f"\n📚 Supabase'de çalışma kaydı sayısı: {session_count}")
            
            # Exam results kontrolü
            c.execute('SELECT COUNT(*) as count FROM exam_results')
            result = c.fetchone()
            exam_count = result['count'] if isinstance(result, dict) else result[0]
            print(f"📝 Supabase'de sınav sonucu sayısı: {exam_count}")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Supabase bağlantısı yapılandırılmamış")

