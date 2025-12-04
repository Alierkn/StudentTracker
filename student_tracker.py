"""
Öğrenci Çalışma Takip Sistemi
Öğrencilerin günlük çalışma verilerini, sınav sonuçlarını ve gelişimlerini takip eder
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os
import json
from functools import wraps
from dotenv import load_dotenv

# Environment variables yükle
load_dotenv()

# Veritabanı modülünü import et
from database import get_db, init_db, get_placeholder, USE_SUPABASE
from sql_helper import adapt_query, get_date_function
from db_utils import get_cursor

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ogrenci-takip-sistemi-secret-key-2024')
CORS(app)

# Google OAuth client (lazy initialization)
_google_oauth = None

def get_google_oauth():
    """Google OAuth client'ı al veya oluştur"""
    global _google_oauth
    if _google_oauth is None:
        try:
            from authlib.integrations.flask_client import OAuth
            GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
            GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
            
            if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
                oauth = OAuth(app)
                _google_oauth = oauth.register(
                    name='google',
                    client_id=GOOGLE_CLIENT_ID,
                    client_secret=GOOGLE_CLIENT_SECRET,
                    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                    client_kwargs={
                        'scope': 'openid email profile'
                    }
                )
        except ImportError:
            pass
    return _google_oauth

def update_streak(student_id, study_date):
    """
    Öğrencinin streak'ini güncelle
    Streak: Üst üste çalışma günü sayısı

    Returns:
        dict: {
            'streak_increased': bool,
            'same_day': bool,
            'new_streak': int,
            'old_streak': int,
            'broken': bool
        }
    """
    try:
        with get_db() as conn:
            c = get_cursor(conn)

            # Öğrencinin mevcut streak bilgilerini al
            query = adapt_query('''
                SELECT current_streak, longest_streak, last_study_date
                FROM students
                WHERE id = ?
            ''')
            c.execute(query, (student_id,))
            student = c.fetchone()

            if not student:
                return {'streak_increased': False, 'same_day': False, 'new_streak': 0, 'old_streak': 0, 'broken': False}

            # Kolonlar yoksa (eski veritabanı) varsayılan değerler kullan
            current_streak = student.get('current_streak', 0) if isinstance(student, dict) else (student[0] if len(student) > 0 else 0)
            longest_streak = student.get('longest_streak', 0) if isinstance(student, dict) else (student[1] if len(student) > 1 else 0)
            last_study_date = student.get('last_study_date', None) if isinstance(student, dict) else (student[2] if len(student) > 2 else None)

            old_streak = current_streak  # Eski streak'i sakla

            # Tarihi parse et
            if isinstance(study_date, str):
                study_date_obj = datetime.strptime(study_date, '%Y-%m-%d').date()
            else:
                study_date_obj = study_date if isinstance(study_date, date) else study_date.date()

            today = date.today()
            yesterday = today - timedelta(days=1)

            # Streak hesapla
            new_streak = 1  # Varsayılan: yeni streak başlat
            same_day = False
            streak_broken = False

            if last_study_date:
                if isinstance(last_study_date, str):
                    last_date = datetime.strptime(last_study_date, '%Y-%m-%d').date()
                else:
                    last_date = last_study_date if isinstance(last_study_date, date) else last_study_date.date()

                # Eğer bugün veya dün çalıştıysa streak devam eder
                if study_date_obj == today or study_date_obj == yesterday:
                    if last_date == yesterday or last_date == today:
                        # Streak devam ediyor
                        new_streak = current_streak + 1
                    elif last_date == today and study_date_obj == today:
                        # Bugün zaten çalışma kaydı var, streak artmaz
                        new_streak = current_streak
                        same_day = True
                    else:
                        # Streak kırıldı, yeni streak başlat
                        new_streak = 1
                        streak_broken = True
                else:
                    # Geçmiş tarih, streak hesaplama
                    days_diff = (study_date_obj - last_date).days
                    if days_diff == 1:
                        # Üst üste çalışma
                        new_streak = current_streak + 1
                    else:
                        # Streak kırıldı
                        new_streak = 1
                        streak_broken = True

            # En uzun streak'i güncelle
            if new_streak > longest_streak:
                longest_streak = new_streak

            # Veritabanını güncelle
            # Önce kolonların var olup olmadığını kontrol et
            try:
                query = adapt_query('''
                    UPDATE students
                    SET current_streak = ?,
                        longest_streak = ?,
                        last_study_date = ?
                    WHERE id = ?
                ''')
                c.execute(query, (new_streak, longest_streak, study_date_obj, student_id))
                conn.commit()
            except Exception as e:
                # Kolonlar yoksa, önce ekle (migration)
                if 'column' in str(e).lower() or 'does not exist' in str(e).lower():
                    print(f"⚠️  Streak kolonları bulunamadı. Migration script'ini çalıştırın: python add_streak_columns.py")
                else:
                    raise

            return {
                'streak_increased': new_streak > old_streak,
                'same_day': same_day,
                'new_streak': new_streak,
                'old_streak': old_streak,
                'broken': streak_broken
            }

    except Exception as e:
        print(f"⚠️  Streak güncelleme hatası: {e}")
        import traceback
        traceback.print_exc()
        return {'streak_increased': False, 'same_day': False, 'new_streak': 0, 'old_streak': 0, 'broken': False}

# Veritabanını başlat (Gunicorn için)
# Gunicorn ile çalışırken if __name__ == '__main__' çalışmaz
# Bu yüzden app oluşturulurken init_db() çağrılmalı
# ÖNEMLİ: init_db() sadece tabloları oluşturur, mevcut verilere dokunmaz
try:
    print("🔄 Veritabanı başlatılıyor...")
    # init_db() sadece CREATE TABLE IF NOT EXISTS yapar, veri silmez
    # ÖNEMLİ: Bu fonksiyon mevcut verilere dokunmaz, sadece tabloları oluşturur
    init_db()
    print("✅ Veritabanı hazır.")
    if USE_SUPABASE:
        print("📁 Veritabanı: Supabase PostgreSQL ✅")
        # Supabase bağlantısını ve veri durumunu kontrol et
        try:
            with get_db() as conn:
                from psycopg2.extras import RealDictCursor
                c = conn.cursor(cursor_factory=RealDictCursor)
                c.execute('SELECT COUNT(*) as count FROM students')
                result = c.fetchone()
                if result:
                    if isinstance(result, dict):
                        student_count = result.get('count', 0)
                    else:
                        student_count = result[0] if len(result) > 0 else 0
                    print(f"📊 Mevcut öğrenci sayısı: {student_count}")
                    if student_count == 0:
                        print("⚠️  UYARI: Veritabanında öğrenci bulunamadı!")
        except Exception as check_error:
            print(f"⚠️  Veri kontrolü hatası: {check_error}")
    else:
        print("📁 Veritabanı: SQLite (Local) ⚠️")
        # Production ortamında SQLite kullanımı uyarısı
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER'):
            print("=" * 60)
            print("🚨 KRİTİK UYARI: Production'da SQLite kullanılıyor!")
            print("=" * 60)
            print("❌ Bu durumda her deploy'da veriler kaybolacak!")
            print("✅ Railway/Render Dashboard → Variables sekmesine gidin")
            print("✅ SUPABASE_URL, SUPABASE_KEY, SUPABASE_DB_URL ekleyin")
            print("=" * 60)
except Exception as e:
    print(f"⚠️  Veritabanı başlatma uyarısı: {e}")
    import traceback
    traceback.print_exc()
    # Hata olsa bile devam et (belki tablolar zaten var)

# Production error handler
@app.errorhandler(500)
def internal_error(error):
    """500 hatası için detaylı log"""
    import traceback
    error_msg = traceback.format_exc()
    print("=" * 60)
    print("❌ INTERNAL SERVER ERROR")
    print("=" * 60)
    print(error_msg)
    print("=" * 60)
    # Production'da detaylı hata gösterme
    if os.environ.get('FLASK_DEBUG', 'False').lower() == 'true':
        return f"<h1>Internal Server Error</h1><pre>{error_msg}</pre>", 500
    return "Internal Server Error", 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Tüm exception'ları yakala"""
    import traceback
    error_msg = traceback.format_exc()
    print("=" * 60)
    print("❌ UNHANDLED EXCEPTION")
    print("=" * 60)
    print(error_msg)
    print("=" * 60)
    return "Internal Server Error", 500

def login_required(f):
    """Giriş yapmış kullanıcı kontrolü"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Admin kontrolü"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Bu sayfaya erişim yetkiniz yok.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ROUTES

@app.route('/')
def index():
    """Ana sayfa - giriş yapmışsa dashboard'a yönlendir"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Kullanıcı adı ve şifre gerekli!', 'error')
            return render_template('login.html')
        
        with get_db() as conn:
            c = get_cursor(conn)
            query = adapt_query('SELECT * FROM students WHERE username = ?')
            c.execute(query, (username,))
            user = c.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['is_admin'] = bool(user['is_admin'])
            flash(f'Hoş geldiniz, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Kullanıcı adı veya şifre hatalı!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Kayıt sayfası"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        email = request.form.get('email', '')
        
        if not username or not password or not full_name:
            flash('Tüm alanlar doldurulmalı!', 'error')
            return render_template('register.html')
        
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Kullanıcı adı kontrolü
            query = adapt_query('SELECT id FROM students WHERE username = ?')
            c.execute(query, (username,))
            if c.fetchone():
                flash('Bu kullanıcı adı zaten kullanılıyor!', 'error')
                return render_template('register.html')
            
            # Yeni kullanıcı ekle
            hashed_password = generate_password_hash(password)
            query = adapt_query('''
                INSERT INTO students (username, password, full_name, email)
                VALUES (?, ?, ?, ?)
            ''')
            c.execute(query, (username, hashed_password, full_name, email))
            conn.commit()
        
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Çıkış yap"""
    session.clear()
    flash('Başarıyla çıkış yapıldı.', 'success')
    return redirect(url_for('login'))

@app.route('/google-login')
def google_login():
    """Google OAuth ile giriş/kayıt"""
    try:
        google = get_google_oauth()
        
        if not google:
            flash('Google OAuth yapılandırılmamış. Lütfen normal kayıt formunu kullanın.', 'info')
            return redirect(url_for('register'))
        
        # Redirect URI
        redirect_uri = url_for('google_callback', _external=True)
        
        # Google'a yönlendir
        return google.authorize_redirect(redirect_uri)
        
    except Exception as e:
        import traceback
        print(f"Google login hatası: {e}")
        print(traceback.format_exc())
        flash('Google girişi şu anda kullanılamıyor. Lütfen normal kayıt formunu kullanın.', 'error')
        return redirect(url_for('register'))

@app.route('/google-callback')
def google_callback():
    """Google OAuth callback"""
    try:
        from werkzeug.security import generate_password_hash
        
        google = get_google_oauth()
        
        if not google:
            flash('Google OAuth yapılandırılmamış.', 'error')
            return redirect(url_for('register'))
        
        # Token al
        token = google.authorize_access_token()
        
        # Kullanıcı bilgilerini al
        user_info = token.get('userinfo')
        if not user_info:
            resp = google.get('userinfo')
            user_info = resp.json()
        
        email = user_info.get('email')
        name = user_info.get('name', '')
        google_id = user_info.get('sub')
        
        if not email:
            flash('Google hesabınızdan e-posta bilgisi alınamadı.', 'error')
            return redirect(url_for('register'))
        
        # Kullanıcı adı oluştur (email'den)
        username = email.split('@')[0]
        
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Kullanıcı var mı kontrol et (email ile)
            query = adapt_query('SELECT * FROM students WHERE email = ?')
            c.execute(query, (email,))
            user = c.fetchone()
            
            if user:
                # Mevcut kullanıcı - giriş yap
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                session['is_admin'] = bool(user['is_admin'])
                flash(f'Hoş geldiniz, {user["full_name"]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Yeni kullanıcı - kayıt ol
                # Username benzersiz olmalı
                base_username = username
                counter = 1
                while True:
                    query = adapt_query('SELECT id FROM students WHERE username = ?')
                    c.execute(query, (username,))
                    if not c.fetchone():
                        break
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Rastgele şifre oluştur (Google OAuth kullanıcıları için)
                import secrets
                random_password = secrets.token_urlsafe(32)
                hashed_password = generate_password_hash(random_password)
                
                # Kullanıcıyı ekle
                query = adapt_query('''
                    INSERT INTO students (username, password, full_name, email)
                    VALUES (?, ?, ?, ?)
                ''')
                c.execute(query, (username, hashed_password, name, email))
                conn.commit()
                
                # Yeni oluşturulan kullanıcıyı al
                query = adapt_query('SELECT * FROM students WHERE username = ?')
                c.execute(query, (username,))
                new_user = c.fetchone()
                
                session['user_id'] = new_user['id']
                session['username'] = new_user['username']
                session['full_name'] = new_user['full_name']
                session['is_admin'] = bool(new_user['is_admin'])
                flash(f'Hoş geldiniz, {name}! Google hesabınızla kayıt oldunuz.', 'success')
                return redirect(url_for('dashboard'))
                
    except Exception as e:
        import traceback
        print(f"Google OAuth hatası: {e}")
        print(traceback.format_exc())
        flash(f'Google girişi sırasında hata oluştu: {str(e)}', 'error')
        return redirect(url_for('register'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Öğrenci dashboard"""
    student_id = session['user_id']
    
    with get_db() as conn:
        c = get_cursor(conn)
        
        # Son 30 günün çalışma verileri
        date_func = get_date_function(30)
        query = adapt_query(f'''
            SELECT date, SUM(hours) as total_hours, AVG(efficiency) as avg_efficiency
            FROM study_sessions
            WHERE student_id = ? AND date >= {date_func}
            GROUP BY date
            ORDER BY date DESC
        ''')
        c.execute(query, (student_id,))
        daily_stats = c.fetchall()
        
        # Toplam istatistikler
        query = adapt_query('''
            SELECT 
                COUNT(*) as total_sessions,
                SUM(hours) as total_hours,
                AVG(efficiency) as avg_efficiency,
                COUNT(DISTINCT date) as study_days
            FROM study_sessions
            WHERE student_id = ?
        ''')
        c.execute(query, (student_id,))
        stats = c.fetchone()
        
        # Son çalışma kayıtları
        query = adapt_query('''
            SELECT * FROM study_sessions
            WHERE student_id = ?
            ORDER BY date DESC, created_at DESC
            LIMIT 10
        ''')
        c.execute(query, (student_id,))
        recent_sessions = c.fetchall()
        
        # Sınav sonuçları
        query = adapt_query('''
            SELECT * FROM exam_results
            WHERE student_id = ?
            ORDER BY exam_date DESC, created_at DESC
        ''')
        c.execute(query, (student_id,))
        exams = c.fetchall()
        
        # Ortalama hesapla
        query = adapt_query('''
            SELECT AVG(score * 100.0 / max_score) as avg_percentage
            FROM exam_results
            WHERE student_id = ?
        ''')
        c.execute(query, (student_id,))
        avg_result = c.fetchone()
        
        # Streak bilgilerini al
        query = adapt_query('''
            SELECT current_streak, longest_streak, last_study_date
            FROM students
            WHERE id = ?
        ''')
        c.execute(query, (student_id,))
        streak_data = c.fetchone()
        
        # Streak değerlerini parse et
        current_streak = 0
        longest_streak = 0
        last_study_date = None

        if streak_data:
            if isinstance(streak_data, dict):
                current_streak = streak_data.get('current_streak', 0) or 0
                longest_streak = streak_data.get('longest_streak', 0) or 0
                last_study_date = streak_data.get('last_study_date')
            else:
                current_streak = streak_data[0] if len(streak_data) > 0 and streak_data[0] else 0
                longest_streak = streak_data[1] if len(streak_data) > 1 and streak_data[1] else 0
                last_study_date = streak_data[2] if len(streak_data) > 2 else None

        # Streak kırılma kontrolü (sadece bir kez göster)
        if not session.get('streak_warning_shown'):
            if last_study_date and current_streak > 0:
                from datetime import date, timedelta
                if isinstance(last_study_date, str):
                    last_date = datetime.strptime(last_study_date, '%Y-%m-%d').date()
                else:
                    last_date = last_study_date if isinstance(last_study_date, date) else last_study_date.date()

                today = date.today()
                yesterday = today - timedelta(days=1)

                # Eğer son çalışma bugün veya dün değilse, streak tehlikede
                if last_date < yesterday:
                    days_since = (today - last_date).days
                    flash(f'⚠️ Son çalışmanın {days_since} gün önce. Streak\'in sıfırlanmak üzere! Bugün çalış ve serini koru! 🔥', 'warning')
                    session['streak_warning_shown'] = True
            elif current_streak == 0 and last_study_date:
                # Streak zaten kırılmış
                if not session.get('streak_broken_shown'):
                    flash('Streak\'in kırıldı ama vazgeçme! Yeni bir seri başlat! 💪', 'info')
                    session['streak_broken_shown'] = True

    return render_template('dashboard.html',
                         daily_stats=daily_stats,
                         stats=stats,
                         recent_sessions=recent_sessions,
                         exams=exams,
                         avg_percentage=avg_result['avg_percentage'] if avg_result['avg_percentage'] else 0,
                         current_streak=current_streak,
                         longest_streak=longest_streak)

@app.route('/leaderboard')
@login_required
def leaderboard():
    """Yarışma/Leaderboard sayfası"""
    with get_db() as conn:
        c = get_cursor(conn)
        
        # Streak leaderboard (current_streak'e göre)
        query = adapt_query('''
            SELECT id, username, full_name, current_streak, longest_streak
            FROM students
            WHERE is_admin = FALSE OR is_admin = 0
            ORDER BY current_streak DESC, longest_streak DESC
            LIMIT 50
        ''')
        c.execute(query)
        streak_leaderboard = c.fetchall()
        
        # Toplam saat leaderboard
        query = adapt_query('''
            SELECT 
                s.id,
                s.username,
                s.full_name,
                COALESCE(SUM(ss.hours), 0) as total_hours,
                COUNT(DISTINCT ss.date) as study_days
            FROM students s
            LEFT JOIN study_sessions ss ON s.id = ss.student_id
            WHERE s.is_admin = FALSE OR s.is_admin = 0
            GROUP BY s.id, s.username, s.full_name
            ORDER BY total_hours DESC
            LIMIT 50
        ''')
        c.execute(query)
        hours_leaderboard = c.fetchall()
        
        # Çalışma sayısı leaderboard
        query = adapt_query('''
            SELECT 
                s.id,
                s.username,
                s.full_name,
                COUNT(ss.id) as total_sessions,
                COALESCE(AVG(ss.efficiency), 0) as avg_efficiency
            FROM students s
            LEFT JOIN study_sessions ss ON s.id = ss.student_id
            WHERE s.is_admin = FALSE OR s.is_admin = 0
            GROUP BY s.id, s.username, s.full_name
            ORDER BY total_sessions DESC
            LIMIT 50
        ''')
        c.execute(query)
        sessions_leaderboard = c.fetchall()
    
    return render_template('leaderboard.html',
                         streak_leaderboard=streak_leaderboard,
                         hours_leaderboard=hours_leaderboard,
                         sessions_leaderboard=sessions_leaderboard)

@app.route('/add-study', methods=['GET', 'POST'])
@login_required
def add_study():
    """Çalışma kaydı ekle"""
    if request.method == 'POST':
        try:
            date = request.form.get('date')
            subject = request.form.get('subject')
            hours_str = request.form.get('hours', '0')
            efficiency_str = request.form.get('efficiency', '50')
            notes = request.form.get('notes', '')
            difficulties = request.form.get('difficulties', '')
            
            # Validasyon
            if not date or not subject:
                flash('Tarih ve ders bilgisi gerekli!', 'error')
                return redirect(url_for('add_study'))
            
            try:
                hours = float(hours_str)
                efficiency = int(efficiency_str)
            except (ValueError, TypeError):
                flash('Saat ve verimlilik değerleri geçerli sayılar olmalı!', 'error')
                return redirect(url_for('add_study'))
            
            if hours <= 0:
                flash('Saat değeri 0\'dan büyük olmalı!', 'error')
                return redirect(url_for('add_study'))
            
            if efficiency < 0 or efficiency > 100:
                flash('Verimlilik 0-100 arasında olmalı!', 'error')
                return redirect(url_for('add_study'))
            
            # Veritabanına kaydet
            student_id = session.get('user_id')
            with get_db() as conn:
                c = get_cursor(conn)
                query = adapt_query('''
                    INSERT INTO study_sessions (student_id, date, subject, hours, efficiency, notes, difficulties)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''')
                c.execute(query, (student_id, date, subject, hours, efficiency, notes, difficulties))
                conn.commit()

            # Streak'i güncelle ve sonuca göre mesaj göster
            streak_result = update_streak(student_id, date)

            # Başarı mesajı
            flash('Çalışma kaydı başarıyla eklendi!', 'success')

            # Streak durumuna göre ek mesajlar
            if streak_result.get('same_day'):
                flash(f'Bugün için zaten çalışma kaydın var. Streak {streak_result.get("new_streak")} günde sabit kaldı.', 'info')
            elif streak_result.get('streak_increased'):
                flash(f'🔥 Harika! Streak\'in {streak_result.get("new_streak")} güne çıktı!', 'success')
            elif streak_result.get('broken'):
                flash(f'Streak kırıldı. Yeni başlangıç: {streak_result.get("new_streak")} gün. Vazgeçme! 💪', 'warning')

            return redirect(url_for('dashboard'))
            
        except Exception as e:
            import traceback
            print(f"HATA: {str(e)}")
            print(traceback.format_exc())
            flash(f'Bir hata oluştu: {str(e)}', 'error')
            return redirect(url_for('add_study'))
    
    return render_template('add_study.html')

@app.route('/add-exam', methods=['GET', 'POST'])
@login_required
def add_exam():
    """Sınav sonucu ekle"""
    if request.method == 'POST':
        exam_name = request.form.get('exam_name')
        score = float(request.form.get('score', 0))
        max_score = float(request.form.get('max_score', 100))
        exam_date = request.form.get('exam_date')
        
        if not exam_name or score < 0:
            flash('Sınav adı ve not bilgisi gerekli!', 'error')
            return redirect(url_for('add_exam'))
        
        with get_db() as conn:
            c = get_cursor(conn)
            query = adapt_query('''
                INSERT INTO exam_results (student_id, exam_name, score, max_score, exam_date)
                VALUES (?, ?, ?, ?, ?)
            ''')
            c.execute(query, (session['user_id'], exam_name, score, max_score, exam_date))
            conn.commit()
        
        flash('Sınav sonucu başarıyla eklendi!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_exam.html')

@app.route('/calculate-grade', methods=['POST'])
@login_required
def calculate_grade():
    """Ortalama hesaplayıcı - hedef ortalamaya ulaşmak için gerekli notları hesapla"""
    data = request.get_json()
    target_avg = float(data.get('target_avg', 0))
    
    if target_avg <= 0 or target_avg > 100:
        return jsonify({'success': False, 'error': 'Geçerli bir hedef ortalama girin (0-100)'})
    
    with get_db() as conn:
        c = get_cursor(conn)
        
        # Mevcut sınav sonuçlarını al
        query = adapt_query('''
            SELECT score, max_score FROM exam_results
            WHERE student_id = ?
            ORDER BY exam_date DESC, created_at DESC
        ''')
        c.execute(query, (session['user_id'],))
        exams = c.fetchall()
        
        if not exams:
            return jsonify({'success': False, 'error': 'Henüz sınav sonucu eklenmemiş'})
    
    # Mevcut ortalama
    total_weighted = sum(exam['score'] * 100.0 / exam['max_score'] for exam in exams)
    current_avg = total_weighted / len(exams)
    
    # Kalan sınav sayısı (kullanıcıdan alınacak)
    remaining_exams = int(data.get('remaining_exams', 1))
    
    if remaining_exams <= 0:
        return jsonify({'success': False, 'error': 'Kalan sınav sayısı 0\'dan büyük olmalı'})
    
    # Toplam ağırlık
    total_exams = len(exams) + remaining_exams
    target_total = target_avg * total_exams
    current_total = current_avg * len(exams)
    needed_total = target_total - current_total
    
    # Her sınav için gerekli ortalama
    needed_avg_per_exam = needed_total / remaining_exams if remaining_exams > 0 else 0
    
    # Eğer hedef ulaşılamazsa
    if needed_avg_per_exam > 100:
        return jsonify({
            'success': False,
            'error': f'Hedef ortalamaya ulaşmak için kalan {remaining_exams} sınavdan ortalama {needed_avg_per_exam:.2f} almanız gerekiyor (maksimum 100)',
            'current_avg': round(current_avg, 2),
            'target_avg': target_avg,
            'needed_avg': round(needed_avg_per_exam, 2)
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'current_avg': round(current_avg, 2),
        'target_avg': target_avg,
        'remaining_exams': remaining_exams,
        'needed_avg_per_exam': round(needed_avg_per_exam, 2),
        'message': f'Hedef ortalamaya ulaşmak için kalan {remaining_exams} sınavdan ortalama {needed_avg_per_exam:.2f} almanız gerekiyor.'
    })

@app.route('/api/stats')
@login_required
def api_stats():
    """İstatistik API - grafikler için"""
    student_id = session['user_id']
    
    with get_db() as conn:
        c = get_cursor(conn)
        
        # Son 30 günün günlük saatleri
        date_func = get_date_function(30)
        query = adapt_query(f'''
            SELECT date, SUM(hours) as total_hours
            FROM study_sessions
            WHERE student_id = ? AND date >= {date_func}
            GROUP BY date
            ORDER BY date ASC
        ''')
        c.execute(query, (student_id,))
        daily_hours = c.fetchall()
        
        # Ders bazında toplam saatler
        query = adapt_query('''
            SELECT subject, SUM(hours) as total_hours
            FROM study_sessions
            WHERE student_id = ?
            GROUP BY subject
            ORDER BY total_hours DESC
            LIMIT 10
        ''')
        c.execute(query, (student_id,))
        subject_hours = c.fetchall()
        
        # Verimlilik trendi (günlük ortalama - son 30 gün)
        query = adapt_query(f'''
            SELECT 
                date,
                AVG(efficiency) as avg_efficiency
            FROM study_sessions
            WHERE student_id = ? AND date >= {date_func}
            GROUP BY date
            ORDER BY date ASC
        ''')
        c.execute(query, (student_id,))
        efficiency_trend = c.fetchall()
    
    return jsonify({
        'daily_hours': [{'date': row['date'], 'hours': float(row['total_hours']) if row['total_hours'] else 0} for row in daily_hours],
        'subject_hours': [{'subject': row['subject'], 'hours': float(row['total_hours']) if row['total_hours'] else 0} for row in subject_hours],
        'efficiency_trend': [{'date': row['date'], 'efficiency': float(row['avg_efficiency']) if row['avg_efficiency'] else 0} for row in efficiency_trend]
    })

@app.route('/update-study/<int:session_id>', methods=['POST'])
@login_required
def update_study(session_id):
    """Çalışma kaydı güncelle"""
    try:
        data = request.get_json()
        
        # Veri doğrulama
        date = data.get('date')
        subject = data.get('subject')
        hours = data.get('hours')
        efficiency = data.get('efficiency')
        notes = data.get('notes', '')
        difficulties = data.get('difficulties', '')
        
        if not date or not subject or hours is None or efficiency is None:
            return jsonify({'success': False, 'error': 'Tüm zorunlu alanlar doldurulmalı!'}), 400
        
        hours = float(hours)
        efficiency = int(efficiency)
        
        if hours <= 0 or hours > 24:
            return jsonify({'success': False, 'error': 'Saat 0-24 arasında olmalı!'}), 400
        
        if efficiency < 0 or efficiency > 100:
            return jsonify({'success': False, 'error': 'Verimlilik 0-100 arasında olmalı!'}), 400
        
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Önce kaydın bu öğrenciye ait olduğunu kontrol et
            query = adapt_query('SELECT student_id FROM study_sessions WHERE id = ?')
            c.execute(query, (session_id,))
            study_record = c.fetchone()
            
            if not study_record:
                return jsonify({'success': False, 'error': 'Kayıt bulunamadı'}), 404
            
            if study_record['student_id'] != session.get('user_id'):
                return jsonify({'success': False, 'error': 'Bu kaydı güncelleme yetkiniz yok'}), 403
            
            # Kaydı güncelle
            query = adapt_query('''
                UPDATE study_sessions 
                SET date = ?, subject = ?, hours = ?, efficiency = ?, notes = ?, difficulties = ?
                WHERE id = ? AND student_id = ?
            ''')
            c.execute(query, (date, subject, hours, efficiency, notes, difficulties, session_id, session.get('user_id')))
            conn.commit()
            
            if c.rowcount > 0:
                return jsonify({'success': True, 'message': 'Çalışma kaydı başarıyla güncellendi!'})
            else:
                return jsonify({'success': False, 'error': 'Kayıt güncellenemedi!'}), 500
        
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-study/<int:session_id>', methods=['GET'])
@login_required
def get_study(session_id):
    """Çalışma kaydı bilgilerini getir"""
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Önce kaydın bu öğrenciye ait olduğunu kontrol et
            query = adapt_query('SELECT * FROM study_sessions WHERE id = ?')
            c.execute(query, (session_id,))
            study_record = c.fetchone()
            
            if not study_record:
                return jsonify({'success': False, 'error': 'Kayıt bulunamadı'}), 404
            
            if study_record['student_id'] != session.get('user_id'):
                return jsonify({'success': False, 'error': 'Bu kaydı görüntüleme yetkiniz yok'}), 403
            
            # Veriyi döndür
            return jsonify({
                'success': True,
                'data': {
                    'id': study_record['id'],
                    'date': study_record['date'],
                    'subject': study_record['subject'],
                    'hours': study_record['hours'],
                    'efficiency': study_record['efficiency'],
                    'notes': study_record['notes'] or '',
                    'difficulties': study_record['difficulties'] or ''
                }
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete-study/<int:session_id>', methods=['POST'])
@login_required
def delete_study(session_id):
    """Çalışma kaydı sil"""
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Önce kaydın bu öğrenciye ait olduğunu kontrol et
            query = adapt_query('SELECT student_id FROM study_sessions WHERE id = ?')
            c.execute(query, (session_id,))
            study_record = c.fetchone()
            
            if not study_record:
                return jsonify({'success': False, 'error': 'Kayıt bulunamadı'}), 404
            
            if study_record['student_id'] != session.get('user_id'):
                return jsonify({'success': False, 'error': 'Bu kaydı silme yetkiniz yok'}), 403
            
            # Kaydı sil
            query = adapt_query('DELETE FROM study_sessions WHERE id = ? AND student_id = ?')
            c.execute(query, (session_id, session.get('user_id')))
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete-exam/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):
    """Sınav sonucu sil"""
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Önce kaydın bu öğrenciye ait olduğunu kontrol et
            query = adapt_query('SELECT student_id FROM exam_results WHERE id = ?')
            c.execute(query, (exam_id,))
            exam_record = c.fetchone()
            
            if not exam_record:
                return jsonify({'success': False, 'error': 'Kayıt bulunamadı'}), 404
            
            if exam_record['student_id'] != session.get('user_id'):
                return jsonify({'success': False, 'error': 'Bu kaydı silme yetkiniz yok'}), 403
            
            # Kaydı sil
            query = adapt_query('DELETE FROM exam_results WHERE id = ? AND student_id = ?')
            c.execute(query, (exam_id, session.get('user_id')))
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin paneli - tüm öğrencilerin verilerini gör"""
    with get_db() as conn:
        c = get_cursor(conn)
        
        # Tüm öğrenciler
        if USE_SUPABASE:
            query = 'SELECT * FROM students WHERE is_admin = FALSE ORDER BY full_name'
        else:
            query = 'SELECT * FROM students WHERE is_admin = 0 ORDER BY full_name'
        c.execute(query)
        students = c.fetchall()
        
        # Her öğrenci için istatistikler
        student_stats = []
        for student in students:
            query = adapt_query('''
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(hours) as total_hours,
                    AVG(efficiency) as avg_efficiency,
                    COUNT(DISTINCT date) as study_days
                FROM study_sessions
                WHERE student_id = ?
            ''')
            c.execute(query, (student['id'],))
            stats = c.fetchone()
            
            query = adapt_query('''
                SELECT AVG(score * 100.0 / max_score) as avg_percentage
                FROM exam_results
                WHERE student_id = ?
            ''')
            c.execute(query, (student['id'],))
            exam_avg = c.fetchone()
            
            student_stats.append({
                'student': student,
                'stats': stats,
                'exam_avg': exam_avg['avg_percentage'] if exam_avg and exam_avg['avg_percentage'] else 0
            })
    
    return render_template('admin_dashboard.html', student_stats=student_stats)

@app.route('/admin/student/<int:student_id>')
@admin_required
def admin_student_detail(student_id):
    """Admin - öğrenci detay sayfası"""
    with get_db() as conn:
        c = get_cursor(conn)
        
        query = adapt_query('SELECT * FROM students WHERE id = ?')
        c.execute(query, (student_id,))
        student = c.fetchone()
        
        if not student:
            flash('Öğrenci bulunamadı!', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Çalışma kayıtları
        query = adapt_query('''
            SELECT * FROM study_sessions
            WHERE student_id = ?
            ORDER BY date DESC, created_at DESC
        ''')
        c.execute(query, (student_id,))
        sessions = c.fetchall()
        
        # Sınav sonuçları
        query = adapt_query('''
            SELECT * FROM exam_results
            WHERE student_id = ?
            ORDER BY exam_date DESC, created_at DESC
        ''')
        c.execute(query, (student_id,))
        exams = c.fetchall()
    
    return render_template('admin_student_detail.html', student=student, sessions=sessions, exams=exams)

@app.route('/admin/study/<int:session_id>/update', methods=['POST'])
@admin_required
def admin_update_study(session_id):
    """Admin - çalışma kaydı güncelle"""
    try:
        data = request.get_json()
        
        # Veri doğrulama
        date = data.get('date')
        subject = data.get('subject')
        hours = data.get('hours')
        efficiency = data.get('efficiency')
        notes = data.get('notes', '')
        difficulties = data.get('difficulties', '')
        
        if not date or not subject or hours is None or efficiency is None:
            return jsonify({'success': False, 'error': 'Tüm zorunlu alanlar doldurulmalı!'}), 400
        
        hours = float(hours)
        efficiency = int(efficiency)
        
        if hours <= 0 or hours > 24:
            return jsonify({'success': False, 'error': 'Saat 0-24 arasında olmalı!'}), 400
        
        if efficiency < 0 or efficiency > 100:
            return jsonify({'success': False, 'error': 'Verimlilik 0-100 arasında olmalı!'}), 400
        
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Kaydın var olduğunu kontrol et
            query = adapt_query('SELECT id FROM study_sessions WHERE id = ?')
            c.execute(query, (session_id,))
            if not c.fetchone():
                return jsonify({'success': False, 'error': 'Kayıt bulunamadı'}), 404
            
            # Kaydı güncelle
            query = adapt_query('''
                UPDATE study_sessions 
                SET date = ?, subject = ?, hours = ?, efficiency = ?, notes = ?, difficulties = ?
                WHERE id = ?
            ''')
            c.execute(query, (date, subject, hours, efficiency, notes, difficulties, session_id))
            conn.commit()
            
            if c.rowcount > 0:
                return jsonify({'success': True, 'message': 'Çalışma kaydı başarıyla güncellendi!'})
            else:
                return jsonify({'success': False, 'error': 'Kayıt güncellenemedi!'}), 500
        
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/study/<int:session_id>', methods=['GET'])
@admin_required
def admin_get_study(session_id):
    """Admin - çalışma kaydı bilgilerini getir"""
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            query = adapt_query('SELECT * FROM study_sessions WHERE id = ?')
            c.execute(query, (session_id,))
            study_record = c.fetchone()
            
            if not study_record:
                return jsonify({'success': False, 'error': 'Kayıt bulunamadı'}), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'id': study_record['id'],
                    'date': study_record['date'],
                    'subject': study_record['subject'],
                    'hours': study_record['hours'],
                    'efficiency': study_record['efficiency'],
                    'notes': study_record['notes'] or '',
                    'difficulties': study_record['difficulties'] or ''
                }
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/student/<int:student_id>/study/add', methods=['POST'])
@admin_required
def admin_add_study(student_id):
    """Admin - öğrenciye çalışma kaydı ekle"""
    try:
        data = request.get_json()
        
        # Veri doğrulama
        date = data.get('date')
        subject = data.get('subject')
        hours = data.get('hours')
        efficiency = data.get('efficiency')
        notes = data.get('notes', '')
        difficulties = data.get('difficulties', '')
        
        if not date or not subject or hours is None or efficiency is None:
            return jsonify({'success': False, 'error': 'Tüm zorunlu alanlar doldurulmalı!'}), 400
        
        hours = float(hours)
        efficiency = int(efficiency)
        
        if hours <= 0 or hours > 24:
            return jsonify({'success': False, 'error': 'Saat 0-24 arasında olmalı!'}), 400
        
        if efficiency < 0 or efficiency > 100:
            return jsonify({'success': False, 'error': 'Verimlilik 0-100 arasında olmalı!'}), 400
        
        # Öğrencinin var olduğunu kontrol et
        with get_db() as conn:
            c = get_cursor(conn)
            query = adapt_query('SELECT id FROM students WHERE id = ?')
            c.execute(query, (student_id,))
            if not c.fetchone():
                return jsonify({'success': False, 'error': 'Öğrenci bulunamadı'}), 404
            
            # Çalışma kaydı ekle
            query = adapt_query('''
                INSERT INTO study_sessions (student_id, date, subject, hours, efficiency, notes, difficulties)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''')
            c.execute(query, (student_id, date, subject, hours, efficiency, notes, difficulties))
            conn.commit()

            # Streak'i güncelle
            update_streak(student_id, date)

            return jsonify({'success': True, 'message': 'Çalışma kaydı başarıyla eklendi!'})
        
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/exam/<int:exam_id>/update', methods=['POST'])
@admin_required
def admin_update_exam(exam_id):
    """Admin - sınav sonucu güncelle"""
    try:
        data = request.get_json()
        
        exam_name = data.get('exam_name')
        score = data.get('score')
        max_score = data.get('max_score', 100)
        exam_date = data.get('exam_date', '')
        
        if not exam_name or score is None:
            return jsonify({'success': False, 'error': 'Tüm zorunlu alanlar doldurulmalı!'}), 400
        
        score = float(score)
        max_score = float(max_score)
        
        if score < 0 or max_score <= 0:
            return jsonify({'success': False, 'error': 'Notlar geçerli olmalı!'}), 400
        
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Kaydın var olduğunu kontrol et
            query = adapt_query('SELECT id FROM exam_results WHERE id = ?')
            c.execute(query, (exam_id,))
            if not c.fetchone():
                return jsonify({'success': False, 'error': 'Kayıt bulunamadı'}), 404
            
            # Kaydı güncelle
            query = adapt_query('''
                UPDATE exam_results 
                SET exam_name = ?, score = ?, max_score = ?, exam_date = ?
                WHERE id = ?
            ''')
            c.execute(query, (exam_name, score, max_score, exam_date if exam_date else None, exam_id))
            conn.commit()
            
            if c.rowcount > 0:
                return jsonify({'success': True, 'message': 'Sınav sonucu başarıyla güncellendi!'})
            else:
                return jsonify({'success': False, 'error': 'Kayıt güncellenemedi!'}), 500
        
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/exam/<int:exam_id>', methods=['GET'])
@admin_required
def admin_get_exam(exam_id):
    """Admin - sınav sonucu bilgilerini getir"""
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            query = adapt_query('SELECT * FROM exam_results WHERE id = ?')
            c.execute(query, (exam_id,))
            exam_record = c.fetchone()
            
            if not exam_record:
                return jsonify({'success': False, 'error': 'Kayıt bulunamadı'}), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'id': exam_record['id'],
                    'exam_name': exam_record['exam_name'],
                    'score': exam_record['score'],
                    'max_score': exam_record['max_score'],
                    'exam_date': exam_record['exam_date'] or ''
                }
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/student/<int:student_id>/exam/add', methods=['POST'])
@admin_required
def admin_add_exam(student_id):
    """Admin - öğrenciye sınav sonucu ekle"""
    try:
        data = request.get_json()
        
        exam_name = data.get('exam_name')
        score = data.get('score')
        max_score = data.get('max_score', 100)
        exam_date = data.get('exam_date', '')
        
        if not exam_name or score is None:
            return jsonify({'success': False, 'error': 'Tüm zorunlu alanlar doldurulmalı!'}), 400
        
        score = float(score)
        max_score = float(max_score)
        
        if score < 0 or max_score <= 0:
            return jsonify({'success': False, 'error': 'Notlar geçerli olmalı!'}), 400
        
        # Öğrencinin var olduğunu kontrol et
        with get_db() as conn:
            c = get_cursor(conn)
            query = adapt_query('SELECT id FROM students WHERE id = ?')
            c.execute(query, (student_id,))
            if not c.fetchone():
                return jsonify({'success': False, 'error': 'Öğrenci bulunamadı'}), 404
            
            # Sınav sonucu ekle
            query = adapt_query('''
                INSERT INTO exam_results (student_id, exam_name, score, max_score, exam_date)
                VALUES (?, ?, ?, ?, ?)
            ''')
            c.execute(query, (student_id, exam_name, score, max_score, exam_date if exam_date else None))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Sınav sonucu başarıyla eklendi!'})
        
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/student/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    """Admin - öğrenciyi sil"""
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Öğrencinin var olup olmadığını ve admin olmadığını kontrol et
            query = adapt_query('SELECT id, username, is_admin FROM students WHERE id = ?')
            c.execute(query, (student_id,))
            student = c.fetchone()
            
            if not student:
                return jsonify({'success': False, 'error': 'Öğrenci bulunamadı!'}), 404
            
            # Admin kullanıcılarını silmeyi engelle
            if USE_SUPABASE:
                is_admin = student.get('is_admin', False)
            else:
                is_admin = bool(student.get('is_admin', 0))
            
            if is_admin:
                return jsonify({'success': False, 'error': 'Admin kullanıcıları silinemez!'}), 403
            
            # Öğrenciyi sil (CASCADE ile tüm ilişkili kayıtlar otomatik silinir)
            query = adapt_query('DELETE FROM students WHERE id = ? AND is_admin = ?')
            if USE_SUPABASE:
                c.execute(query, (student_id, False))
            else:
                c.execute(query, (student_id, 0))
            
            conn.commit()
            
            # Silinen kayıt sayısını kontrol et
            if c.rowcount > 0:
                flash(f'Öğrenci ({student["username"]}) başarıyla silindi!', 'success')
                return jsonify({'success': True, 'message': 'Öğrenci başarıyla silindi!'})
            else:
                return jsonify({'success': False, 'error': 'Öğrenci silinemedi!'}), 500
    
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

# DERS PROGRAMI ROUTE'LARI

@app.route('/schedule')
@login_required
def schedule():
    """Öğrenci ders programı sayfası"""
    student_id = session['user_id']
    
    with get_db() as conn:
        c = get_cursor(conn)
        
        # Öğrencinin ders programlarını al
        query = adapt_query('''
            SELECT * FROM schedules
            WHERE student_id = ?
            ORDER BY created_at DESC
        ''')
        c.execute(query, (student_id,))
        schedules = c.fetchall()
        
        # Aktif program varsa onu al
        active_schedule = None
        schedule_items = []
        completions = {}
        
        if schedules:
            active_schedule = schedules[0]  # En son oluşturulan program
            
            # Program öğelerini al
            query = adapt_query('''
                SELECT * FROM schedule_items
                WHERE schedule_id = ?
                ORDER BY day_of_week, start_time
            ''')
            c.execute(query, (active_schedule['id'],))
            schedule_items = c.fetchall()
            
            # Tamamlama durumlarını al (bugün ve geçmiş)
            from datetime import date
            today_date = date.today()
            
            for item in schedule_items:
                query = adapt_query('''
                    SELECT * FROM schedule_completions
                    WHERE schedule_item_id = ? AND completion_date <= ?
                    ORDER BY completion_date DESC
                ''')
                c.execute(query, (item['id'], today_date))
                item_completions = c.fetchall()
                # SQLite için boolean dönüşümü
                processed_completions = []
                for comp in item_completions:
                    comp_dict = dict(comp)
                    if not USE_SUPABASE:
                        comp_dict['is_completed'] = bool(comp_dict['is_completed'])
                    processed_completions.append(comp_dict)
                completions[item['id']] = processed_completions
    
    from datetime import date
    today = str(date.today())
    
    return render_template('schedule.html', 
                         schedules=schedules,
                         active_schedule=active_schedule,
                         schedule_items=schedule_items,
                         completions=completions,
                         today=today)

@app.route('/schedule/create', methods=['GET', 'POST'])
@login_required
def create_schedule():
    """Ders programı oluştur"""
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name', '')
        description = data.get('description', '')
        items = data.get('items', [])
        
        if not name:
            return jsonify({'success': False, 'error': 'Program adı gerekli!'})
        
        student_id = session['user_id']
        
        try:
            with get_db() as conn:
                c = get_cursor(conn)
                
                # Program oluştur
                query = adapt_query('''
                    INSERT INTO schedules (student_id, name, description)
                    VALUES (?, ?, ?)
                ''')
                c.execute(query, (student_id, name, description))
                conn.commit()
                
                # Yeni oluşturulan program ID'sini al
                if USE_SUPABASE:
                    c.execute('SELECT LASTVAL()')
                else:
                    c.execute('SELECT last_insert_rowid()')
                schedule_id = c.fetchone()[0]
                
                # Program öğelerini ekle
                for item in items:
                    query = adapt_query('''
                        INSERT INTO schedule_items 
                        (schedule_id, day_of_week, start_time, end_time, subject, location, instructor)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''')
                    c.execute(query, (
                        schedule_id,
                        int(item.get('day_of_week', 0)),
                        item.get('start_time', ''),
                        item.get('end_time', ''),
                        item.get('subject', ''),
                        item.get('location', ''),
                        item.get('instructor', '')
                    ))
                
                conn.commit()
            
            return jsonify({'success': True, 'schedule_id': schedule_id})
        except Exception as e:
            import traceback
            print(f"HATA: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return render_template('schedule.html')

@app.route('/schedule/<int:schedule_id>/update', methods=['POST'])
@login_required
def update_schedule(schedule_id):
    """Ders programını güncelle"""
    data = request.get_json()
    name = data.get('name', '')
    description = data.get('description', '')
    items = data.get('items', [])
    
    student_id = session['user_id']
    
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Programın öğrenciye ait olduğunu kontrol et
            query = adapt_query('SELECT student_id FROM schedules WHERE id = ?')
            c.execute(query, (schedule_id,))
            schedule = c.fetchone()
            
            if not schedule:
                return jsonify({'success': False, 'error': 'Program bulunamadı!'}), 404
            
            if schedule['student_id'] != student_id:
                return jsonify({'success': False, 'error': 'Bu programı düzenleme yetkiniz yok!'}), 403
            
            # Programı güncelle
            query = adapt_query('''
                UPDATE schedules 
                SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''')
            c.execute(query, (name, description, schedule_id))
            
            # Eski öğeleri sil
            query = adapt_query('DELETE FROM schedule_items WHERE schedule_id = ?')
            c.execute(query, (schedule_id,))
            
            # Yeni öğeleri ekle
            for item in items:
                query = adapt_query('''
                    INSERT INTO schedule_items 
                    (schedule_id, day_of_week, start_time, end_time, subject, location, instructor)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''')
                c.execute(query, (
                    schedule_id,
                    int(item.get('day_of_week', 0)),
                    item.get('start_time', ''),
                    item.get('end_time', ''),
                    item.get('subject', ''),
                    item.get('location', ''),
                    item.get('instructor', '')
                ))
            
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/schedule/<int:student_id>/data')
@admin_required
def admin_get_schedule_data(student_id):
    """Admin - öğrenci ders programı verilerini getir"""
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Öğrencinin aktif programını bul
            query = adapt_query('SELECT * FROM schedules WHERE student_id = ? ORDER BY created_at DESC LIMIT 1')
            c.execute(query, (student_id,))
            schedule = c.fetchone()
            
            if not schedule:
                return jsonify({'success': True, 'schedule': None, 'items': []})
            
            # Program öğelerini al
            query = adapt_query('SELECT * FROM schedule_items WHERE schedule_id = ? ORDER BY day_of_week, start_time')
            c.execute(query, (schedule['id'],))
            items = c.fetchall()
            
            # Items'ı dict formatına çevir
            items_list = []
            for item in items:
                items_list.append({
                    'day_of_week': item['day_of_week'],
                    'start_time': item['start_time'],
                    'end_time': item['end_time'],
                    'subject': item['subject'],
                    'location': item['location'] or '',
                    'instructor': item['instructor'] or ''
                })
            
            return jsonify({
                'success': True,
                'schedule': {
                    'id': schedule['id'],
                    'name': schedule['name'],
                    'description': schedule['description'] or ''
                },
                'items': items_list
            })
    
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/schedule/<int:schedule_id>/data')
@login_required
def get_schedule_data(schedule_id):
    """Ders programı verilerini getir (düzenleme için)"""
    student_id = session['user_id']
    
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Program bilgisi
            query = adapt_query('SELECT * FROM schedules WHERE id = ?')
            c.execute(query, (schedule_id,))
            schedule = c.fetchone()
            
            if not schedule:
                return jsonify({'success': False, 'error': 'Program bulunamadı!'}), 404
            
            if schedule['student_id'] != student_id:
                return jsonify({'success': False, 'error': 'Bu programı görüntüleme yetkiniz yok!'}), 403
            
            # Program öğeleri
            query = adapt_query('''
                SELECT * FROM schedule_items
                WHERE schedule_id = ?
                ORDER BY day_of_week, start_time
            ''')
            c.execute(query, (schedule_id,))
            items = c.fetchall()
            
            # SQLite için boolean dönüşümü
            items_list = []
            for item in items:
                item_dict = dict(item)
                items_list.append(item_dict)
        
        return jsonify({
            'success': True,
            'schedule': dict(schedule),
            'items': items_list
        })
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/schedule/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    """Ders programını sil"""
    student_id = session['user_id']
    
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Programın öğrenciye ait olduğunu kontrol et
            query = adapt_query('SELECT student_id FROM schedules WHERE id = ?')
            c.execute(query, (schedule_id,))
            schedule = c.fetchone()
            
            if not schedule:
                return jsonify({'success': False, 'error': 'Program bulunamadı!'}), 404
            
            if schedule['student_id'] != student_id:
                return jsonify({'success': False, 'error': 'Bu programı silme yetkiniz yok!'}), 403
            
            # Programı sil (CASCADE ile öğeler de silinir)
            query = adapt_query('DELETE FROM schedules WHERE id = ?')
            c.execute(query, (schedule_id,))
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/schedule/item/<int:item_id>/complete', methods=['POST'])
@login_required
def complete_schedule_item(item_id):
    """Ders programı öğesini tamamla"""
    data = request.get_json()
    completion_date = data.get('date', '')
    is_completed = data.get('is_completed', True)
    notes = data.get('notes', '')
    
    if not completion_date:
        from datetime import date
        completion_date = str(date.today())
    
    student_id = session['user_id']
    
    try:
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Öğenin öğrenciye ait olduğunu kontrol et
            query = adapt_query('''
                SELECT s.student_id 
                FROM schedule_items si
                JOIN schedules s ON si.schedule_id = s.id
                WHERE si.id = ?
            ''')
            c.execute(query, (item_id,))
            result = c.fetchone()
            
            if not result:
                return jsonify({'success': False, 'error': 'Ders bulunamadı!'}), 404
            
            if result['student_id'] != student_id:
                return jsonify({'success': False, 'error': 'Bu dersi işaretleme yetkiniz yok!'}), 403
            
            # Tamamlama durumunu kontrol et (aynı tarih için)
            query = adapt_query('''
                SELECT id FROM schedule_completions
                WHERE schedule_item_id = ? AND completion_date = ?
            ''')
            c.execute(query, (item_id, completion_date))
            existing = c.fetchone()
            
            if existing:
                # Güncelle
                if USE_SUPABASE:
                    completed_value = is_completed
                else:
                    completed_value = 1 if is_completed else 0
                
                query = adapt_query('''
                    UPDATE schedule_completions
                    SET is_completed = ?, notes = ?
                    WHERE id = ?
                ''')
                c.execute(query, (completed_value, notes, existing['id']))
            else:
                # Yeni kayıt oluştur
                if USE_SUPABASE:
                    completed_value = is_completed
                else:
                    completed_value = 1 if is_completed else 0
                
                query = adapt_query('''
                    INSERT INTO schedule_completions 
                    (schedule_item_id, completion_date, is_completed, notes)
                    VALUES (?, ?, ?, ?)
                ''')
                c.execute(query, (item_id, completion_date, completed_value, notes))
            
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/schedule/<int:student_id>/update', methods=['POST'])
@admin_required
def admin_update_schedule(student_id):
    """Admin - öğrenci ders programını güncelle"""
    try:
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description', '')
        items = data.get('items', [])
        
        if not name:
            return jsonify({'success': False, 'error': 'Program adı gereklidir!'}), 400
        
        with get_db() as conn:
            c = get_cursor(conn)
            
            # Öğrencinin var olduğunu kontrol et
            query = adapt_query('SELECT id FROM students WHERE id = ?')
            c.execute(query, (student_id,))
            if not c.fetchone():
                return jsonify({'success': False, 'error': 'Öğrenci bulunamadı'}), 404
            
            # Öğrencinin aktif programını bul
            query = adapt_query('SELECT id FROM schedules WHERE student_id = ? ORDER BY created_at DESC LIMIT 1')
            c.execute(query, (student_id,))
            schedule = c.fetchone()
            
            schedule_id = None
            if schedule:
                schedule_id = schedule['id']
                # Mevcut programı güncelle
                query = adapt_query('''
                    UPDATE schedules 
                    SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''')
                c.execute(query, (name, description, schedule_id))
                
                # Eski öğeleri sil
                query = adapt_query('DELETE FROM schedule_items WHERE schedule_id = ?')
                c.execute(query, (schedule_id,))
            else:
                # Yeni program oluştur
                query = adapt_query('''
                    INSERT INTO schedules (student_id, name, description)
                    VALUES (?, ?, ?)
                ''')
                c.execute(query, (student_id, name, description))
                
                # Yeni oluşturulan program ID'sini al
                if USE_SUPABASE:
                    from psycopg2.extras import RealDictCursor
                    c2 = conn.cursor(cursor_factory=RealDictCursor)
                    c2.execute('SELECT LASTVAL() as lastval')
                    result = c2.fetchone()
                    schedule_id = result['lastval']
                    c2.close()
                else:
                    c.execute('SELECT last_insert_rowid()')
                    schedule_id = c.fetchone()[0]
            
            # Yeni öğeleri ekle
            for item in items:
                query = adapt_query('''
                    INSERT INTO schedule_items 
                    (schedule_id, day_of_week, start_time, end_time, subject, location, instructor)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''')
                c.execute(query, (
                    schedule_id,
                    int(item.get('day_of_week', 0)),
                    item.get('start_time', ''),
                    item.get('end_time', ''),
                    item.get('subject', ''),
                    item.get('location', ''),
                    item.get('instructor', '')
                ))
            
            conn.commit()
        
        return jsonify({'success': True, 'message': 'Ders programı başarıyla güncellendi!'})
    except Exception as e:
        import traceback
        print(f"HATA: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/schedule/<int:student_id>')
@admin_required
def admin_view_schedule(student_id):
    """Admin - öğrenci ders programını görüntüle"""
    with get_db() as conn:
        c = get_cursor(conn)
        
        # Öğrenci bilgisi
        query = adapt_query('SELECT * FROM students WHERE id = ?')
        c.execute(query, (student_id,))
        student = c.fetchone()
        
        if not student:
            flash('Öğrenci bulunamadı!', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Öğrencinin ders programlarını al
        query = adapt_query('''
            SELECT * FROM schedules
            WHERE student_id = ?
            ORDER BY created_at DESC
        ''')
        c.execute(query, (student_id,))
        schedules = c.fetchall()
        
        # Aktif program varsa onu al
        active_schedule = None
        schedule_items = []
        completions = {}
        
        if schedules:
            active_schedule = schedules[0]  # En son oluşturulan program
            
            # Program öğelerini al
            query = adapt_query('''
                SELECT * FROM schedule_items
                WHERE schedule_id = ?
                ORDER BY day_of_week, start_time
            ''')
            c.execute(query, (active_schedule['id'],))
            schedule_items = c.fetchall()
            
            # Tamamlama durumlarını al
            from datetime import date
            today_date = date.today()
            
            for item in schedule_items:
                query = adapt_query('''
                    SELECT * FROM schedule_completions
                    WHERE schedule_item_id = ? AND completion_date <= ?
                    ORDER BY completion_date DESC
                ''')
                c.execute(query, (item['id'], today_date))
                item_completions = c.fetchall()
                # SQLite için boolean dönüşümü
                processed_completions = []
                for comp in item_completions:
                    comp_dict = dict(comp)
                    if not USE_SUPABASE:
                        comp_dict['is_completed'] = bool(comp_dict['is_completed'])
                    processed_completions.append(comp_dict)
                completions[item['id']] = processed_completions
    
    from datetime import date
    today = str(date.today())
    
    return render_template('admin_schedule.html',
                         student=student,
                         schedules=schedules,
                         active_schedule=active_schedule,
                         schedule_items=schedule_items,
                         completions=completions,
                         today=today)

if __name__ == '__main__':
    try:
        # Veritabanını başlat
        print("🔄 Veritabanı başlatılıyor...")
        init_db()
        print("✅ Veritabanı hazır.")
        
        port = int(os.environ.get('PORT', 5002))
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        
        print("=" * 60)
        print("📚 Öğrenci Çalışma Takip Sistemi - EducationalTR")
        print("=" * 60)
        print(f"🌐 Uygulama başlatılıyor: http://0.0.0.0:{port}")
        if USE_SUPABASE:
            print("📁 Veritabanı: Supabase PostgreSQL")
        else:
            print("📁 Veritabanı: SQLite (Local)")
        print("=" * 60)
        
        app.run(debug=debug, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"❌ Uygulama başlatılırken hata: {e}")
        import traceback
        traceback.print_exc()
        raise

