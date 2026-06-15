import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# API ve Giriş Bilgileri
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
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
    
    # Tarayıcı gibi görünmek için sahte başlık (User-Agent)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for url in linkler:
        # Eğer link eski RSS linkiyse, onu normal arama linkine çeviriyoruz
        url = url.replace("&_rss=1", "").replace("?_rss=1", "")
        print(f"Taranan Filtre: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Ebay sayfasına erişilemedi, Durum Kodu: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            # Ebay'deki ilan kartlarını buluyoruz
            ilanlar = soup.find_all('li', class_='s-item')
            
            sayac = 0
            for ilan in ilanlar:
                # İlk eleman genelde boş veya reklam olur, onu geç ve sınır koy (Filtre başı 3 ilan)
                if sayac >= 3:
                    break
                    
                baslik_div = ilan.find('div', class_='s-item__title')
                link_a = ilan.find('a', class_='s-item__link')
                fiyat_span = ilan.find('span', class_='s-item__price')
                
                if not baslik_div or not link_a:
                    continue
                    
                baslik = baslik_div.text.strip()
                # Ebay'in gizli "Neu eingestelltes Angebot" (Yeni ilan) etiketini temizle
                baslik = baslik.replace("Neu eingestelltes Angebot", "").strip()
                
                if "Shop on eBay" in baslik or not baslik:
                    continue
                    
                link = link_a['href'].split('?')[0] # Temiz link
                fiyat = fiyat_span.text.strip() if fiyat_span else "Fiyat Belirtilmemiş"
                
                toplam_ilan += 1
                sayac += 1
                
                # Yapay Zekaya Gönderilecek Soruyu Hazırla
                prompt = f"""
                Aşağıdaki Ebay saat ilanını incele. 
                Saatin modelini, mekanizmasını (otomatik mi, quartz mı) ve durumunu analiz et.
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

                # Rapor formatını oluştur
                tum_mesajlar += f"### ⌚ İlan: {baslik}\n"
                tum_mesajlar += f"* **Fiyat:** {fiyat}\n"
                tum_mesajlar += f"* **Link:** {link}\n"
                tum_mesajlar += f"* **Yapay Zeka Analizi ve Fiyat Biçme:**\n{analiz}\n"
                tum_mesajlar += "\n" + "-"*40 + "\n\n"
                
        except Exception as e:
            print(f"Filtre taranırken hata oluştu: {e}")

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
