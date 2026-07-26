import os
import smtplib
import urllib.request
import urllib.parse
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Secrets alanından alınan gizli bilgiler
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

CAMP_ID = "5339157033"

# Takip edilmesini istediğiniz özel markalar
ARAMALAR = ["panerai+uhr", "zeno+watch+basel", "longines+uhr"]

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
    except Exception as e:
        return []

def gemini_gercek_ekspertiz(baslik, fiyat):
    if not GEMINI_API_KEY:
        return "Gemini API Key bulunamadi."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}

    prompt = (
        f"Sen bir luks saat uzmanisiniz. eBay Almanya uzerinde satilan su saati analiz et:\n"
        f"Saat Adi: {baslik}\n"
        f"Listelenen Fiyat: {fiyat}\n\n"
        f"Lutfen Türkçe olarak su 3 soruya cok kisa cevap ver:\n"
        f"1. Tahmini piyasa degeri nedir?\n"
        f"2. Bu fiyat kelepir mi, normal mi, pahali mi?\n"
        f"3. Alirken neye dikkat edilmeli?\n"
        f"Hicbir emoji veya ozel sembol kullanma. Sadece net kelimelerle yaz."
    )

    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            analiz = res_json['candidates'][0]['content']['parts'][0]['text']
            return analiz.strip()
    except Exception as e:
        return "Yapay zeka analizi su an yapilamadi."

def rapor_olustur():
    rapor_satirlari = []
    rapor_satirlari.append("CANLI EBAY VE GEMINI AI SAAT EKSPERTIZ RAPORU")
    rapor_satirlari.append("=========================================\n")

    for kelime in ARAMALAR:
        marka_adi = kelime.replace('+', ' ').upper()
        rapor_satirlari.append(f"--- {marka_adi} EN YENİ İLANLAR ---\n")
        
        resmi_link = f"https://www.ebay.de/sch/i.html?_nkw={kelime}&_sop=10&mkcid=1&mkrid=707-53477-19255-0&siteid=77&campid={CAMP_ID}&customid=bot-rapor"
        
        ilanlar = ebay_canli_veri_cek(kelime)

        if ilanlar:
            for idx, (baslik, fiyat) in enumerate(ilanlar, 1):
                analiz = gemini_gercek_ekspertiz(baslik, fiyat)
                rapor_satirlari.append(f"Ilan {idx}: {baslik}")
                rapor_satirlari.append(f"Fiyat: {fiyat}")
                rapor_satirlari.append(f"Ekspertiz Analizi:\n{analiz}")
                rapor_satirlari.append(f"Arama Linki: {resmi_link}\n")
        else:
            rapor_satirlari.append("Canli ilan çekilemedi, dogrudan arama linkinden bakabilirsiniz:")
            rapor_satirlari.append(f"Link: {resmi_link}\n")

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
