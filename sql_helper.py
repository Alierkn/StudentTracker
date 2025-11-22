"""
SQL Helper - SQLite ve PostgreSQL uyumluluğu için
"""

from database import USE_SUPABASE, get_placeholder

def adapt_query(query):
    """SQL sorgusunu veritabanı tipine göre adapte et"""
    if USE_SUPABASE:
        # PostgreSQL için
        # ? -> %s
        query = query.replace('?', '%s')
        # SQLite date fonksiyonlarını PostgreSQL'e çevir
        query = query.replace("date('now', '-30 days')", "CURRENT_DATE - INTERVAL '30 days'")
        query = query.replace("date('now', '-12 weeks')", "CURRENT_DATE - INTERVAL '12 weeks'")
        query = query.replace("date('now')", "CURRENT_DATE")
    return query

def get_date_function(days=0):
    """Tarih fonksiyonunu döndür"""
    if USE_SUPABASE:
        if days == 0:
            return "CURRENT_DATE"
        return f"CURRENT_DATE - INTERVAL '{days} days'"
    else:
        if days == 0:
            return "date('now')"
        return f"date('now', '-{days} days')"




