# 🔐 Google OAuth Kurulum Kılavuzu

## 📋 Google OAuth Credentials Oluşturma

### 1. Google Cloud Console'a Giriş

1. [Google Cloud Console](https://console.cloud.google.com/) → Giriş yapın
2. Yeni bir proje oluşturun veya mevcut projeyi seçin

### 2. OAuth Consent Screen Ayarları

1. Sol menüden **APIs & Services** > **OAuth consent screen**
2. **User Type**: External seçin → Create
3. **App information**:
   - App name: `EducationalTR Öğrenci Takip Sistemi`
   - User support email: E-posta adresiniz
   - Developer contact: E-posta adresiniz
4. **Scopes**: Varsayılan scope'lar yeterli (email, profile, openid)
5. **Test users**: Test için kullanıcı e-postaları ekleyin (isteğe bağlı)
6. **Save and Continue** → **Back to Dashboard**

### 3. OAuth 2.0 Client ID Oluşturma

1. **APIs & Services** > **Credentials**
2. **+ CREATE CREDENTIALS** → **OAuth client ID**
3. **Application type**: Web application
4. **Name**: `EducationalTR Web Client`
5. **Authorized JavaScript origins**:
   - Local: `http://localhost:5002`
   - Production: `https://your-app.onrender.com` (veya deploy URL'iniz)
6. **Authorized redirect URIs**:
   - Local: `http://localhost:5002/google-callback`
   - Production: `https://your-app.onrender.com/google-callback`
7. **Create** → Client ID ve Client Secret'i kopyalayın

### 4. Environment Variables Ekleme

#### Local (.env dosyası):

```env
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

#### Production (Render.com/Railway):

1. Dashboard → Environment Variables
2. Yeni variable ekle:
   - **Name**: `GOOGLE_CLIENT_ID`
   - **Value**: `your-client-id-here.apps.googleusercontent.com`
3. Yeni variable ekle:
   - **Name**: `GOOGLE_CLIENT_SECRET`
   - **Value**: `your-client-secret-here`
4. Deploy'u yeniden başlatın

## ✅ Test

1. Uygulamayı başlatın
2. Login veya Register sayfasına gidin
3. "Google ile Giriş Yap" veya "Google ile Kayıt Ol" butonuna tıklayın
4. Google hesabınızla giriş yapın
5. Başarılı olursa dashboard'a yönlendirilirsiniz

## 🔒 Güvenlik Notları

- ✅ Client Secret'i asla GitHub'a push etmeyin
- ✅ `.env` dosyası `.gitignore`'da (güvenli)
- ✅ Production'da HTTPS kullanın
- ✅ Redirect URI'leri doğru yapılandırın

## 🐛 Sorun Giderme

**"Google OAuth yapılandırılmamış" hatası:**
- Environment variables'ı kontrol edin
- `GOOGLE_CLIENT_ID` ve `GOOGLE_CLIENT_SECRET` ekli mi?

**"Redirect URI mismatch" hatası:**
- Google Cloud Console'da redirect URI'yi kontrol edin
- Production URL'inizi eklediğinizden emin olun

**"authlib not found" hatası:**
- `pip install authlib` çalıştırın
- `requirements.txt`'de `authlib>=1.3.0` var mı kontrol edin

## 📝 Önemli

- Google OAuth credentials olmadan da sistem çalışır (sadece Google butonu çalışmaz)
- Normal kullanıcı adı/şifre ile kayıt olma devam eder
- Google OAuth opsiyonel bir özelliktir

