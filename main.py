import time
import os
import csv
from datetime import datetime, timedelta
import pytz

import config
from data_fetcher import get_sp500_tickers, get_historical_data
from strategy_tester import test_strategy
from telegram_notifier import send_alert

def main():
    print("Avvio trading bot...")
    
    # 1. Scarica i ticker (prendiamo ad esempio i primi TOP_STOCKS_COUNT)
    tickers = get_sp500_tickers()
    if not tickers:
        print("Impossibile recuperare i ticker.")
        return
        
    tickers = tickers[:config.TOP_STOCKS_COUNT]
    print(f"Inizio analisi su {len(tickers)} tickers più capitalizzati del S&P 500...")
    
    now_it = datetime.now(pytz.timezone('Europe/Rome'))
    
    for ticker in tickers:
        print(f"\nAnalizzo {ticker}...")
        
        # 2. Scarica dati e valida
        df = get_historical_data(ticker, years=config.YEARS_HISTORY)
        if df is None:
            time.sleep(config.PAUSE_BETWEEN_STOCKS)
            continue
            
        # 3. Testa strategia e calcola win rate
        result = test_strategy(df)
        if result:
            win_rate, past_cases, buy_price, target_price = result
            print(f"[{ticker}] Segnale acceso! Win Rate Storico: {win_rate:.1f}% ({past_cases} casi)")
            
            # 4. Verifica filtro win rate
            if win_rate >= config.MIN_WIN_RATE:
                # Calcola il timeout (5 giorni di borsa aperta, calcoliamo 7 solari per semplicità sui weekend)
                timeout_date = now_it + timedelta(days=7)
                timeout_str = timeout_date.replace(hour=21, minute=55).strftime('%d/%m/%Y alle %H:%M')
                
                # 5. Invia alert Telegram
                send_alert(ticker, win_rate, past_cases, buy_price, target_price, timeout_str)
                
                # 6. Salva su CSV locale
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
                print(f"[{ticker}] Scartato: Win Rate {win_rate:.1f}% è inferiore al minimo richiesto ({config.MIN_WIN_RATE}%).")
        else:
            print(f"[{ticker}] Nessun setup rilevato oggi.")
            
        # Pausa anti-ban per Yahoo Finance
        time.sleep(config.PAUSE_BETWEEN_STOCKS)
        
    print("\nAnalisi completata!")

if __name__ == "__main__":
    main()
