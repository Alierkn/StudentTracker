"""
Veritabanı helper fonksiyonları - SQLite ve PostgreSQL uyumluluğu
"""

import os

USE_SUPABASE = os.environ.get('USE_SUPABASE', 'false').lower() == 'true'

def get_placeholder():
    """Placeholder karakterini döndür (? veya %s)"""
    return '%s' if USE_SUPABASE else '?'

def execute_query(conn, query, params=None, fetch_one=False, fetch_all=False):
    """Genel query çalıştırma - hem SQLite hem PostgreSQL için"""
    cursor = conn.cursor()
    
    # SQLite için row_factory ayarla
    if not USE_SUPABASE:
        try:
            import sqlite3
            if isinstance(conn, sqlite3.Connection):
                conn.row_factory = sqlite3.Row
        except:
            pass
    
    cursor.execute(query, params or ())
    
    if fetch_one:
        result = cursor.fetchone()
    elif fetch_all:
        result = cursor.fetchall()
    else:
        result = None
    
    return result, cursor

def dict_factory(cursor, row):
    """SQLite için dict factory"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}




