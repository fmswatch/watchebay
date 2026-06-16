import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")

genai.configure(api_key=GEMINI_API_KEY)

def ilanlari_tara():
    if not os.path.exists("liste.txt"):
        print("liste.txt dosyası bulunamadı!")
        return
        
    with open("liste.txt", "r", encoding="utf-8") as f:
        sayfa_icerigi = f.read().strip()

    if len(sayfa_icerigi) < 50:
        print("liste.txt dosyasının içi boş veya çok kısa!")
        return

    print("Kopyalanan Ebay içeriği yapay zekaya gönderiliyor...")

    prompt = f"""
    Aşağıda sana bir Ebay arama sayfasının ham metin içerikleri veriliyor.
    Bu metnin içindeki saat ilanlarını bul. 
    Bulduğun en güncel ilanların modelini, mekanizmasını ve fiyatını analiz et.
    Piyasa değerine göre kelepir mi, ederi mi yoksa pahalı mı belirt.
    Analizi tamamen Türkçe, kısa ve net maddeler halinde yap.

    Ebay Verisi:
    {sayfa_icerigi[:15000]}
    """

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        analiz = response.text
        
        # Mail Gönder
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = GMAIL_USER
        msg['Subject'] = "📢 Garantili Ebay Saat Analiz Raporu"
        msg.attach(MIMEText(analiz, 'plain', 'utf-8'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.close()
        print("Email başarıyla gönderildi!")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    ilanlari_tara()
