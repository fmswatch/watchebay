import feedparser
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# API ve Giriş Bilgileri (GitHub Secrets'tan gelir)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")

genai.configure(api_key=GEMINI_API_KEY)

def ilanlari_tara():
    # liste.txt dosyasındaki tüm linkleri oku
    if not os.path.exists("liste.txt"):
        print("liste.txt dosyası bulunamadı!")
        return
        
    with open("liste.txt", "r") as f:
        linkler = [line.strip() for line in f if line.strip()]

    tum_mesajlar = ""
    toplam_ilan = 0

    # Her bir filtre linkini sırayla tara
    for url in linkler:
        print(f"Taranan Filtre: {url}")
        feed = feedparser.parse(url)
        
        if not feed.entries:
            continue

        # Her filtre için en güncel 3 ilanı al (Mail şişmesin diye)
        for entry in feed.entries[:3]:
            toplam_ilan += 1
            baslik = entry.title
            link = entry.link
            detay = entry.get("description", "Detay yok")

            # Yapay Zekaya Gönderilecek Soruyu Hazırla
            prompt = f"""
            Aşağıdaki Ebay saat ilanını incele. 
            Saatin modelini, mekanizmasını (otomatik mi, quartz mı) ve durumunu analiz et.
            Bu saate piyasa değerine göre tahmini bir fiyat biç ve şu anki fiyatı kelepir mi, ederi mi yoksa pahalı mı belirt.
            Analizi tamamen Türkçe, kısa ve çok net maddeler halinde yap.

            İlan Başlığı: {baslik}
            İlan Detayı: {detay}
            """

            try:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                analiz = response.text
            except Exception as e:
                analiz = f"Yapay zeka analizi yapılamadı: {e}"

            # Rapor formatını oluştur
            tum_mesajlar += f"### ⌚ İlan: {baslik}\n"
            tum_mesajlar += f"* **Link:** {link}\n"
            tum_mesajlar += f"* **Yapay Zeka Analizi ve Fiyat Biçme:**\n{analiz}\n"
            tum_mesajlar += "\n" + "-"*40 + "\n\n"

    print(f"Toplam {toplam_ilan} adet ilan analiz edildi.")
    
    if toplam_ilan > 0:
        mail_gonder(tum_mesajlar)
    else:
        print("Tüm filtrelerde yeni ilan bulunamadı.")

def mail_gonder(icerik):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "📢 Günlük Ebay Saat Analiz Raporu"
    
    # İçeriği düz metin olarak ekleme
    msg.attach(MIMEText(icerik, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.close()
        print("Email başarıyla gönderildi!")
    except Exception as e:
        print(f"Email gönderilirken hata oluştu: {e}")

if __name__ == "__main__":
    ilanlari_tara()
