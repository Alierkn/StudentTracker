"""
Öğrenci Çalışma Takip Sistemi
Öğrencilerin günlük çalışma verilerini, sınav sonuçlarını ve gelişimlerini takip eder
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
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

# Veritabanını başlat (Gunicorn için)
# Gunicorn ile çalışırken if __name__ == '__main__' çalışmaz
# Bu yüzden app oluşturulurken init_db() çağrılmalı
try:
    print("🔄 Veritabanı başlatılıyor...")
    init_db()
    print("✅ Veritabanı hazır.")
    if USE_SUPABASE:
        print("📁 Veritabanı: Supabase PostgreSQL")
    else:
        print("📁 Veritabanı: SQLite (Local)")
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
    
    return render_template('dashboard.html',
                         daily_stats=daily_stats,
                         stats=stats,
                         recent_sessions=recent_sessions,
                         exams=exams,
                         avg_percentage=avg_result['avg_percentage'] if avg_result['avg_percentage'] else 0)

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
            with get_db() as conn:
                c = get_cursor(conn)
                query = adapt_query('''
                    INSERT INTO study_sessions (student_id, date, subject, hours, efficiency, notes, difficulties)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''')
                c.execute(query, (session.get('user_id'), date, subject, hours, efficiency, notes, difficulties))
                conn.commit()
            
            flash('Çalışma kaydı başarıyla eklendi!', 'success')
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

