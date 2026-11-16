import time
import requests
import yfinance as yf
from datetime import datetime

# --- TELEGRAM AYARLARI ---
TOKEN = "9209685687:AAEx7AzR93SHqRpBLPt7AcbVg16ngXu-Spc"
CHAT_ID = "9052221255"

def telegrama_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram hata: {e}")

SYMBOL = "GC=F"
STOP_LOSS_PCT = 0.50
TAKE_PROFIT_PCT = 0.50

print("XAU/USD 5 Dakikalık Canlı Sinyal Botu Başlatıldı...")

# Bot başlar başlamaz GECİKMEDEN anında Telegram'a bildirimi çakalım:
telegrama_mesaj_gonder("🚀 *XAU/USD 5m Sinyal Botu* devrede ve aktif!")

aktif_pozisyon = None
giris_fiyati = 0.0
son_saat_bildirimi = datetime.now().hour

while True:
    try:
        simdiki_zaman = datetime.now()
        su_anki_saat = simdiki_zaman.hour

        # Her saat başı durum raporu
        if su_anki_saat != son_saat_bildirimi:
            telegrama_mesaj_gonder(f"ℹ️ *Bot Durum Raporu:* Sistem aktif, 5m veriler taranıyor. Saat: {simdiki_zaman.strftime('%H:%00')}")
            son_saat_bildirimi = su_anki_saat

        # Piyasalar kapalıyken geçmiş verilerle test için period="3d"
        data = yf.download(SYMBOL, period="3d", interval="5m", progress=False)
        
        if not data.empty and len(data) >= 3:
            if hasattr(data.columns, 'levels'):
                data.columns = data.columns.get_level_values(0)

            fiyatlar = data['Close'].dropna().tolist()
            guncel_fiyat = float(fiyatlar[-1])
            
            p_eski = float(fiyatlar[-3])
            p_orta = float(fiyatlar[-2])
            p_yeni = float(fiyatlar[-1])
            
            print(f"[{simdiki_zaman.strftime('%H:%M')}] Güncel Fiyat: {guncel_fiyat:.2f} | Pozisyon: {aktif_pozisyon}")

            # Sinyal Kontrolü
            if aktif_pozisyon is None:
                if p_orta < p_eski and p_yeni > p_orta:
                    aktif_pozisyon = "LONG"
                    giris_fiyati = guncel_fiyat
                    sl = giris_fiyati * (1 - (STOP_LOSS_PCT / 100))
                    tp = giris_fiyati * (1 + (TAKE_PROFIT_PCT / 100))
                    
                    mesaj = f"🟢 *XAU/USD 5m 20x LONG SİNYALİ!*\n\nGiriş: `{giris_fiyati:.2f}`\nSL: `{sl:.2f}`\nTP: `{tp:.2f}`"
                    telegrama_mesaj_gonder(mesaj)
                    
                elif p_orta > p_eski and p_yeni < p_orta:
                    aktif_pozisyon = "SHORT"
                    giris_fiyati = guncel_fiyat
                    sl = giris_fiyati * (1 + (STOP_LOSS_PCT / 100))
                    tp = giris_fiyati * (1 - (TAKE_PROFIT_PCT / 100))
                    
                    mesaj = f"🔴 *XAU/USD 5m 20x SHORT SİNYALİ!*\n\nGiriş: `{giris_fiyati:.2f}`\nSL: `{sl:.2f}`\nTP: `{tp:.2f}`"
                    telegrama_mesaj_gonder(mesaj)

            # Pozisyon Kapanış Kontrolü
            elif aktif_pozisyon is not None:
                fark = ((guncel_fiyat - giris_fiyati) / giris_fiyati) * 100
                if aktif_pozisyon == "LONG" and (fark <= -STOP_LOSS_PCT or fark >= TAKE_PROFIT_PCT):
                    telegrama_mesaj_gonder(f"🔔 *LONG Pozisyon Kapanış Sinyali!* Fiyat: `{guncel_fiyat:.2f}`")
                    aktif_pozisyon = None
                elif aktif_pozisyon == "SHORT":
                    fark_s = ((giris_fiyati - guncel_fiyat) / giris_fiyati) * 100
                    if fark_s <= -STOP_LOSS_PCT or fark_s >= TAKE_PROFIT_PCT:
                        telegrama_mesaj_gonder(f"🔔 *SHORT Pozisyon Kapanış Sinyali!* Fiyat: `{guncel_fiyat:.2f}`")
                        aktif_pozisyon = None

        time.sleep(300)
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        time.sleep(60)