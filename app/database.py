import sqlite3
import os

DB_PATH = "instance/leads.db"

def _ensure_directories():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs("instance/kullanicilar", exist_ok=True)

def baglanti_kur():
    _ensure_directories()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(app):
    with app.app_context():
        conn = baglanti_kur()
        cursor = conn.cursor()
        
        cursor.executescript("""
            -- 1. ADIM: ESKİ TABLOYU KOMPLE SİL
            DROP TABLE IF EXISTS kullanicilar;

            -- 2. ADIM: YENİ TABLOYU ŞİFRE ZORUNLULUĞU OLMADAN KUR
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_soyad TEXT NOT NULL,
                telefon TEXT UNIQUE NOT NULL,
                mail TEXT UNIQUE NOT NULL,
                sifre_hash TEXT,  -- DİKKAT: 'NOT NULL' kuralını kaldırdık!
                role TEXT NOT NULL DEFAULT 'user',
                is_online BOOLEAN DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS kiyafetler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER,
                dosya_yolu TEXT NOT NULL,
                kategori TEXT,
                renk TEXT,
                eklenme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar (id)
            );

            CREATE TABLE IF NOT EXISTS kombin_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER,
                istek_detayi TEXT,
                yapay_zeka_yaniti TEXT,
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar (id)
            );

            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER,
                page_visited TEXT NOT NULL,
                duration_seconds INTEGER DEFAULT 0,
                login_time TIMESTAMP,
                logout_time TIMESTAMP,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar (id)
            );

            CREATE TABLE IF NOT EXISTS corporate_secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        conn.close()

def veri_tabanini_baslat(app):
    return init_db(app)

def kullanici_ozel_klasor_olustur(user_id):
    _ensure_directories()
    wardrobe_dir = f"instance/kullanicilar/{user_id}/kiyafetler"
    chats_dir = f"instance/kullanicilar/{user_id}/konusmalar"
    os.makedirs(wardrobe_dir, exist_ok=True)
    os.makedirs(chats_dir, exist_ok=True)
    return wardrobe_dir, chats_dir

def kullaniciyi_dogrula_veya_kaydet(ad_soyad, telefon, mail, sifre_hash, role="user"):
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM kullanicilar WHERE telefon = ? OR mail = ?", (telefon, mail))
    row = cursor.fetchone()
    
    if row:
        user_id = row["id"]
        cursor.execute(
            "UPDATE kullanicilar SET ad_soyad = ?, mail = ?, sifre_hash = ? WHERE id = ?",
            (ad_soyad, mail, sifre_hash, user_id)
        )
    else:
        cursor.execute(
            "INSERT INTO kullanicilar (ad_soyad, telefon, mail, sifre_hash, role) VALUES (?, ?, ?, ?, ?)",
            (ad_soyad, telefon, mail, sifre_hash, role)
        )
        user_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    kullanici_ozel_klasor_olustur(user_id)
    return user_id

def kombin_gecmisi_kaydet(user_id, prompt, response):
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO kombin_gecmisi (kullanici_id, istek_detayi, yapay_zeka_yaniti) VALUES (?, ?, ?)",
        (user_id, prompt, response)
    )
    conn.commit()
    conn.close()

def kullanici_durum_guncelle(user_id, is_online):
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE kullanicilar SET is_online = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?",
        (int(is_online), user_id)
    )
    conn.commit()
    conn.close()

def kullanici_aktivite_logla(user_id, page_visited, duration=0):
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_logs (kullanici_id, page_visited, duration_seconds) VALUES (?, ?, ?)",
        (user_id, page_visited, duration)
    )
    conn.commit()
    conn.close()

def chatbot_lead_kaydet(ad_soyad, telefon, mail):
    conn = baglanti_kur()
    cursor = conn.cursor()
    
    # sifre_hash'i tamamen çıkardık, çünkü veritabanında gerçekten yok!
    cursor.execute(
        "INSERT INTO kullanicilar (ad_soyad, telefon, mail, role) VALUES (?, ?, ?, ?)",
        (ad_soyad, telefon, mail, "lead")
    )
    
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return lead_id