"""
Supabase PostgreSQL Veritabanı Bağlantısı
SQLite ve PostgreSQL uyumluluğu
"""

import os
from contextlib import contextmanager

# Supabase bağlantı bilgileri
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '').strip()
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL', '').strip()  # PostgreSQL connection string

USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY and SUPABASE_DB_URL)

# Production'da Supabase zorunludur - uyarı ver
if not USE_SUPABASE and os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER'):
    print("=" * 60)
    print("⚠️  UYARI: Production ortamında Supabase bağlantısı yok!")
    print("=" * 60)
    print("❌ SUPABASE_URL:", "✅ Var" if SUPABASE_URL else "❌ YOK")
    print("❌ SUPABASE_KEY:", "✅ Var" if SUPABASE_KEY else "❌ YOK")
    print("❌ SUPABASE_DB_URL:", "✅ Var" if SUPABASE_DB_URL else "❌ YOK")
    print("=" * 60)
    print("⚠️  Production'da SQLite kullanılıyor - VERİLER KAYBOLACAK!")
    print("📋 Railway/Render Dashboard → Variables sekmesine gidin")
    print("📋 SUPABASE_URL, SUPABASE_KEY, SUPABASE_DB_URL ekleyin")
    print("=" * 60)

# Connection pool (PostgreSQL için)
_pool = None

def get_db_pool():
    """PostgreSQL connection pool oluştur"""
    global _pool
    
    if not USE_SUPABASE:
        return None
    
    if _pool is None:
        try:
            from psycopg2.pool import SimpleConnectionPool
            _pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=SUPABASE_DB_URL
            )
        except ImportError:
            raise ImportError("psycopg2-binary paketi gerekli! pip install psycopg2-binary")
    
    return _pool

@contextmanager
def get_db():
    """Veritabanı bağlantısı context manager - hem SQLite hem PostgreSQL"""
    if USE_SUPABASE:
        # PostgreSQL (Supabase)
        pool = get_db_pool()
        conn = pool.getconn()
        
        try:
            conn.set_session(autocommit=False)
            # RealDictCursor için cursor factory ayarla
            from psycopg2.extras import RealDictCursor
            # Connection'ı RealDictCursor kullanacak şekilde işaretle
            # (cursor oluştururken belirtilecek)
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            pool.putconn(conn)
    else:
        # SQLite (local development)
        import sqlite3
        DB_FILE = os.path.join(os.path.dirname(__file__), 'student_tracker.db')
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

def get_placeholder():
    """Placeholder karakterini döndür"""
    return '%s' if USE_SUPABASE else '?'

# init_db() çağrı sayacı - sadece bir kez çalışmasını sağlamak için
_init_db_called = False

def init_db():
    """
    Veritabanı tablolarını oluştur - SADECE TABLO OLUŞTURUR, VERİ SİLMEZ
    
    ÖNEMLİ GÜVENLİK NOTLARI:
    - Bu fonksiyon sadece CREATE TABLE IF NOT EXISTS kullanır
    - Mevcut tablolar ve veriler KORUNUR
    - Hiçbir DELETE, DROP, TRUNCATE işlemi yapılmaz
    - Sadece tablo yoksa oluşturur, varsa dokunmaz
    """
    global _init_db_called
    
    # Eğer daha önce çağrıldıysa ve tablolar varsa tekrar çalıştırma
    # (Production'da gereksiz çağrıları önlemek için)
    if _init_db_called:
        try:
            with get_db() as conn:
                # Tabloların var olup olmadığını kontrol et
                if USE_SUPABASE:
                    from psycopg2.extras import RealDictCursor
                    c = conn.cursor(cursor_factory=RealDictCursor)
                    c.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'students')")
                else:
                    c = conn.cursor()
                    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
                result = c.fetchone()
                if result:
                    # Tablo varsa, init_db'yi tekrar çalıştırmaya gerek yok
                    if USE_SUPABASE:
                        table_exists = result[0] if isinstance(result, dict) else result[0]
                    else:
                        table_exists = result is not None
                    if table_exists:
                        return  # Tablolar zaten var, tekrar çalıştırmaya gerek yok
        except:
            pass  # Hata olursa devam et, init_db'yi çalıştır
    
    _init_db_called = True
    
    if USE_SUPABASE:
        # PostgreSQL (Supabase)
        with get_db() as conn:
            cur = conn.cursor()
            
            # Öğrenciler tablosu
            cur.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Çalışma kayıtları tablosu
            cur.execute('''
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    hours REAL NOT NULL,
                    efficiency INTEGER NOT NULL,
                    notes TEXT,
                    difficulties TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
                )
            ''')
            
            # Sınav sonuçları tablosu
            cur.execute('''
                CREATE TABLE IF NOT EXISTS exam_results (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    exam_name VARCHAR(255) NOT NULL,
                    score REAL NOT NULL,
                    max_score REAL DEFAULT 100,
                    exam_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
                )
            ''')
            
            # Ders programları tablosu
            cur.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
                )
            ''')
            
            # Ders programı öğeleri tablosu
            cur.execute('''
                CREATE TABLE IF NOT EXISTS schedule_items (
                    id SERIAL PRIMARY KEY,
                    schedule_id INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    location VARCHAR(255),
                    instructor VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE CASCADE
                )
            ''')
            
            # Ders programı tamamlama durumları tablosu
            cur.execute('''
                CREATE TABLE IF NOT EXISTS schedule_completions (
                    id SERIAL PRIMARY KEY,
                    schedule_item_id INTEGER NOT NULL,
                    completion_date DATE NOT NULL,
                    is_completed BOOLEAN DEFAULT FALSE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (schedule_item_id) REFERENCES schedule_items (id) ON DELETE CASCADE
                )
            ''')
            
            # Index'ler
            cur.execute('CREATE INDEX IF NOT EXISTS idx_study_sessions_student_id ON study_sessions(student_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_study_sessions_date ON study_sessions(date)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_exam_results_student_id ON exam_results(student_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_schedules_student_id ON schedules(student_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_schedule_items_schedule_id ON schedule_items(schedule_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_schedule_completions_item_id ON schedule_completions(schedule_item_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_schedule_completions_date ON schedule_completions(completion_date)')
            
            conn.commit()
            
            # Varsayılan admin kullanıcısı oluştur
            create_default_admin(conn)
    else:
        # SQLite (local development)
        import sqlite3
        from werkzeug.security import generate_password_hash
        
        DB_FILE = os.path.join(os.path.dirname(__file__), 'student_tracker.db')
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date DATE NOT NULL,
                subject TEXT NOT NULL,
                hours REAL NOT NULL,
                efficiency INTEGER NOT NULL,
                notes TEXT,
                difficulties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                exam_name TEXT NOT NULL,
                score REAL NOT NULL,
                max_score REAL DEFAULT 100,
                exam_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        
        # Ders programları tablosu
        c.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        
        # Ders programı öğeleri tablosu
        c.execute('''
            CREATE TABLE IF NOT EXISTS schedule_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                subject TEXT NOT NULL,
                location TEXT,
                instructor TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (schedule_id) REFERENCES schedules (id)
            )
        ''')
        
        # Ders programı tamamlama durumları tablosu
        c.execute('''
            CREATE TABLE IF NOT EXISTS schedule_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_item_id INTEGER NOT NULL,
                completion_date DATE NOT NULL,
                is_completed INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (schedule_item_id) REFERENCES schedule_items (id)
            )
        ''')
        
        # Index'ler
        c.execute('CREATE INDEX IF NOT EXISTS idx_schedules_student_id ON schedules(student_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_schedule_items_schedule_id ON schedule_items(schedule_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_schedule_completions_item_id ON schedule_completions(schedule_item_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_schedule_completions_date ON schedule_completions(completion_date)')
        
        conn.commit()
        conn.close()
        
        # Varsayılan admin oluştur
        create_default_admin()

def create_default_admin(conn=None):
    """Varsayılan admin kullanıcısı oluştur"""
    from werkzeug.security import generate_password_hash
    
    if USE_SUPABASE:
        if conn is None:
            with get_db() as conn:
                _create_admin(conn)
        else:
            _create_admin(conn)
    else:
        import sqlite3
        DB_FILE = os.path.join(os.path.dirname(__file__), 'student_tracker.db')
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT id FROM students WHERE username = ?', ('admin',))
        if not c.fetchone():
            admin_password = generate_password_hash('admin123')
            c.execute('''
                INSERT INTO students (username, password, full_name, email, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', admin_password, 'Admin Kullanıcı', 'admin@example.com', 1))
            conn.commit()
            print("✅ Varsayılan admin kullanıcısı oluşturuldu (username: admin, password: admin123)")
        conn.close()

def _create_admin(conn):
    """Admin kullanıcısı oluştur (PostgreSQL)"""
    from werkzeug.security import generate_password_hash
    
    cur = conn.cursor()
    cur.execute('SELECT id FROM students WHERE username = %s', ('admin',))
    if not cur.fetchone():
        admin_password = generate_password_hash('admin123')
        cur.execute('''
            INSERT INTO students (username, password, full_name, email, is_admin)
            VALUES (%s, %s, %s, %s, %s)
        ''', ('admin', admin_password, 'Admin Kullanıcı', 'admin@example.com', True))
        conn.commit()
        print("✅ Varsayılan admin kullanıcısı oluşturuldu (username: admin, password: admin123)")
