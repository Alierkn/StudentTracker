#!/usr/bin/env python3
"""
Veritabanı yedeğinden geri yükleme scripti
Eğer bir yedek dosyanız varsa, bu script ile geri yükleyebilirsiniz.
"""

import os
import sqlite3
import sys
from datetime import datetime

def restore_from_backup(backup_file, target_file='student_tracker.db'):
    """Yedek dosyadan veritabanını geri yükle"""
    
    if not os.path.exists(backup_file):
        print(f"❌ Yedek dosya bulunamadı: {backup_file}")
        return False
    
    print(f"📂 Yedek dosya: {backup_file}")
    print(f"📂 Hedef dosya: {target_file}")
    
    # Mevcut dosyayı yedekle
    if os.path.exists(target_file):
        backup_name = f"{target_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 Mevcut veritabanı yedekleniyor: {backup_name}")
        os.rename(target_file, backup_name)
    
    try:
        # Yedek dosyayı kopyala
        import shutil
        shutil.copy2(backup_file, target_file)
        print(f"✅ Veritabanı geri yüklendi!")
        
        # Kontrol et
        conn = sqlite3.connect(target_file)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM students')
        student_count = c.fetchone()[0]
        print(f"\n👥 Öğrenci sayısı: {student_count}")
        
        c.execute('SELECT COUNT(*) FROM study_sessions')
        session_count = c.fetchone()[0]
        print(f"📚 Çalışma kaydı sayısı: {session_count}")
        
        c.execute('SELECT COUNT(*) FROM exam_results')
        exam_count = c.fetchone()[0]
        print(f"📝 Sınav sonucu sayısı: {exam_count}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False

def import_from_sqlite(source_file, target_file='student_tracker.db'):
    """Başka bir SQLite dosyasından veri import et"""
    
    if not os.path.exists(source_file):
        print(f"❌ Kaynak dosya bulunamadı: {source_file}")
        return False
    
    print(f"📂 Kaynak dosya: {source_file}")
    print(f"📂 Hedef dosya: {target_file}")
    
    try:
        # Kaynak veritabanı
        source_conn = sqlite3.connect(source_file)
        source_conn.row_factory = sqlite3.Row
        source_cur = source_conn.cursor()
        
        # Hedef veritabanı
        target_conn = sqlite3.connect(target_file)
        target_cur = target_conn.cursor()
        
        # Students import
        print("\n👥 Öğrenciler import ediliyor...")
        source_cur.execute('SELECT * FROM students WHERE username != "admin"')
        students = source_cur.fetchall()
        
        imported_students = 0
        for student in students:
            try:
                # Kontrol et - zaten var mı?
                target_cur.execute('SELECT id FROM students WHERE username = ?', (student['username'],))
                if target_cur.fetchone():
                    print(f"  ⏭️  {student['username']} zaten mevcut, atlanıyor...")
                    continue
                
                target_cur.execute('''
                    INSERT INTO students (username, password, full_name, email, is_admin, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    student['username'],
                    student['password'],
                    student['full_name'],
                    student.get('email', ''),
                    student.get('is_admin', 0),
                    student.get('created_at', None)
                ))
                imported_students += 1
            except Exception as e:
                print(f"  ❌ {student['username']} import edilirken hata: {e}")
        
        target_conn.commit()
        print(f"✅ {imported_students} öğrenci import edildi.")
        
        # Student ID mapping oluştur
        student_id_map = {}
        source_cur.execute('SELECT id, username FROM students')
        for row in source_cur.fetchall():
            target_cur.execute('SELECT id FROM students WHERE username = ?', (row['username'],))
            target_student = target_cur.fetchone()
            if target_student:
                student_id_map[row['id']] = target_student[0]
        
        # Study sessions import
        print("\n📚 Çalışma kayıtları import ediliyor...")
        source_cur.execute('SELECT * FROM study_sessions')
        sessions = source_cur.fetchall()
        
        imported_sessions = 0
        for session in sessions:
            try:
                old_student_id = session['student_id']
                new_student_id = student_id_map.get(old_student_id)
                
                if not new_student_id:
                    continue
                
                target_cur.execute('''
                    INSERT INTO study_sessions (student_id, date, subject, hours, efficiency, notes, difficulties, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    new_student_id,
                    session['date'],
                    session['subject'],
                    session['hours'],
                    session['efficiency'],
                    session.get('notes', ''),
                    session.get('difficulties', ''),
                    session.get('created_at', None)
                ))
                imported_sessions += 1
            except Exception as e:
                print(f"  ❌ Session import edilirken hata: {e}")
        
        target_conn.commit()
        print(f"✅ {imported_sessions} çalışma kaydı import edildi.")
        
        # Exam results import
        print("\n📝 Sınav sonuçları import ediliyor...")
        source_cur.execute('SELECT * FROM exam_results')
        exams = source_cur.fetchall()
        
        imported_exams = 0
        for exam in exams:
            try:
                old_student_id = exam['student_id']
                new_student_id = student_id_map.get(old_student_id)
                
                if not new_student_id:
                    continue
                
                target_cur.execute('''
                    INSERT INTO exam_results (student_id, exam_name, score, max_score, exam_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    new_student_id,
                    exam['exam_name'],
                    exam['score'],
                    exam.get('max_score', 100),
                    exam.get('exam_date', None),
                    exam.get('created_at', None)
                ))
                imported_exams += 1
            except Exception as e:
                print(f"  ❌ Exam import edilirken hata: {e}")
        
        target_conn.commit()
        print(f"✅ {imported_exams} sınav sonucu import edildi.")
        
        source_conn.close()
        target_conn.close()
        
        print("\n" + "=" * 60)
        print("✅ VERİ İMPORTU TAMAMLANDI!")
        print("=" * 60)
        print(f"📊 Özet:")
        print(f"   - Öğrenciler: {imported_students}")
        print(f"   - Çalışma Kayıtları: {imported_sessions}")
        print(f"   - Sınav Sonuçları: {imported_exams}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔄 Veritabanı Geri Yükleme Scripti")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nKullanım:")
        print("  1. Yedek dosyadan geri yükle:")
        print("     python restore_from_backup.py restore <yedek_dosya.db>")
        print("\n  2. Başka bir SQLite dosyasından import et:")
        print("     python restore_from_backup.py import <kaynak_dosya.db>")
        print("\nÖrnek:")
        print("  python restore_from_backup.py restore student_tracker.db.backup")
        print("  python restore_from_backup.py import old_database.db")
        sys.exit(1)
    
    command = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not file_path:
        print("❌ Dosya yolu belirtilmedi!")
        sys.exit(1)
    
    if command == 'restore':
        success = restore_from_backup(file_path)
    elif command == 'import':
        success = import_from_sqlite(file_path)
    else:
        print(f"❌ Bilinmeyen komut: {command}")
        sys.exit(1)
    
    if success:
        print("\n🎉 Başarılı! Veriler geri yüklendi.")
    else:
        print("\n❌ Geri yükleme başarısız oldu.")

