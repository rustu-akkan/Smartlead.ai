import re
import os
import uuid
from flask import request, jsonify
from app import app
from app.database import kullaniciyi_dogrula_veya_kaydet, baglanti_kur, kullanici_ozel_klasor_olustur
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, render_template

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE_MB = 5

def dosya_uzantisi_gecerli_mi(dosya_adi):
    return '.' in dosya_adi and dosya_adi.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    ad_soyad = data.get('ad_soyad')
    telefon = data.get('telefon')
    mail = data.get('mail')
    sifre = data.get('sifre')
    
    if not ad_soyad or not telefon or not mail or not sifre:
        return jsonify({"status": "error", "message": "Tüm alanların doldurulması zorunludur!"}), 400
        
    if not re.match(EMAIL_REGEX, mail):
        return jsonify({
            "status": "error", 
            "message": "Lütfen @gmail.com veya @hotmail.com gibi geçerli ve standart bir e-posta adresi giriniz."
        }), 400

    if not re.match(PASSWORD_REGEX, sifre):
        return jsonify({
            "status": "error", 
            "message": "Şifreniz en az 8 karakter uzunluğunda olmalı; en az bir büyük harf, bir küçük harf, bir rakam ve bir özel karakter içermelidir."
        }), 400

    try:
        baglanti = baglanti_kur()
        cursor = baglanti.cursor()
        cursor.execute("SELECT id, mail, telefon FROM kullanicilar WHERE mail = ? OR telefon = ?", (mail, telefon))
        mevcut_kullanici = cursor.fetchone()
        baglanti.close()
        
        if mevcut_kullanici:
            if mevcut_kullanici["mail"] == mail:
                return jsonify({
                    "status": "error", 
                    "message": "Bu e-posta adresi zaten kullanımda. Lütfen farklı bir e-posta adresi giriniz veya giriş yapmayı deneyiniz."
                }), 400
            if mevcut_kullanici["telefon"] == telefon:
                return jsonify({
                    "status": "error", 
                    "message": "Bu telefon numarası zaten sistemde kayıtlı."
                }), 400

        sifre_hash = generate_password_hash(sifre)
        kullanici_id = kullaniciyi_dogrula_veya_kaydet(ad_soyad, telefon, mail, sifre_hash)
        
        return jsonify({
            "status": "success", 
            "message": "Kayıt başarıyla tamamlandı!",
            "kullanici_id": kullanici_id
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": f"Bir hata oluştu: {str(e)}"}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    mail = data.get('mail')
    sifre = data.get('sifre')
    
    if not mail or not sifre:
        return jsonify({"status": "error", "message": "E-posta ve şifre alanları zorunludur!"}), 400
        
    try:
        baglanti = baglanti_kur()
        cursor = baglanti.cursor()
        cursor.execute("SELECT id, ad_soyad, sifre_hash FROM kullanicilar WHERE mail = ?", (mail,))
        kullanici = cursor.fetchone()
        baglanti.close()
        
        if not kullanici:
            return jsonify({
                "status": "redirect_register", 
                "message": "Bu e-posta adresi ile kayıtlı bir hesap bulunamadı. Lütfen önce kayıt olunuz.",
                "action_url": "/kayit-ol"
            }), 200
            
        if not check_password_hash(kullanici["sifre_hash"], sifre):
            return jsonify({
                "status": "error", 
                "message": "Girdiğiniz şifre hatalı. Lütfen şifrenizi kontrol edip tekrar deneyiniz."
            }), 200
            
        return jsonify({
            "status": "success",
            "message": f"Hoş geldiniz, {kullanici['ad_soyad']}!",
            "kullanici_id": kullanici["id"]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Bir hata oluştu: {str(e)}"}), 500

@app.route('/api/kiyafet-ekle', methods=['POST'])
def add_clothing():
    kullanici_id = request.form.get('kullanici_id')
    kategori = request.form.get('kategori')
    renk = request.form.get('renk')
    
    if not kullanici_id:
        return jsonify({"status": "error", "message": "Kullanıcı kimliği gereklidir!"}), 400
        
    if 'dosya' not in request.files:
        return jsonify({"status": "error", "message": "Yüklenecek bir dosya bulunamadı!"}), 400
        
    dosya = request.files['dosya']
    
    if dosya.filename == '':
        return jsonify({"status": "error", "message": "Dosya seçilmedi!"}), 400
        
    if not dosya_uzantisi_gecerli_mi(dosya.filename):
        return jsonify({
            "status": "error", 
            "message": "Desteklenmeyen dosya formatı! Sadece .png, .jpg, .jpeg ve .webp uzantılı görsel dosyaları yükleyebilirsiniz."
        }), 400

    dosya.seek(0, os.SEEK_END)
    dosya_boyutu = dosya.tell()
    dosya.seek(0)
    
    if dosya_boyutu > MAX_FILE_SIZE_MB * 1024 * 1024:
        return jsonify({
            "status": "error", 
            "message": f"Dosya boyutu çok büyük! Maksimum dosya boyutu {MAX_FILE_SIZE_MB} MB olmalıdır."
        }), 400

    try:
        kiyafet_dizini, _ = kullanici_ozel_klasor_olustur(kullanici_id)
        dosya_uzantisi = dosya.filename.rsplit('.', 1)[1].lower()
        benzersiz_dosya_adi = f"{uuid.uuid4().hex}.{dosya_uzantisi}"
        dosya_yolu = os.path.join(kiyafet_dizini, benzersiz_dosya_adi)
        dosya.save(dosya_yolu)
        
        baglanti = baglanti_kur()
        cursor = baglanti.cursor()
        cursor.execute(
            "INSERT INTO kiyafetler (kullanici_id, dosya_yolu, kategori, renk) VALUES (?, ?, ?, ?)",
            (kullanici_id, dosya_yolu, kategori, renk)
        )
        baglanti.commit()
        kiyafet_id = cursor.lastrowid
        baglanti.close()
        
        return jsonify({
            "status": "success",
            "message": "Kıyafet başarıyla yüklendi ve kaydedildi.",
            "kiyafet_id": kiyafet_id,
            "dosya_yolu": dosya_yolu
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": f"Bir hata oluştu: {str(e)}"}), 500

@app.route('/api/stil-danismani', methods=['POST'])
def stil_danismani():
    data = request.get_json()
    kullanici_id = data.get('kullanici_id')
    kullanici_mesaji = data.get('mesaj', '')
    tercih = data.get('tercih')
    
    if not kullanici_id:
        return jsonify({"status": "error", "message": "Kullanıcı kimliği gereklidir!"}), 400
        
    try:
        baglanti = baglanti_kur()
        cursor = baglanti.cursor()
        cursor.execute("SELECT id, kategori, renk, dosya_yolu FROM kiyafetler WHERE kullanici_id = ?", (kullanici_id,))
        kiyafetler = cursor.fetchall()
        baglanti.close()
        
        gardirot = [dict(k) for k in kiyafetler]
        
        if not tercih and any(kelime in kullanici_mesaji.lower() for kelime in ["kombin", "giysi", "ne giysem", "hazırla"]):
            if len(gardirot) > 0:
                return jsonify({
                    "status": "needs_preference",
                    "message": "Gardırobuna yüklediğin kıyafetleri kullanarak mı, yoksa sezonun global trendlerine göre sıfırdan bir konsept kombin mi hazırlayayım?",
                    "secenekler": ["Gardırobumdan Eşleştir", "Global Trendlere Göre"]
                }), 200
            else:
                tercih = "trend"
                
        if tercih == "gardirot":
            if not gardirot:
                return jsonify({
                    "status": "error",
                    "message": "Gardırobunuzda kayıtlı kıyafet bulunamadığı için bu seçeneği kullanamıyoruz. Önce kıyafet yüklemelisiniz."
                }), 400
            
            ai_yaniti = f"Gardırobundaki {len(gardirot)} parça incelendi. Senin için en uyumlu parçaları bir araya getirdik."
            
        elif tercih == "trend" or len(gardirot) == 0:
            ai_yaniti = f"Sezonun global trendlerine göre '{kullanici_mesaji}' talebiniz için bu dönem pastel tonlar ön planda."
            
        else:
            ai_yaniti = f"İsteğiniz alındı: '{kullanici_mesaji}'. Stil danışmanınız olarak size özel moda önerileri hazırlanıyor..."

        return jsonify({
            "status": "success",
            "yanit": ai_yaniti,
            "gardirot_durumu": f"{len(gardirot)} parça mevcut"
        }), 200
    

    except Exception as e:
        return jsonify({"status": "error", "message": f"Bir hata oluştu: {str(e)}"}), 500
    from flask import render_template

@app.route('/')
def ana_sayfa():
    return render_template('index.html')