#!/usr/bin/env python3
"""Supabase bağlantısını ve verilerini detaylı kontrol et"""

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

from database import get_db, USE_SUPABASE, SUPABASE_URL, SUPABASE_DB_URL

print("=" * 60)
print("🔍 SUPABASE BAĞLANTI KONTROLÜ")
print("=" * 60)

# Bağlantı bilgilerini kontrol et
print("\n📋 Bağlantı Bilgileri:")
print(f"  ✅ USE_SUPABASE: {USE_SUPABASE}")
if USE_SUPABASE:
    print(f"  📍 SUPABASE_URL: {SUPABASE_URL}")
    # DB URL'den proje referansını çıkar
    if SUPABASE_DB_URL:
        if 'glduuxixobpdkvczkbxn' in SUPABASE_DB_URL:
            print(f"  ✅ Proje Referansı: glduuxixobpdkvczkbxn (DOĞRU)")
        else:
            print(f"  ⚠️  Proje Referansı: Farklı bir proje olabilir")
        # URL'den host bilgisini çıkar
        if 'pooler.supabase.com' in SUPABASE_DB_URL:
            print(f"  ✅ Connection Pooler kullanılıyor")
        elif 'db.' in SUPABASE_DB_URL:
            print(f"  ⚠️  Direct connection kullanılıyor (pooler önerilir)")
    else:
        print(f"  ❌ SUPABASE_DB_URL boş!")

if not USE_SUPABASE:
    print("\n❌ Supabase bağlantısı yapılandırılmamış!")
    print("   .env dosyasında SUPABASE_URL, SUPABASE_KEY ve SUPABASE_DB_URL kontrol edin.")
    sys.exit(1)

print("\n" + "=" * 60)
print("📊 VERİTABANI VERİ DURUMU")
print("=" * 60)

try:
    with get_db() as conn:
        from psycopg2.extras import RealDictCursor
        c = conn.cursor(cursor_factory=RealDictCursor)
        
        # Tabloları kontrol et
        print("\n📋 Tablolar:")
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = c.fetchall()
        for table in tables:
            print(f"  ✅ {table['table_name']}")
        
        # Students kontrolü
        print("\n👥 Öğrenciler:")
        c.execute('SELECT COUNT(*) as count FROM students')
        result = c.fetchone()
        student_count = result['count']
        print(f"  📊 Toplam öğrenci sayısı: {student_count}")
        
        if student_count > 0:
            c.execute('SELECT id, username, full_name, email, is_admin, created_at FROM students ORDER BY id')
            students = c.fetchall()
            print(f"\n  📝 Öğrenci Listesi:")
            for s in students:
                admin_status = "👑 Admin" if s['is_admin'] else "👤 Öğrenci"
                print(f"    - ID: {s['id']}, Username: {s['username']}, Ad: {s['full_name']}, {admin_status}")
                print(f"      Email: {s['email']}, Oluşturulma: {s['created_at']}")
        else:
            print("  ⚠️  UYARI: Veritabanında öğrenci yok!")
        
        # Study sessions kontrolü
        print("\n📚 Çalışma Kayıtları:")
        c.execute('SELECT COUNT(*) as count FROM study_sessions')
        result = c.fetchone()
        session_count = result['count']
        print(f"  📊 Toplam çalışma kaydı sayısı: {session_count}")
        
        if session_count > 0:
            c.execute('''
                SELECT ss.id, ss.student_id, s.username, ss.subject, ss.date, ss.hours, ss.efficiency
                FROM study_sessions ss
                JOIN students s ON ss.student_id = s.id
                ORDER BY ss.id DESC
                LIMIT 10
            ''')
            sessions = c.fetchall()
            print(f"\n  📝 Son 10 Çalışma Kaydı:")
            for sess in sessions:
                print(f"    - ID: {sess['id']}, Öğrenci: {sess['username']}, Ders: {sess['subject']}, Tarih: {sess['date']}, Saat: {sess['hours']}h, Verimlilik: {sess['efficiency']}%")
        
        # Exam results kontrolü
        print("\n📝 Sınav Sonuçları:")
        c.execute('SELECT COUNT(*) as count FROM exam_results')
        result = c.fetchone()
        exam_count = result['count']
        print(f"  📊 Toplam sınav sonucu sayısı: {exam_count}")
        
        if exam_count > 0:
            c.execute('''
                SELECT er.id, er.student_id, s.username, er.exam_name, er.score, er.max_score, er.exam_date
                FROM exam_results er
                JOIN students s ON er.student_id = s.id
                ORDER BY er.id DESC
                LIMIT 10
            ''')
            exams = c.fetchall()
            print(f"\n  📝 Son 10 Sınav Sonucu:")
            for exam in exams:
                print(f"    - ID: {exam['id']}, Öğrenci: {exam['username']}, Sınav: {exam['exam_name']}, Not: {exam['score']}/{exam['max_score']}, Tarih: {exam['exam_date']}")
        
        # Schedules kontrolü
        print("\n📅 Ders Programları:")
        c.execute('SELECT COUNT(*) as count FROM schedules')
        result = c.fetchone()
        schedule_count = result['count']
        print(f"  📊 Toplam ders programı sayısı: {schedule_count}")
        
        if schedule_count > 0:
            c.execute('''
                SELECT sc.id, sc.student_id, s.username, sc.name, sc.description
                FROM schedules sc
                JOIN students s ON sc.student_id = s.id
                ORDER BY sc.id DESC
                LIMIT 5
            ''')
            schedules = c.fetchall()
            print(f"\n  📝 Son 5 Ders Programı:")
            for sched in schedules:
                print(f"    - ID: {sched['id']}, Öğrenci: {sched['username']}, İsim: {sched['name']}")
        
        # Veri kaybı kontrolü
        print("\n" + "=" * 60)
        print("🔒 VERİ GÜVENLİK KONTROLÜ")
        print("=" * 60)
        
        if student_count == 0:
            print("  ⚠️  UYARI: Veritabanında öğrenci yok!")
            print("     Bu normal değil. Veri kaybı olmuş olabilir.")
        elif student_count == 1:
            c.execute('SELECT username FROM students WHERE is_admin = TRUE')
            admin_check = c.fetchone()
            if admin_check and admin_check['username'] == 'admin':
                print("  ⚠️  UYARI: Sadece admin kullanıcısı var.")
                print("     Normal öğrenciler silinmiş olabilir.")
            else:
                print("  ✅ En azından bir öğrenci var.")
        else:
            print(f"  ✅ {student_count} öğrenci mevcut.")
        
        print("\n" + "=" * 60)
        print("✅ KONTROL TAMAMLANDI")
        print("=" * 60)
        
except Exception as e:
    print(f"\n❌ Hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

