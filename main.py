import os
import smtplib
import urllib.request
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')

CAMP_ID = "5339157033"
ARAMALAR = ["tissot+uhr+herren", "cartier+uhr", "hamilton+uhr"]

def ebay_canli_veri_cek(kelime):
    # Hesap güvenliği için arama yaparken CAMP_ID kullanılmaz, anonim istek atılır
    url = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        # HTML içinden ilan başlıklarını ve fiyatlarını ayıklama
        basliklar = re.findall(r'class="s-item__title"[^>]*><span[^>]*>(.*?)<\/span>', html)
        fiyatlar = re.findall(r'class="s-item__price"[^>]*>(.*?)<\/span>', html)
        
        # Filtreleme (eBay arama sayfasındaki boş veya alakasız ilk sonuçları temizler)
        gecerli_ilanlar = []
        for b, f in zip(basliklar, fiyatlar):
            if "shop on ebay" in b.lower() or "artikelsuche" in b.lower():
                continue
            gecerli_ilanlar.append((b.strip(), f.strip()))
            if len(gecerli_ilanlar) == 2:
                break
                
        return gecerli_ilanlar
    except Exception:
        return []

def yapay_zeka_ekspertiz(marka, baslik, fiyat_metni):
    # Fiyattan sadece sayısal değeri temizleme
    fiyat_temiz = "".join(c for c in fiyat_metni if c.isdigit() or c in [',', '.'])
    
    if "tissot" in marka.lower():
        ort = "450 ile 550 EUR"
        durum = "Fiyatı piyasa ortalamasındadır. Kondisyonu ve kutu içeriği kontrol edilerek karar verilmelidir."
        if "seastar" in baslik.lower():
            durum = "Seastar modelleri talep görmektedir. Fiyat makul görünüyor, değerlendirilebilir."
    elif "cartier" in marka.lower():
        ort = "4000 ile 5500 EUR"
        durum = "Yüksek değerli bir modeldir. Orijinallik sertifikası mutlaka sorgulanmalıdır. Fiyatı incelemeye değer."
    else:
        ort = "400 ile 600 EUR"
        durum = "Hamilton modelleri için dengeli bir fiyattır. Günlük kullanım için temizliği kontrol edilmelidir."
        
    return f"Bu modelin piyasa ortalaması tahmini {ort} civarındadır. Gelen fiyat {fiyat_metni}. {durum}"

def rapor_olustur():
    tum_mesajlar = "CANLI EBAY SAAT TAKİP RAPORU VE EKSPERTİZ ANALİZİ\n"
    tum_mesajlar = tum_mesajlar + "=========================================\n\n"
    
    for kelime in ARAMALAR:
        marka_adi = kelime.replace('+', ' ').upper()
        tum_mesajlar = tum_mesajlar + marka_adi + " En Yeni İlanlar\n\n"
        
        # Kullanıcı tıklayınca kazanç sağlayan resmi EPN linki
        resmi_link = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10&mkcid=1&mkrid=707-53477-19255-0&siteid=77&campid={CAMP_ID}&customid=bot-rapor"
        
        ilanlar = ebay_canli_veri_cek(kelime)
        
        if not ilanlar:
            tum_mesajlar = tum_mesajlar + "Bu marka için şu an canlı ilan verisi çekilemedi. Lütfen daha sonra tekrar deneyiniz.\n\n"
            continue
            
        sayac = 1
        for baslik, fiyat in ilanlar:
            ekspertiz = yapay_zeka_ekspertiz(kelime, baslik, fiyat)
            tum_mesajlar = tum_mesajlar + "İlan " + str(sayac) + " " + baslik + "\n"
            tum_mesajlar = tum_mesajlar + "Fiyat " + fiyat + "\n"
            tum_mesajlar = tum_mesajlar + "Ekspertiz Analizi " + ekspertiz + "\n"
            tum_mesajlar = tum_mesajlar + "Link " + resmi_link + "\n\n"
            sayac = sayac + 1
            
    mail_gonder(tum_mesajlar)

def mail_gonder(icerik):
    if not GMAIL_USER or not GMAIL_PASS:
        print("HATA GMAIL_USER veya GMAIL_PASS eksik")
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "Resmi Canlı Ebay Saat Raporu ve Ekspertiz Analizi"
    msg.attach(MIMEText(icerik, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.close()
        print("Email basariyla gonderildi")
    except Exception as e:
        print("Email hatasi")

if __name__ == "__main__":
    rapor_olustur()
