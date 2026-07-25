import os
import smtplib
import urllib.request
import urllib.parse
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')

CAMP_ID = "5339157033"
ARAMALAR = ["tissot+uhr+herren", "cartier+uhr", "hamilton+uhr"]

def ebay_canli_veri_cek(kelime):
    url = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        gecerli_ilanlar = []
        titles = re.findall(r'class="s-item__title"[^>]*><span[^>]*>(.*?)<\/span>', html)
        prices = re.findall(r'class="s-item__price"[^>]*>(.*?)<\/span>', html)
        
        for t, p in zip(titles, prices):
            t_clean = re.sub(r'<[^>]+>', '', t).strip()
            p_clean = re.sub(r'<[^>]+>', '', p).strip()
            if t_clean and p_clean and "shop on ebay" not in t_clean.lower() and "artikelsuche" not in t_clean.lower():
                gecerli_ilanlar.append((t_clean, p_clean))
            if len(gecerli_ilanlar) == 2:
                break
        return gecerli_ilanlar
    except Exception:
        return []

def canli_ai_ekspertiz(baslik, fiyat):
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        query = f"{baslik} {fiyat} saat piyasa degeri kelepir mi"
        data = urllib.parse.urlencode({'q': query}).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            res_html = response.read().decode('utf-8', errors='ignore')
        
        cevaplar = re.findall(r'class="result__snip">(.*?)<\/span>', res_html)
        if cevaplar:
            temiz = re.sub(r'<[^>]+>', '', cevaplar[0]).strip()
            return temiz
    except Exception:
        pass
    return "Fiyat seviyesi inceleniyor, ilan detayina gitmek icin linke tiklayiniz."

def rapor_olustur():
    rapor_satirlari = []
    rapor_satirlari.append("CANLI EBAY SAAT TAKİP RAPORU VE EKSPERTİZ ANALİZİ")
    rapor_satirlari.append("=========================================\n")
    
    veri_bulundu = False
    
    for kelime in ARAMALAR:
        marka_adi = kelime.replace('+', ' ').upper()
        rapor_satirlari.append(f"{marka_adi} En Yeni İlanlar\n")
        
        resmi_link = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10&mkcid=1&mkrid=707-53477-19255-0&siteid=77&campid={CAMP_ID}&customid=bot-rapor"
        
        ilanlar = ebay_canli_veri_cek(kelime)
        
        if ilanlar:
            veri_bulundu = True
            sayac = 1
            for baslik, fiyat in ilanlar:
                ekspertiz = canli_ai_ekspertiz(baslik, fiyat)
                rapor_satirlari.append(f"İlan {sayac} {baslik}")
                rapor_satirlari.append(f"Fiyat {fiyat}")
                rapor_satirlari.append(f"Ekspertiz Analizi {ekspertiz}")
                rapor_satirlari.append(f"Link {resmi_link}\n")
                sayac += 1
        else:
            rapor_satirlari.append("Canli ilan verisi cekilemedi, arama linki aşağıdadır.")
            rapor_satirlari.append(f"Link {resmi_link}\n")
            
    tam_metin = "\n".join(rapor_satirlari)
    mail_gonder(tam_metin)

def mail_gonder(icerik):
    if not GMAIL_USER or not GMAIL_PASS:
        print("HATA GMAIL bilgileri eksik")
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "Resmi Canlı Ebay Saat Raporu"
    msg.attach(MIMEText(icerik, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.close()
        print("Mail basariyla gonderildi")
    except Exception as e:
        print("Mail hatasi")

if __name__ == "__main__":
    rapor_olustur()
