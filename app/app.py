from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, upsert_user, get_db_connection, update_user_status, log_user_activity
from chatbot_routes import chatbot_bp

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://rustuakkan7.wixstudio.com"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "ngrok-skip-browser-warning"]
    }
}, supports_credentials=True)

init_db(app)
app.register_blueprint(chatbot_bp)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    ad_soyad = data.get('ad_soyad')
    telefon = data.get('telefon')
    mail = data.get('mail')
    sifre = data.get('sifre')
    
    if not all([ad_soyad, telefon, mail, sifre]):
        return jsonify({"success": False, "message": "Tüm alanlar zorunludur."}), 400
        
    sifre_hash = generate_password_hash(sifre)
    
    try:
        user_id = upsert_user(ad_soyad, telefon, mail, sifre_hash, role="user")
        return jsonify({"success": True, "message": "Kayıt başarılı.", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Bu telefon veya e-posta zaten kayıtlı. Hata: {str(e)}"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = data.get('identifier')
    sifre = data.get('sifre')
    
    if not identifier or not sifre:
        return jsonify({"success": False, "message": "Bilgiler eksik."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kullanicilar WHERE mail = ? OR telefon = ?", (identifier, identifier))
    user = cursor.fetchone()
    conn.close()
    
    hash_key = "sifre_hash" if "sifre_hash" in user.keys() else "s_hashing"
    
    if user and check_password_hash(user[hash_key], sifre):
        update_user_status(user["id"], is_online=True)
        log_user_activity(user["id"], page_visited="Login")
        
        return jsonify({
            "success": True,
            "message": "Giriş başarılı.",
            "user": {
                "id": user["id"],
                "ad_soyad": user["ad_soyad"],
                "mail": user["mail"],
                "role": user["role"]
            }
        }), 200
    else:
        return jsonify({"success": False, "message": "Hatalı bilgi veya şifre."}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if user_id:
        update_user_status(user_id, is_online=False)
        return jsonify({"success": True, "message": "Çıkış yapıldı."}), 200
    return jsonify({"success": False, "message": "Kullanıcı ID bulunamadı."}), 400

@app.route('/api/admin/dashboard', methods=['POST', 'GET'])
def admin_dashboard():
    data = request.get_json() if request.is_json else request.args
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "message": "Yetki doğrulanamadı."}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT role FROM kullanicilar WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user or user["role"] != 'admin':
        conn.close()
        return jsonify({"success": False, "message": "Bu alana erişim yetkiniz yok."}), 403
    
    cursor.execute("SELECT id, ad_soyad, mail, last_active FROM kullanicilar WHERE is_online = 1")
    online_users = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, ad_soyad, mail, role, is_online, last_active, kayit_tarihi FROM kullanicilar")
    all_users = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('''
        SELECT user_logs.*, kullanicilar.ad_soyad, kullanicilar.mail 
        FROM user_logs 
        JOIN kullanicilar ON user_logs.kullanici_id = kullanicilar.id 
        ORDER BY user_logs.timestamp DESC LIMIT 50
    ''')
    activity_logs = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM corporate_secrets")
    corporate_secrets = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        "success": True,
        "online_users": online_users,
        "all_users": all_users,
        "activity_logs": activity_logs,
        "corporate_secrets": corporate_secrets
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)