import os
import smtplib
import urllib.request
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')
EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

ARAMALAR = ["tissot uhr herren", "cartier uhr", "hamilton uhr"]

def ebay_resmi_api_veri_cek(kelime):
    if not EBAY_APP_ID:
        print("HATA: EBAY_APP_ID eklenmedi veya henüz onaylanmadı.")
        return []

    url = f"https://svcs.ebay.com/services/search/FindingService/v1"
    headers = {
        "X-EBAY-SOA-OPERATION-NAME": "findItemsAdvanced",
        "X-EBAY-SOA-SERVICE-VERSION": "1.0.0",
        "X-EBAY-SOA-REQUEST-DATA-FORMAT": "JSON",
        "X-EBAY-SOA-SECURITY-APPNAME": EBAY_APP_ID,
        "X-EBAY-SOA-GLOBAL-ID": "EBAY-DE"
    }

    params = {
        "keywords": kelime,
        "sortOrder": "StartTimeNewest",
        "paginationInput.entriesPerPage": "2"
    }

    try:
        data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode('utf-8'))

        items = res_json.get("findItemsAdvancedResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
        
        ilanlar = []
        for item in items:
            title = item.get("title", [""])[0]
            price = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", "0")
            currency = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("@currencyId", "EUR")
            item_url = item.get("viewItemURL", [""])[0]
            ilanlar.append({"title": title, "price": f"{price} {currency}", "url": item_url})
            
        return ilanlar
    except Exception as e:
        print(f"eBay API Hatası: {e}")
        return []

def gemini_gercek_ekspertiz(baslik, fiyat):
    if not GEMINI_API_KEY:
        return "Gemini API Key bulunamadi, yapay zeka analizi atlandi."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}

    prompt = (
        f"Sen profesyonel bir lüks saat ekspertizisin. eBay üzerinde listelenen şu ilanı analiz et:\n"
        f"Saat Başlığı: {baslik}\n"
        f"Listelenen Fiyat: {fiyat}\n\n"
        f"Lütfen Türkçe olarak şu 3 soruyu kısa ve net yanıtla:\n"
        f"1. Tahmini ikinci el piyasa değeri nedir?\n"
        f"2. Bu fiyat kelepir mi, normal mi yoksa pahalı mı?\n"
        f"3. Alıcı için dikkat edilmesi gereken risk/püf nokta var mı?\n"
        f"Özel semboller veya emoji kullanma. Sadece net metin yaz."
    )

    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            analiz = res_json['candidates'][0]['content']['parts'][0]['text']
            return analiz.strip()
    except Exception as e:
        print(f"Gemini API Hatası: {e}")
        return "Yapay zeka analizi anlik olarak alinamadi."

def rapor_olustur():
    rapor_satirlari = []
    rapor_satirlari.append("CANLI EBAY VE GEMINI AI SAAT EKSPERTİZ RAPORU")
    rapor_satirlari.append("=========================================\n")

    for kelime in ARAMALAR:
        rapor_satirlari.append(f"--- {kelime.upper()} EN YENİ İLANLAR ---\n")
        ilanlar = ebay_resmi_api_veri_cek(kelime)

        if ilanlar:
            for idx, ilan in enumerate(ilanlar, 1):
                analiz = gemini_gercek_ekspertiz(ilan['title'], ilan['price'])
                rapor_satirlari.append(f"İlan {idx}: {ilan['title']}")
                rapor_satirlari.append(f"Fiyat: {ilan['price']}")
                rapor_satirlari.append(f"Ekspertiz Analizi:\n{analiz}")
                rapor_satirlari.append(f"İlan Linki: {ilan['url']}\n")
        else:
            rapor_satirlari.append("eBay resmi API üzerinden canlı veri çekilemedi (eBay hesabı onay aşamasında olabilir).\n")

    tam_metin = "\n".join(rapor_satirlari)
    mail_gonder(tam_metin)

def mail_gonder(icerik):
    if not GMAIL_USER or not GMAIL_PASS:
        print("HATA: Gmail bilgileri eksik.")
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "Gerçek Canlı Ebay & Gemini AI Saat Raporu"
    msg.attach(MIMEText(icerik, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.close()
        print("Mail başarıyla gönderildi.")
    except Exception as e:
        print(f"Mail gönderme hatası: {e}")

if __name__ == "__main__":
    rapor_olustur()
