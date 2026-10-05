import requests
from config import Config

class AIServiceError(Exception):
    """AI Servisi hata sınıfı"""
    pass

def ai_service(prompt, history=None):
    """
    Groq API kullanarak kullanıcının mesajına dinamik yanıt üretir.
    
    :param prompt: Kullanıcının gönderdiği son mesaj (str)
    :param history: Önceki sohbet geçmişi (list)
    :return: AI tarafından üretilen yanıt metni (str)
    """
    if not getattr(Config, 'GROQ_API_KEY', None):
        raise AIServiceError("Groq API anahtarı (.env / Config) tanımlanmamış.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {Config.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Sistem talimatını ve şirket bağlamını ekliyoruz
    messages = [
        {"role": "system", "content": getattr(Config, 'BUSINESS_CONTEXT', 'Sen yardımcı bir asistansın.')}
    ]

    # Varsa geçmiş konuşmaları listeye ekle
    if history and isinstance(history, list):
        for msg in history:
            messages.append(msg)

    # Kullanıcının son mesajını ekle
    messages.append({"role": "user", "content": prompt})

    # Groq OpenAI uyumlu payload yapısı
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_data = response.json()

        if response.status_code != 200:
            error_msg = res_data.get('error', {}).get('message', 'Bilinmeyen API hatası')
            raise AIServiceError(f"Groq API Hatası ({response.status_code}): {error_msg}")

        # Modelin ürettiği dinamik cevabı çekip döndürüyoruz
        reply_content = res_data['choices'][0]['message']['content']
        return reply_content

    except requests.exceptions.RequestException as e:
        raise AIServiceError(f"Bağlantı hatası oluştu: {str(e)}")
    except (KeyError, IndexError):
        raise AIServiceError("API'den beklenen formatta yanıt alınamadı.")
    except Exception as e:
        raise AIServiceError(f"AI Servis Hatası: {str(e)}")