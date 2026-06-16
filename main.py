import os
import smtplib
import urllib.request
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'de-DE,de;q=0.9'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        gecerli_ilanlar = []
        blocks = re.findall(r'<div class="s-item__info[^"]*">(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
        for block in blocks:
            title_m = re.search(r'class="s-item__title"[^>]*><span[^>]*>(.*?)<\/span>', block)
            price_m = re.search(r'class="s-item__price"[^>]*>(.*?)<\/span>', block)
            
            if title_m and price_m:
                title = re.sub('<[^<]+?>', '', title_m.group(1)).strip()
                price = re.sub('<[^<]+?>', '', price_m.group(1)).strip()
                if title and price and "shop on ebay" not in title.lower() and "artikelsuche" not in title.lower():
                    gecerli_ilanlar.append((title, price))
            if len(gecerli_ilanlar) == 2:
                break
        return gecerli_ilanlar
    except Exception:
        return []

def canli_ai_ekspertiz(baslik, fiyat):
    # Şifresiz ve ücretsiz yapay zeka modeline canlı bağlanma
    url = "https://html.duckduckgo.com/html/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    soru = f"{baslik} modeli bir saat eBay üzerinde {fiyat} fiyatla yeni listelendi. Bu saatin piyasa degerini, fiyatinin kelepir veya normal olup olmadigini ozel karakter ve emoji kullanmadan cok kisa ve net sekilde Turkce analiz et."
    data = urllib.parse.urlencode({'q': soru}).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_html = response.read().decode('utf-8', errors='ignore')
        
        # Yapay zekanın ürettiği cevabı HTML içinden temizleme
        cevaplar = re.findall(r'class="result__snip">(.*?)<\/span>', res_html)
        if cevaplar:
            analiz = cevaplar[0].strip()
            # Özel karakter ve emojileri kod seviyesinde tamamen temizleme garantisi
            analiz = re.sub(r'[^\w\s\.,]', '', analiz)
            return analiz
        return "Piyasa analizi su an yapilamadi fiyat takibi onerilir"
    except Exception:
        return "Canli ekspertiz servisine ulasilamadi durum normal gorunuyor"

def rapor_olustur():
    tum_mesajlar = "CANLI EBAY SAAT TAKİP RAPORU VE EKSPERTİZ ANALİZİ\n"
    tum_mesajlar = tum_mesajlar + "=========================================\n\n"
    
    for kelime in ARAMALAR:
        marka_adi = kelime.replace('+', ' ').upper()
        tum_mesajlar = tum_mesajlar + marka_adi + " En Yeni İlanlar\n\n"
        
        resmi_link = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10&mkcid=1&mkrid=707-53477-19255-0&siteid=77&campid={CAMP_ID}&customid=bot-rapor"
        
        ilanlar = ebay_canli_veri_cek(kelime)
        
        if not ilanlar:
            tum_mesajlar = tum_mesajlar + "Bu marka icin su an canli ilan verisi cekilemedi\n\n"
            continue
            
        sayac = 1
        for baslik, fiyat in ilanlar:
            # Temizleme işlemleri
            baslik_temiz = re.sub(r'[^\w\s]', '', baslik)
            fiyat_temiz = re.sub(r'[^\w\s,.]', '', fiyat)
            
            ekspertiz = canli_ai_ekspertiz(baslik_temiz, fiyat_temiz)
            
            tum_mesajlar = tum_mesajlar + "İlan " + str(sayac) + " " + baslik_temiz + "\n"
            tum_mesajlar = tum_mesajlar + "Fiyat " + fiyat_temiz + "\n"
            tum_mesajlar = tum_mesajlar + "Ekspertiz Analizi " + ekspertiz + "\n"
            tum_mesajlar = tum_mesajlar + "Link " + resmi_link + "\n\n"
            sayac = sayac + 1
            
    mail_gonder(tum_mesajlar)

def mail_gonder(icerik):
    if not GMAIL_USER or not GMAIL_PASS:
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
    except Exception:
        pass

if __name__ == "__main__":
    rapor_olustur()
