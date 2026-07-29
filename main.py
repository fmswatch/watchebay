import os
import smtplib
import urllib.request
import urllib.parse
import json
import base64
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASS = os.environ.get('GMAIL_PASS')
EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
EBAY_CERT_ID = os.environ.get('EBAY_CERT_ID')

# Ana ve Yedek API Anahtarlarını alıyoruz
GEMINI_KEYS = [
    k.strip() for k in [os.environ.get('GEMINI_API_KEY'), os.environ.get('GEMINI_API_KEY_2')] if k
]

ARAMALAR = ["panerai"]

def ebay_oauth_token_al():
    if not EBAY_APP_ID or not EBAY_CERT_ID:
        return None, "HATA: EBAY_APP_ID veya EBAY_CERT_ID eksik!"

    auth_header = base64.b64encode(f"{EBAY_APP_ID.strip()}:{EBAY_CERT_ID.strip()}".encode('utf-8')).decode('utf-8')
    
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_header}"
    }
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            return res_json.get("access_token"), None
    except Exception as e:
        return None, f"OAuth Baglanti Hatasi: {str(e)}"

def ebay_browse_api_veri_cek(kelime, token):
    params = {
        "q": kelime,
        "category_ids": "31387",
        "filter": "price:[2000..],priceCurrency:EUR",
        "limit": "3",
        "sort": "newlyListed"
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"https://api.ebay.com/buy/browse/v1/item_summary/search?{query_string}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_DE",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode('utf-8'))

        items = res_json.get("itemSummaries", [])
        if not items:
            return [], "2000 EUR uzerinde Panerai ilani bulunamadi."

        ilanlar = []
        for item in items:
            title = item.get("title", "Ilan Basligi Yok")
            price_dict = item.get("price", {})
            price_val = price_dict.get("value", "0")
            curr = price_dict.get("currency", "EUR")
            item_url = item.get("itemWebUrl", "#")
            
            try:
                if float(price_val) < 2000:
                    continue
            except ValueError:
                pass

            ilanlar.append({"title": title, "price": f"{price_val} {curr}", "url": item_url})

        return ilanlar, None

    except Exception as e:
        return None, f"Browse API Hatasi: {str(e)}"

def gemini_gercek_ekspertiz(baslik, fiyat):
    if not GEMINI_KEYS:
        return "HATA: Hicbir GEMINI_API_KEY bulunamadi!"

    prompt = (
        f"Sen bir luks saat uzmanisiniz. eBay Almanya uzerinde yeni listelenen su ilani analiz et:\n"
        f"Saat Adi: {baslik}\n"
        f"Fiyat: {fiyat}\n\n"
        f"Lutfen Türkçe olarak su 3 soruyu kısa ve net yanıtla:\n"
        f"1. Tahmini piyasa degeri nedir?\n"
        f"2. Bu fiyat kelepir mi, normal mi, pahali mi?\n"
        f"3. Alırken neye dikkat edilmeli?\n"
        f"Sadece net metin yaz, emoji kullanma."
    )

    data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}

    # Mevcut tum API key'leri sirayla dener
    for api_key in GEMINI_KEYS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                analiz = res_json['candidates'][0]['content']['parts'][0]['text']
                return analiz.strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Kota dolduysa bir sonraki anahtara geç
                continue
            else:
                return f"Gemini HTTP Hatasi ({e.code})"
        except Exception as e:
            return f"Gemini Baglanti Hatasi: {str(e)}"

    return "HATA (HTTP 429): Tum Gemini API Key'lerinin gunluk kotasi doldu! Lutfen yeni bir API Key ekleyin."

def rapor_olustur():
    token, token_hata = ebay_oauth_token_al()
    
    rapor_satirlari = []
    rapor_satirlari.append("CANLI EBAY VE GEMINI AI SAAT EKSPERTIZ RAPORU (MIN 2000 EUR)")
    rapor_satirlari.append("=========================================================\n")

    if not token:
        rapor_satirlari.append(f"KRITIK HATA: eBay OAuth Jetonu Alinamadi!\nDetay: {token_hata}")
        mail_gonder("\n".join(rapor_satirlari))
        return

    for kelime in ARAMALAR:
        marka_adi = kelime.upper()
        rapor_satirlari.append(f"--- {marka_adi} (2000 EUR+) EN YENİ İLANLAR ---\n")

        ilanlar, hata = ebay_browse_api_veri_cek(kelime, token)

        if ilanlar:
            for idx, ilan in enumerate(ilanlar, 1):
                analiz = gemini_gercek_ekspertiz(ilan['title'], ilan['price'])
                rapor_satirlari.append(f"Ilan {idx}: {ilan['title']}")
                rapor_satirlari.append(f"Fiyat: {ilan['price']}")
                rapor_satirlari.append(f"Ekspertiz Analizi:\n{analiz}")
                rapor_satirlari.append(f"Ilan Linki: {ilan['url']}\n")
                time.sleep(2)
        else:
            rapor_satirlari.append(f"DURUM / HATA: {hata}\n")

    tam_metin = "\n".join(rapor_satirlari)
    mail_gonder(tam_metin)

def mail_gonder(icerik):
    if not GMAIL_USER or not GMAIL_PASS:
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = "Canli Panerai Saat Ekspertiz Raporu (2000 EUR+)"
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
