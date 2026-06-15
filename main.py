import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import urllib.parse

# API ve Giriş Bilgileri
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")

genai.configure(api_key=GEMINI_API_KEY)

def ilanlari_tara():
    if not os.path.exists("liste.txt"):
        print("liste.txt dosyası bulunamadı!")
        return
        
    with open("liste.txt", "r") as f:
        linkler = [line.strip() for line in f if line.strip()]

    tum_mesajlar = ""
    toplam_ilan = 0

    for url in linkler:
        print(f"Taranan Filtre (Google Köprüsü ile): {url}")
        
        # Ebay linkini Google Script üzerinden dolaylı yoldan çağırıyoruz
        payload = {'url': url}
        hedef_url = GOOGLE_SCRIPT_URL + "?" + urllib.parse.urlencode(payload)
        
        try:
            response = requests.get(hedef_url, timeout=40)
            if response.status_code != 200:
                print(f"Google Köprüsü hatası, Durum Kodu: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            ilanlar = soup.find_all('li', class_='s-item')
            
            sayac = 0
            for ilan in ilanlar:
                if sayac >= 3:  # Filtre başına en güncel 3 ilanı al
                    break
                    
                baslik_div = ilan.find('div', class_='s-item__title')
                link_a = ilan.find('a', class_='s-item__link')
                fiyat_span = ilan.find('span', class_='s-item__price')
                
                if not baslik_div or not link_a:
                    continue
                    
                baslik = baslik_div.text.strip()
                baslik = baslik.replace("Neu eingestelltes Angebot", "").strip()
                
                if "Shop on eBay" in baslik or not baslik:
                    continue
                    
                link = link_a['href'].split('?')[0]
                fiyat = fiyat_span.text.strip() if fiyat_span else "Fiyat Belirtilmemiş"
                
                toplam_ilan += 1
                sayac += 1
                
                prompt = f"""
                Aşağıdaki Ebay saat ilanını incele. 
                Saatin modelini, mekanizmasını (otomatik mi, quartz mı) ve durumunu analizar et.
                Bu saate piyasa değerine göre tahmini bir fiyat biç ve şu anki fiyatı kelepir mi, ederi mi yoksa pahalı mı belirt.
                Analizi tamamen Türkçe, kısa ve çok net maddeler halinde yap.

                İlan Başlığı: {baslik}
                İlan Fiyatı: {fiyat}
                """

                try:
                    model = genai.GenerativeModel('gemini-pro')
                    response = model.generate_content(prompt)
                    analiz = response.text
                except Exception as e:
                    analiz = f"Yapay zeka analizi yapılamadı: {e}"

                tum_mesajlar += f"### ⌚ İlan: {baslik}\n"
                tum_mesajlar += f"* **Fiyat:** {fiyat}\n"
                tum_mesajlar += f"* **Link:** {link}\n"
                tum_mesajlar += f"* **Yapay Zeka Analizi ve Fiyat Biçme:**\n{analiz}\n"
                tum_mesajlar += "\n" + "-"*40 + "\n\n"
                
        except Exception as e:
            print(f"Bağlantı hatası oluştu: {e}")

    print(f"Toplam {toplam_ilan} adet ilan analiz edildi.")
    if toplam_ilan > 0:
        mail_gonder(tum_mesajlar)
    else:
        print("Tüm filtrelerde aradığın kriterde ilan bulunamadı.")

def mail_gonder(icerik):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "📢 Detaylı Filtreli Ebay Saat Raporu"
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
