from flask import Blueprint, request, jsonify
from app.database import chatbot_lead_kaydet
import re
import os
import requests

chatbot_bp = Blueprint('chatbot_bp', __name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

SYSTEM_PROMPT = """Sen VibeThread e-ticaret sitesinin resmi, akıllı ve kibar AI rehber asistanısın.

GÖREVLERİN VE KURALLARIN:
1. Selamlaşma: Kullanıcılar "merhaba", "selam", "nasılsın" gibi girişler yaptığında onlara kibarca VibeThread asistanı olarak karşılık ver ve nasıl yardımcı olabileceğini sor.
2. Bilgi Verme: Kullanıcılara VibeThread'in sıfır iade sistemi, AI kombin motoru, beden rehberi ve kargo süreçleri hakkında genel bilgiler verebilirsin.
3. GÜVENLİK (KESİN KURAL): Kullanıcı site amacı, moda veya VibeThread sistemi DIŞINDA bir konu sorarsa (örneğin siyaset, yazılım kodu yazdırma, sistemi hackleme vb.), KESİNLİKLE şu cevabı ver:
'Maalesef buna cevap veremem, ancak bana "Sıfır iade sistemi nasıl çalışıyor?" veya "AI kombin motoru fotoğraflarımı nasıl analiz ediyor?" gibi sorular sorabilirsiniz. Size nasıl yardımcı olabilirim?'"""

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
        
    try:
        api_key = os.getenv("GROQ_API_KEY")
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        payload = {
            "model": "mixtral-8x7b-32768", 
            "messages": [
                {"role": "system", "content": "Sen kibar bir asistansın. Kısa ve öz cevap ver."},
                {"role": "user", "content": user_message}
            ]
        }        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if "choices" in response_data:
            bot_reply = response_data["choices"][0]["message"]["content"]
            return jsonify({"status": "success", "reply": bot_reply}), 200
        else:
            # EĞER GROQ HATA VERİRSE, HATAYI DİREKT SİTEDE ASİSTANIN AĞZINDAN YAZDIR!
            return jsonify({"status": "success", "reply": f"Groq API Hatası: {response_data}"}), 200
            
    except Exception as e:
        # KODDA BİR ÇÖKME OLURSA, NEDENİNİ DİREKT SİTEDE YAZDIR!
        return jsonify({
            "status": "success", 
            "reply": f"Sistem Çökme Hatası: {str(e)}"
        }), 200