from flask import Blueprint, request, jsonify
from app.database import chatbot_lead_kaydet
import re
import os
import requests

chatbot_bp = Blueprint('chatbot_bp', __name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

SYSTEM_PROMPT = """Sen VibeThread e-ticaret sitesinin resmi, akıllı ve kibar AI rehber asistanısın.
Kullanıcılara sıfır iade sistemi, AI kombin motoru ve beden rehberi hakkında akıcı, profesyonel ve yardımcı yanıtlar ver."""

@chatbot_bp.route('/api/chatbot/lead', methods=['POST'])
def save_chatbot_lead():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Geçersiz veri formatı."}), 400
        
    ad = data.get('ad', '').strip()
    soyad = data.get('soyad', '').strip()
    ad_soyad = f"{ad} {soyad}".strip()
    
    telefon = data.get('telefon', '').strip()
    mail = data.get('mail', '').strip()
    
    if not ad or not soyad or not mail:
        return jsonify({"status": "error", "message": "Ad, Soyad ve E-posta alanları zorunludur."}), 400
        
    if not re.match(EMAIL_REGEX, mail):
        return jsonify({"status": "error", "message": "Lütfen geçerli bir e-posta adresi giriniz."}), 400
        
    try:
        lead_id = chatbot_lead_kaydet(ad_soyad, telefon, mail)
        return jsonify({
            "status": "success", 
            "message": "Bilgileriniz başarıyla kaydedildi, asistan başlatılıyor.",
            "lead_id": lead_id
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Veritabanı hatası: {str(e)}"}), 500

@chatbot_bp.route('/api/chatbot/ask', methods=['POST'])
def ask_chatbot():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"status": "error", "message": "Boş bir mesaj gönderilemez."}), 400
        
    son_hata = ""

    # 1. YÖNTEM: GOOGLE GEMINI API (Eğer Render'da GEMINI_API_KEY varsa direkt buradan dener)
    try:
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            gemini_payload = {
                "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nKullanıcı: {user_message}"}]}]
            }
            res = requests.post(gemini_url, json=gemini_payload, headers={'Content-Type': 'application/json'}, timeout=6)
            if res.status_code == 200:
                data_res = res.json()
                if "candidates" in data_res:
                    reply = data_res["candidates"][0]["content"]["parts"][0]["text"]
                    return jsonify({"status": "success", "reply": reply.strip()}), 200
    except Exception as e:
        son_hata += f"Gemini Hatası: {str(e)} | "

    # 2. YÖNTEM: GROQ VE OPENAI UYUMLU TÜM MODELLER (Sırayla hepsini dener)
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            headers = {
                'Authorization': f'Bearer {groq_key}',
                'Content-Type': 'application/json'
            }
            
            # Dünyada ne kadar güncel ve aktif model varsa hepsini buraya yığdık
            tum_modeller = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "llama-3.1-70b-versatile",
                "gemma2-9b-it",
                "llama3-8b-8192",
                "llama3-70b-8192",
                "mixtral-8x7b-32768",
                "llama-3.2-3b-preview",
                "llama-3.2-1b-preview"
            ]
            
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            for m in tum_modeller:
                payload = {
                    "model": m,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ]
                }
                try:
                    r = requests.post(url, json=payload, headers=headers, timeout=5)
                    r_data = r.json()
                    if r.status_code == 200 and "choices" in r_data:
                        reply = r_data["choices"][0]["message"]["content"]
                        return jsonify({"status": "success", "reply": reply.strip()}), 200
                    else:
                        son_hata += f"Model {m}: {str(r_data.get('error', {}).get('message', 'Hata'))} | "
                except Exception as ex:
                    son_hata += f"Model {m} İstisna: {str(ex)} | "
                    continue
    except Exception as e:
        son_hata += f"Groq Genel Hata: {str(e)} | "

    # Eğer akıllı ağdaki hiçbir modelden yanıt dönemezse detaylı hatayı döner
    return jsonify({
        "status": "success", 
        "reply": f"Tüm yapay zeka modelleri ve ağlar denendi ancak erişim sağlanamadı. Detay: {son_hata}"
    }), 200