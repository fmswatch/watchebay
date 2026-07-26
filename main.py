import os
import smtplib
import urllib.request
import json
import xml.etree.ElementTree as ET
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

CAMP_ID = "5339157033"
ARAMALAR = ["panerai+uhr", "zeno+watch+basel", "longines+uhr"]

def ebay_rss_veri_cek(kelime):
    # eBay RSS akışı IP engellerine takılmaz ve anlık ilanları sunar
    url = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10&_rss=1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        items = root.findall('.//item')
        
        gecerli_ilanlar = []
        for item in items[:2]: # Her marka için en yeni 2 ilan
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            description = item.find('description').text if item.find('description') is not None else ""
            
            # Açıklamadan veya başlıktan fiyatı çekme
            fiyat_match = re.search(r'EUR\s*[\d\.,]+|[\d\.,]+\s*EUR', description)
            fiyat = fiyat_match.group(0) if fiyat_match else "Fiyat belirtilmedi"
            
            if title:
                # Başlığı temizleme
                title_clean = re.sub(r'[^\w\s]', '', title)
                gecerli_ilanlar.append((title_clean, fiyat, link))
                
        return gecerli_ilanlar
    except Exception as e:
        print(f"RSS Hatasi: {e}")
        return []

def gemini_gercek_ekspertiz(baslik, fiyat):
    if not GEMINI_API_KEY:
        return "Gemini API Key bulunamadi."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}

    prompt = (
        f"Sen luks saat uzmanisiniz. eBay Almanya uzerinde yeni listelenen su ilani analiz et:\n"
        f"Saat Adi: {baslik}\n"
        f"Fiyat: {fiyat}\n\n"
        f"Lutfen Türkçe olarak su 3 soruyu kısa ve net yanıtla:\n"
        f"1. Tahmini piyasa degeri nedir?\n"
        f"2. Bu fiyat kelepir mi, normal mi, pahali mi?\n"
        f"3. Alirken neye dikkat edilmeli?\n"
        f"Hicbir emoji veya ozel sembol kullanma. Sadece net metin yaz."
    )

    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            analiz = res_json['candidates'][0]['content']['parts'][0]['text']
            return analiz.strip()
    except Exception as e:
        return "Yapay zeka analizi anlik alınamadı."

def rapor_olustur():
    rapor_satirlari = []
    rapor_satirlari.append("CANLI EBAY VE GEMINI AI SAAT EKSPERTIZ RAPORU")
    rapor_satirlari.append("=========================================\n")

    for kelime in ARAMALAR:
        marka_adi = kelime.replace('+', ' ').upper()
        rapor_satirlari.append(f"--- {marka_adi} EN YENİ İLANLAR ---\n")
        
        ilanlar = ebay_rss_veri_cek(kelime)

        if ilanlar:
            for idx, (baslik, fiyat, link) in enumerate(ilanlar, 1):
                analiz = gemini_gercek_ekspertiz(baslik, fiyat)
                rapor_satirlari.append(f"Ilan {idx}: {baslik}")
                rapor_satirlari.append(f"Fiyat: {fiyat}")
                rapor_satirlari.append(f"Ekspertiz Analizi:\n{analiz}")
                rapor_satirlari.append(f"Ilan Linki: {link}\n")
        else:
            resmi_link = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10&campid={CAMP_ID}"
            rapor_satirlari.append(f"Veri akisi saglanamadi. Arama linki: {resmi_link}\n")

    tam_metin = "\n".join(rapor_satirlari)
    mail_gonder(tam_metin)

def mail_gonder(icerik):
    if not GMAIL_USER or not GMAIL_PASS:
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "Canli Saat Ekspertiz Raporu (Panerai, Zeno, Longines)"
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
