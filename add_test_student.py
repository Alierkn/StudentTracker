#!/usr/bin/env python3
"""
Test için örnek öğrenci ekleme scripti
"""

from database import get_db, USE_SUPABASE, get_placeholder
from sql_helper import adapt_query
from werkzeug.security import generate_password_hash
from db_utils import get_cursor

def add_test_student():
    """Test için örnek öğrenci ekle"""
    
    # Test öğrenci bilgileri
    test_student = {
        'username': 'test_ogrenci',
        'password': 'test123',
        'full_name': 'Test Öğrenci',
        'email': 'test@example.com'
    }
    
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Kullanıcı adı zaten var mı kontrol et
            query = adapt_query('SELECT id FROM students WHERE username = ?')
            c.execute(query, (test_student['username'],))
            existing = c.fetchone()
            
            if existing:
                print(f"⚠️  '{test_student['username']}' kullanıcı adı zaten mevcut!")
                print(f"   Mevcut öğrenci ID: {existing['id']}")
                return False
            
            # Şifreyi hash'le
            hashed_password = generate_password_hash(test_student['password'])
            
            # Öğrenciyi ekle
            query = adapt_query('''
                INSERT INTO students (username, password, full_name, email, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''')
            
            if USE_SUPABASE:
                is_admin_value = False
            else:
                is_admin_value = 0
            
            c.execute(query, (
                test_student['username'],
                hashed_password,
                test_student['full_name'],
                test_student['email'],
                is_admin_value
            ))
            conn.commit()
            
            # Eklenen öğrenciyi al
            query = adapt_query('SELECT id FROM students WHERE username = ?')
            c.execute(query, (test_student['username'],))
            new_student = c.fetchone()
            
            print("=" * 60)
            print("✅ Test öğrencisi başarıyla eklendi!")
            print("=" * 60)
            print(f"📝 Kullanıcı Adı: {test_student['username']}")
            print(f"🔑 Şifre: {test_student['password']}")
            print(f"👤 Ad Soyad: {test_student['full_name']}")
            print(f"📧 E-posta: {test_student['email']}")
            print(f"🆔 Öğrenci ID: {new_student['id']}")
            print("=" * 60)
            print("\n💡 Bu öğrenci ile giriş yapabilir veya admin panelinden silebilirsiniz.")
            
            return True
            
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    add_test_student()




