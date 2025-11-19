"""
SQLite'den Supabase PostgreSQL'e Veri Aktarım Scripti
Mevcut SQLite veritabanındaki tüm verileri Supabase'e aktarır
"""

import os
import sqlite3
from dotenv import load_dotenv

# Environment variables yükle (database import'undan ÖNCE!)
load_dotenv()

# Şimdi database modülünü import et
from database import get_db, init_db, USE_SUPABASE
from sql_helper import adapt_query
from db_utils import get_cursor

def migrate_data():
    """SQLite veritabanındaki tüm verileri Supabase'e aktar"""
    
    # Önce Supabase bağlantısını kontrol et
    if not USE_SUPABASE:
        print("❌ HATA: Supabase bağlantısı yapılandırılmamış!")
        print("Lütfen .env dosyasında SUPABASE_URL, SUPABASE_KEY ve SUPABASE_DB_URL değerlerini kontrol edin.")
        return False
    
    # SQLite veritabanı dosyası
    sqlite_db = os.path.join(os.path.dirname(__file__), 'student_tracker.db')
    
    if not os.path.exists(sqlite_db):
        print(f"❌ SQLite veritabanı bulunamadı: {sqlite_db}")
        print("Aktarılacak veri yok. Supabase'de tablolar otomatik oluşturulacak.")
        # Sadece tabloları oluştur
        init_db()
        print("✅ Supabase'de tablolar oluşturuldu.")
        return True
    
    print("=" * 60)
    print("🔄 SQLite → Supabase Veri Aktarımı Başlatılıyor...")
    print("=" * 60)
    
    # SQLite bağlantısı
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()
    
    try:
        # Supabase'de tabloları oluştur
        print("\n📋 Supabase'de tablolar oluşturuluyor...")
        init_db()
        print("✅ Tablolar hazır.")
        
        # Supabase bağlantısı
        with get_db() as supabase_conn:
            supabase_cur = get_cursor(supabase_conn)
            
            # 1. Students tablosunu aktar
            print("\n👥 Students tablosu aktarılıyor...")
            sqlite_cur.execute('SELECT * FROM students')
            students = sqlite_cur.fetchall()
            
            migrated_students = 0
            for student in students:
                try:
                    # Supabase'de var mı kontrol et
                    query = adapt_query('SELECT id FROM students WHERE username = ?')
                    supabase_cur.execute(query, (student['username'],))
                    if supabase_cur.fetchone():
                        print(f"  ⏭️  {student['username']} zaten mevcut, atlanıyor...")
                        continue
                    
                    # Insert
                    query = adapt_query('''
                        INSERT INTO students (username, password, full_name, email, is_admin, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''')
                    is_admin = bool(student['is_admin']) if USE_SUPABASE else student['is_admin']
                    supabase_cur.execute(query, (
                        student['username'],
                        student['password'],
                        student['full_name'],
                        student.get('email', ''),
                        is_admin,
                        student.get('created_at', None)
                    ))
                    migrated_students += 1
                except Exception as e:
                    print(f"  ❌ {student['username']} aktarılırken hata: {e}")
            
            supabase_conn.commit()
            print(f"✅ {migrated_students} öğrenci aktarıldı.")
            
            # 2. Study Sessions tablosunu aktar
            print("\n📚 Study Sessions tablosu aktarılıyor...")
            sqlite_cur.execute('SELECT * FROM study_sessions')
            sessions = sqlite_cur.fetchall()
            
            # Önce student_id mapping oluştur (SQLite id -> Supabase id)
            student_id_map = {}
            sqlite_cur.execute('SELECT id, username FROM students')
            for row in sqlite_cur.fetchall():
                query = adapt_query('SELECT id FROM students WHERE username = ?')
                supabase_cur.execute(query, (row['username'],))
                supabase_student = supabase_cur.fetchone()
                if supabase_student:
                    student_id_map[row['id']] = supabase_student['id']
            
            migrated_sessions = 0
            for session in sessions:
                try:
                    old_student_id = session['student_id']
                    new_student_id = student_id_map.get(old_student_id)
                    
                    if not new_student_id:
                        print(f"  ⚠️  Student ID {old_student_id} bulunamadı, atlanıyor...")
                        continue
                    
                    query = adapt_query('''
                        INSERT INTO study_sessions (student_id, date, subject, hours, efficiency, notes, difficulties, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''')
                    supabase_cur.execute(query, (
                        new_student_id,
                        session['date'],
                        session['subject'],
                        session['hours'],
                        session['efficiency'],
                        session.get('notes', ''),
                        session.get('difficulties', ''),
                        session.get('created_at', None)
                    ))
                    migrated_sessions += 1
                except Exception as e:
                    print(f"  ❌ Session aktarılırken hata: {e}")
            
            supabase_conn.commit()
            print(f"✅ {migrated_sessions} çalışma kaydı aktarıldı.")
            
            # 3. Exam Results tablosunu aktar
            print("\n📝 Exam Results tablosu aktarılıyor...")
            sqlite_cur.execute('SELECT * FROM exam_results')
            exams = sqlite_cur.fetchall()
            
            migrated_exams = 0
            for exam in exams:
                try:
                    old_student_id = exam['student_id']
                    new_student_id = student_id_map.get(old_student_id)
                    
                    if not new_student_id:
                        print(f"  ⚠️  Student ID {old_student_id} bulunamadı, atlanıyor...")
                        continue
                    
                    query = adapt_query('''
                        INSERT INTO exam_results (student_id, exam_name, score, max_score, exam_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''')
                    supabase_cur.execute(query, (
                        new_student_id,
                        exam['exam_name'],
                        exam['score'],
                        exam.get('max_score', 100),
                        exam.get('exam_date', None),
                        exam.get('created_at', None)
                    ))
                    migrated_exams += 1
                except Exception as e:
                    print(f"  ❌ Exam aktarılırken hata: {e}")
            
            supabase_conn.commit()
            print(f"✅ {migrated_exams} sınav sonucu aktarıldı.")
        
        print("\n" + "=" * 60)
        print("✅ VERİ AKTARIMI TAMAMLANDI!")
        print("=" * 60)
        print(f"📊 Özet:")
        print(f"   - Öğrenciler: {migrated_students}")
        print(f"   - Çalışma Kayıtları: {migrated_sessions}")
        print(f"   - Sınav Sonuçları: {migrated_exams}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        sqlite_conn.close()

if __name__ == '__main__':
    print("🚀 SQLite → Supabase Veri Aktarım Scripti")
    print("=" * 60)
    
    # Kullanıcıya onay sor
    response = input("\n⚠️  Bu işlem mevcut SQLite verilerini Supabase'e aktaracak.\nDevam etmek istiyor musunuz? (E/H): ")
    
    if response.upper() != 'E':
        print("❌ İşlem iptal edildi.")
        exit(0)
    
    success = migrate_data()
    
    if success:
        print("\n🎉 Başarılı! Artık uygulamanızı Supabase ile kullanabilirsiniz.")
        print("💡 Uygulamayı başlatmak için: python student_tracker.py")
    else:
        print("\n❌ Aktarım sırasında hata oluştu. Lütfen hataları kontrol edin.")

