from flask import Blueprint, request, jsonify
from app.chatbot_db import chatbot_lead_kaydet
import re
import os
import requests

chatbot_bp = Blueprint('chatbot_bp', __name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

# xAI Grok API Yapılandırması (Environment üzerinden veya doğrudan anahtar)
GROK_API_KEY = os.getenv("GROK_API_KEY", "buraya_grok_api_anahtarinizi_yazın")
GROK_API_URL = "https://api.x.ai/v1/chat/completions" # xAI standart endpoint

SYSTEM_PROMPT = """
Sen VibeThread e-ticaret sitesinin resmi ve özel AI rehber asistanısın. Yalnızca sıfır iade sistemi, AI kombin motoru, beden rehberi, kargo süreçleri ve site kullanımı hakkında bilgi verebilirsin. 
Eğer kullanıcı site dışı bir konu sorarsa (örneğin yemek tarifi, siyaset, genel kültür vb.), kesinlikle şu kalıpta yanıt ver: 
'Maalesef buna cevap veremem, ancak bana "Sıfır iade sistemi nasıl çalışıyor?" veya "AI kombin motoru fotoğraflarımı nasıl analiz ediyor?" gibi sorular sorabilirsiniz. Size nasıl yardımcı olabilirim?'
"""

@chatbot_bp.route('/api/chatbot/lead', methods=['POST'])
def save_chatbot_lead():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Geçersiz veri formatı."}), 400
        
    ad_soyad = data.get('ad_soyad', '').strip()
    telefon = data.get('telefon', '').strip()
    mail = data.get('mail', '').strip()
    
    if not ad_soyad or not mail:
        return jsonify({"status": "error", "message": "Ad Soyad ve E-posta alanları zorunludur."}), 400
        
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
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    
    payload = {
        "model": "grok-beta", # Veya güncel xAI modeli
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(GROK_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            bot_reply = res_data['choices'][0]['message']['content']
            return jsonify({"status": "success", "reply": bot_reply}), 200
        else:
            return jsonify({"status": "error", "message": "Yapay zeka servisine şu an ulaşılamıyor."}), 502
    except Exception as e:
        # API anahtarı girilmediği veya internet kesintisi olduğu durumlarda sistemin çökmemesi için yedek yanıt
        return jsonify({
            "status": "success", 
            "reply": "Maalesef buna cevap veremem, ancak bana \"Sıfır iade sistemi nasıl çalışıyor?\" veya \"AI kombin motoru fotoğraflarımı nasıl analiz ediyor?\" gibi sorular sorabilirsiniz. Size nasıl yardımcı olabilirim?"
        }), 200