# VibeThread - SmartLead AI Projesi

Merhaba, bu repoda bitirme projem kapsamında geliştirdiğim "VibeThread" adlı yapay zeka destekli stil asistanının kaynak kodları bulunuyor. 

Projenin temel amacı şu: Siteye giren ziyaretçiler, kendi tarzlarını bulmak için yapay zeka ile sohbet ediyor. Biz de bu sohbet başlamadan önce veya sohbet sırasında kullanıcıdan iletişim bilgilerini alıp (lead toplayıp) arka plandaki veritabanımıza kaydediyoruz. Sistem B2C (müşteri yüzü) ve B2B (yönetim paneli) olarak iki kısımdan oluşuyor.

## Mimari ve Kod Yapısı
Projeyi geliştirirken en çok dikkat ettiğim nokta **Sorumlulukların Ayrılığı (Separation of Concerns)** ilkesi oldu. Spagetti koddan kaçınmak için her işlevi kendi modülüne ayırdım:

* **`config.py`**: Bütün API key ve temel ayarları merkezden yönettiğim dosya.
* **`database.py`**: Veritabanı (SQLite) ile konuşan tek yer burası. SQL Injection riskine karşı sorguları `?` parametreleriyle güvenli hale getirdim.
* **`services/ai_service.py`**: Sadece LLM ile iletişim kuran katman. Groq API üzerinden Llama 3 modelini burada çalıştırıyorum. 
* **`routes.py`**: Yönlendirme (Controller) mantığım. Gelen GET/POST isteklerini alıp ilgili servislere dağıtıyor, içinde kesinlikle SQL veya AI kodu barındırmıyor.

## Kullandığım Teknolojiler
* **Backend:** Python, Flask, SQLite
* **AI Entegrasyonu:** Groq API (Llama-3.1-8b-instant)
* **Frontend:** Wix Studio & Velo (wix-fetch ile API haberleşmesi)
* **Sunucu / Yayınlama:** Gunicorn ile Render üzerinde canlıya alındı.

## Projeyi Lokalinizde Çalıştırmak İçin
1. Repoyu bilgisayarınıza çekin: `git clone https://github.com/rustu-akkan/Smartlead.ai`
2. Sanal ortamı (venv) kurup aktif edin: `python -m venv venv`
3. Kütüphaneleri indirin: `pip install -r requirements.txt`
4. Ana dizinde bir `.env` dosyası açıp içine kendi `GROQ_API_KEY` ve `SECRET_KEY` değerlerinizi girin.
5. `python run.py` yazarak sunucuyu başlatın ve `localhost:5000/health` adresinden test edin.
