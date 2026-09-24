from flask import Blueprint, request, jsonify
from app.database import chatbot_lead_kaydet
import re
import os
import google.generativeai as genai

chatbot_bp = Blueprint('chatbot_bp', __name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(user_message)
        
        return jsonify({"status": "success", "reply": response.text}), 200
    except Exception as e:
        # Arka planda gerçek bir API hatası varsa Render loglarında görebilmemiz için logluyoruz
        print(f"Gemini API Hatası: {str(e)}")
        return jsonify({
            "status": "success", 
            "reply": "Maalesef buna cevap veremem, ancak bana \"Sıfır iade sistemi nasıl çalışıyor?\" veya \"AI kombin motoru fotoğraflarımı nasıl analiz ediyor?\" gibi sorular sorabilirsiniz. Size nasıl yardımcı olabilirim?"
        }), 200