import requests
import json
import os
import config

SUBSCRIBERS_FILE = 'iscritti.json'

def update_subscribers():
    """Legge i nuovi messaggi dal bot e salva chi ha scritto /start"""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    
    # Carica iscritti esistenti
    subscribers = set()
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r') as f:
            try:
                subs_list = json.load(f)
                subscribers = set(subs_list)
            except:
                pass
                
    # Aggiungi sempre te stesso di default
    if config.TELEGRAM_CHAT_ID:
        subscribers.add(str(config.TELEGRAM_CHAT_ID))
        
    try:
        response = requests.get(url)
        if response.ok:
            data = response.json()
            for result in data.get('result', []):
                message = result.get('message', {})
                text = message.get('text', '')
                chat_id = str(message.get('chat', {}).get('id', ''))
                
                if text == '/start' and chat_id:
                    subscribers.add(chat_id)
                    
            # Salva il file aggiornato
            with open(SUBSCRIBERS_FILE, 'w') as f:
                json.dump(list(subscribers), f)
                
    except Exception as e:
        print(f"Errore aggiornamento iscritti Telegram: {e}")
        
    return list(subscribers)

def send_alert(ticker, win_rate, past_cases, buy_price, target_price, time_out_str):
    """Invia il segnale a tutti gli iscritti"""
    subscribers = update_subscribers()
    
    message = (
        f"🚨 <b>SEGNALE DI TRADING</b> 🚨\n\n"
        f"📈 <b>Titolo (Ticker):</b> {ticker}\n"
        f"📊 <b>Statistiche:</b> {win_rate:.1f}% di successo ({past_cases} casi passati negli ultimi 10 anni)\n\n"
        f"💵 <b>Prezzo d'Acquisto:</b> ~{buy_price:.2f} $\n"
        f"🎯 <b>Target Price:</b> {target_price:.2f} $\n"
        f"⏳ <b>Time Out:</b> {time_out_str}\n"
    )
    
    for chat_id in subscribers:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Errore invio a {chat_id}: {e}")
            
    print(f"Alert inviato a {len(subscribers)} utenti per {ticker}")
    
def send_general_message(text):
    """Invia un messaggio di testo libero a tutti (es. blocco per sentiment negativo)"""
    subscribers = update_subscribers()
    for chat_id in subscribers:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, json=payload)
        except:
            pass
