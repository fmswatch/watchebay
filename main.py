import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')

CAMP_ID = "5339157033"
ARAMALAR = ["tissot+uhr+herren", "cartier+uhr", "hamilton+uhr"]

def rapor_olustur():
    tum_mesajlar = "📢 EPN DESTEKLİ GÜNLÜK SAAT RAPORU\n"
    tum_mesajlar += "=========================================\n\n"
    
    for kelime in ARAMALAR:
        # Ebay Partner Network (EPN) kurallarına uygun resmi yönlendirme linki
        resmi_link = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10&mkcid=1&mkrid=707-53477-19255-0&siteid=77&campid={CAMP_ID}&customid=bot-rapor"
        
        tum_mesajlar += f"⌚ Marka/Arama: {kelime.replace('+', ' ').upper()}\n"
        tum_mesajlar += f"🔗 En Yeni İlanlar (Resmi Link):\n{resmi_link}\n"
        tum_mesajlar += f"{'-'*40}\n\n"
        
    mail_gonder(tum_mesajlar)

def mail_gonder(icerik):
    if not GMAIL_USER or not GMAIL_PASS:
        print("HATA: GitHub Secrets ayarlarında GMAIL_USER veya GMAIL_PASS eksik!")
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "📢 EPN Güncel Ebay Saat Raporu"
    msg.attach(MIMEText(icerik, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.close()
        print("Email başarıyla gönderildi!")
    except Exception as e:
        print(f"Email hatası: {e}")

if __name__ == "__main__":
    rapor_olustur()
