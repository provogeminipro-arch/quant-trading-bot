import requests
import config

def send_alert(ticker, win_rate, past_cases, buy_price, target_price, time_out_str):
    message = (
        f"🚨 <b>SEGNALE DI TRADING</b> 🚨\n\n"
        f"📈 <b>Titolo (Ticker):</b> {ticker}\n"
        f"📊 <b>Statistiche:</b> {win_rate:.1f}% di successo ({past_cases} casi passati negli ultimi 10 anni)\n\n"
        f"💵 <b>Prezzo d'Acquisto:</b> ~{buy_price:.2f} $\n"
        f"🎯 <b>Target Price:</b> {target_price:.2f} $\n"
        f"⏳ <b>Time Out:</b> {time_out_str}\n"
    )
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Alert inviato con successo per {ticker}")
    except Exception as e:
        print(f"Errore durante l'invio dell'alert Telegram per {ticker}: {e}")
