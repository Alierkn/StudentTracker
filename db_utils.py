"""
Veritabanı utility fonksiyonları
"""

from database import USE_SUPABASE

def get_cursor(conn):
    """Veritabanı tipine göre cursor oluştur"""
    if USE_SUPABASE:
        from psycopg2.extras import RealDictCursor
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

