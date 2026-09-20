import os
from google import generativeai as genai
from config import Yapilandirma
from database import kullanici_gecmisini_getir, kombin_gecmisine_ekle

# Gemini API anahtarını güvenli yapılandırma sınıfından alıp yapılandırıyoruz
genai.configure(api_key=Yapilandirma.GEMINI_API_ANAHTARI)

def ai_yanit_uret(kullanici_id, kullanici_mesaji, resim_yolu=None):
    """
    Kullanıcının kimliğini, geçmiş kombin hafızasını ve varsa yüklediği kıyafet görselini 
    Gemini modeline aktararak kişiselleştirilmiş moda ve stil yanıtı üretir.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        gecmis_veriler = kullanici_gecmisini_getir(kullanici_id)
        hafiza_metni = ""
        if gecmis_veriler:
            hafiza_metni = "\nKullanıcının Geçmiş Tercihleri ve Kombinleri:\n"
            for g in gecmis_veriler:
                hafiza_metni += f"- İstek: {g['istek_detayi']} | Yanıt: {g['yapay_zeka_yaniti']}\n"
        tam_baglam = f"{Yapilandirma.ISLETME_BAGLAMI}\n{hafiza_metni}"
        icerik_listesi = [tam_baglam, f"Kullanıcı Mesajı: {kullanici_mesaji}"]
        if resim_yolu and os.path.exists(resim_yolu):
            # Görsel dosyayı Gemini'nin okuyabileceği formata çeviriyoruz
            import PIL.Image
            gorsel = PIL.Image.open(resim_yolu)
            icerik_listesi.append(gorsel)
            icerik_listesi.append("Lütfen bu kıyafet görselini analiz et, renklerini ve 2026 trendlerine uygun kombin önerilerini sun.")
        yanit = model.generate_content(icerik_listesi)
        ai_metin = yanit.text
        kombin_gecmisine_ekle(kullanici_id, kullanici_mesaji, ai_metin)
        return ai_metin
    except Exception as e:
        return f"Moda asistanımız şu an yoğun bir stil provasında! Lütfen biraz sonra tekrar dene. (Hata Detayı: {str(e)})"