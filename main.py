import time
import os
import csv
from datetime import datetime, timedelta
import pytz

import config
from data_fetcher import get_sp500_tickers, get_historical_data
from strategy_tester import test_strategy
from telegram_notifier import send_alert, send_general_message
from macro_analyzer import get_macro_sentiment
from analytics import aggiorna_portafoglio

def main():
    print("Avvio trading bot (V2 Pro)...")
    now_it = datetime.now(pytz.timezone('Europe/Rome'))
    
    # 0. Aggiorna Portafoglio (controlla i trade passati)
    print("Aggiornamento Analytics e Portafoglio Virtuale...")
    aggiorna_portafoglio()
    
    # 1. Analisi Geopolitica e Macro tramite Gemini AI + Finnhub
    print("\nControllo Macro-Economico e Geopolitico in corso...")
    is_safe, reason = get_macro_sentiment()
    print(f"Esito AI: {'SICURO' if is_safe else 'BLOCCO'} - Motivo: {reason}")
    
    if not is_safe:
        warning_msg = f"⛔️ <b>TRADING BLOCCATO OGGI</b> ⛔️\n\nL'Intelligenza Artificiale ha bloccato gli acquisti a causa di un grave rischio macroeconomico:\n\n<i>{reason}</i>\n\nProtezione del capitale attivata."
        print("Operatività sospesa. Inviando notifica agli iscritti...")
        send_general_message(warning_msg)
        return # Ferma tutto lo script
        
    print("\nCondizioni di mercato stabili. Procedo con lo scan dei titoli...")

    # 2. Scarica i ticker
    tickers = get_sp500_tickers()
    if not tickers:
        print("Impossibile recuperare i ticker.")
        return
        
    tickers = tickers[:config.TOP_STOCKS_COUNT]
    
    for ticker in tickers:
        print(f"\nAnalizzo {ticker}...")
        
        # 3. Scarica dati e valida
        df = get_historical_data(ticker, years=config.YEARS_HISTORY)
        if df is None:
            time.sleep(config.PAUSE_BETWEEN_STOCKS)
            continue
            
        # 4. Testa strategia e calcola win rate
        result = test_strategy(df)
        if result:
            win_rate, past_cases, buy_price, target_price = result
            
            # 5. Verifica filtro win rate
            if win_rate >= config.MIN_WIN_RATE:
                timeout_date = now_it + timedelta(days=7)
                timeout_str = timeout_date.replace(hour=21, minute=55).strftime('%d/%m/%Y alle %H:%M')
                
                # Invia alert a TUTTI gli iscritti
                send_alert(ticker, win_rate, past_cases, buy_price, target_price, timeout_str)
                
                # Salva su CSV locale
                log_file = 'registro_segnali.csv'
                file_exists = os.path.isfile(log_file)
                with open(log_file, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(['Data', 'Ticker', 'Win Rate', 'Casi Passati', 'Prezzo Acquisto', 'Target Price', 'Time Out'])
                    writer.writerow([
                        now_it.strftime('%Y-%m-%d %H:%M:%S'), 
                        ticker, 
                        f"{win_rate:.1f}%", 
                        past_cases, 
                        round(buy_price, 2), 
                        round(target_price, 2), 
                        timeout_str
                    ])
            else:
                print(f"[{ticker}] Scartato: Win Rate {win_rate:.1f}% è inferiore al minimo richiesto.")
        
        time.sleep(config.PAUSE_BETWEEN_STOCKS)
        
    print("\nAnalisi completata!")

if __name__ == "__main__":
    main()
