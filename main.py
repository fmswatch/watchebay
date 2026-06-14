import os
import smtplib
import feedparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai

# 1. Ayarları Buluttan Al
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
EBAY_URL = os.getenv("EBAY_URL")

# 2. Gemini Yapay Zekayı Başlat
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. Ebay İlanlarını Çek
feed = feedparser.parse(EBAY_URL)
rapor_icerigi = ""

print(f"{len(feed.entries)} adet ilan bulundu. Analiz ediliyor...")

# Sadece ilk 20 ilanı tara (Kota dostu)
for entry in feed.entries[:20]:
    ilan_basligi = entry.title
    ilan_linki = entry.link
    ilan_ozet = entry.description if 'description' in entry else "Açıklama yok"
    
    # Yapay Zekaya Sor
    prompt = f"""
    Sen profesyonel bir lüks ve vintage saat eksperisin. Aşağıdaki Ebay ilanını incele:
    Başlık: {ilan_basligi}
    Özet: {ilan_ozet}
    
    Lütfen bu saatin tahmini piyasa değerini, kondisyon risklerini ve bu ilanın bir 'FIRSAT' olup olmadığını yorumla. 
    Kısa, net ve Türkçe bir özet çıkar.
    """
    
    try:
        response = model.generate_content(prompt)
        ai_yorumu = response.text
    except:
        ai_yorumu = "Yapay zeka analizi sırasında bir hata oluştu."
        
    rapor_icerigi += f"<h3><a href='{ilan_linki}'>{ilan_basligi}</a></h3><p>{ai_yorumu}</p><hr>"

# 4. Raporu Gmail ile Kendine Gönder
if rapor_icerigi:
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "Günlük Ebay Zeno Watch Otomatik Raporu 🚨"
    
    msg.attach(MIMEText(f"<html><body><h2>Günün Potansiyel Saat Fırsatları</h2>{rapor_icerigi}</body></html>", 'html', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.close()
        print("Rapor başarıyla Gmail adresine gönderildi!")
    except Exception as e:
        print(f"E-posta gönderilirken hata oluştu: {e}")
else:
    print("Yeni ilan bulunamadı.")
