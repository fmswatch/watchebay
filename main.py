import os
import smtplib
import urllib.request
import urllib.parse
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')
EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

CAMP_ID = "5339157033"
ARAMALAR = ["panerai uhr", "zeno watch basel", "longines uhr"]

def ebay_resmi_api_veri_cek(kelime):
    if not EBAY_APP_ID:
        return [], "HATA: EBAY_APP_ID GitHub Secrets icinde bulunamadi veya adi farkli yazilmis!"

    url = "https://svcs.ebay.com/services/search/FindingService/v1"
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
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        req = urllib.request.Request(full_url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode('utf-8'))

        response_node = res_json.get("findItemsAdvancedResponse", [{}])[0]
        ack = response_node.get("ack", [""])[0]
        
        if ack != "Success":
            error_msg = response_node.get("errorMessage", [{}])[0].get("error", [{}])[0].get("message", ["Bilinmeyen eBay hatasi"])[0]
            return [], f"eBay API Reddetti (Ack: {ack}): {error_msg}"

        items = response_node.get("searchResult", [{}])[0].get("item", [])
        
        ilanlar = []
        for item in items:
            title = item.get("title", [""])[0]
            price = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", "0")
            currency = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("@currencyId", "EUR")
            item_url = item.get("viewItemURL", [""])[0]
            ilanlar.append({"title": title, "price": f"{price} {currency}", "url": item_url})
            
        return ilanlar, None

    except urllib.error.HTTPError as e:
        hata_icerik = e.read().decode('utf-8', errors='ignore')
        return [], f"HTTP Hatasi ({e.code}): {hata_icerik}"
    except Exception as e:
        return [], f"Sistem Hatasi: {str(e)}"

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
        return f"Yapay zeka analizi alinamadi: {e}"

def rapor_olustur():
    rapor_satirlari = []
    rapor_satirlari.append("CANLI EBAY VE GEMINI AI SAAT EKSPERTIZ RAPORU")
    rapor_satirlari.append("=========================================\n")

    for kelime in ARAMALAR:
        marka_adi = kelime.upper()
        rapor_satirlari.append(f"--- {marka_adi} EN YENİ İLANLAR ---\n")
        
        ilanlar, hata = ebay_resmi_api_veri_cek(kelime)

        if ilanlar:
            for idx, ilan in enumerate(ilanlar, 1):
                analiz = gemini_gercek_ekspertiz(ilan['title'], ilan['price'])
                rapor_satirlari.append(f"Ilan {idx}: {ilan['title']}")
                rapor_satirlari.append(f"Fiyat: {ilan['price']}")
                rapor_satirlari.append(f"Ekspertiz Analizi:\n{analiz}")
                rapor_satirlari.append(f"Ilan Linki: {ilan['url']}\n")
        else:
            rapor_satirlari.append(f"HATA DETAYI: {hata}\n")

    tam_metin = "\n".join(rapor_satirlari)
    mail_gonder(tam_metin)

def mail_gonder(icerik):
    if not GMAIL_USER or not GMAIL_PASS:
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "Saat Ekspertiz Raporu - Tehis Testi"
    msg.attach(MIMEText(icerik, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        server.close()
    except Exception as e:
        print(f"Mail gonderme hatasi: {e}")

if __name__ == "__main__":
    rapor_olustur()
