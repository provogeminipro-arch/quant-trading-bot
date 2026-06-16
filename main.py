import time
import os
import csv
from datetime import datetime, timedelta
import pytz

import config
from data_fetcher import get_sp500_tickers, get_historical_data, get_sp500_with_sectors
from strategy_tester import test_strategy
from telegram_notifier import send_alert, send_general_message
from macro_analyzer import get_macro_sentiment, get_ticker_sentiment
from analytics import aggiorna_portafoglio
from sector_analyzer import get_strong_sectors


def main():
    print("Avvio trading bot (V2 Pro)...")
    now_it = datetime.now(pytz.timezone('Europe/Rome'))
    
    # 0. Aggiorna Portafoglio (controlla i trade passati)
    print("Aggiornamento Analytics e Portafoglio Virtuale...")
    aggiorna_portafoglio()
    
    # 1. Analisi Geopolitica e Macro tramite Gemini AI + Finnhub
    print("\nControllo Macro-Economico e Geopolitico in corso...")
    is_safe, reason, news_summary = get_macro_sentiment()
    print(f"Esito AI: {'SICURO' if is_safe else 'BLOCCO'} - Motivo: {reason}")
    
    if not is_safe:
        warning_msg = (
            f"⛔️ <b>TRADING BLOCCATO OGGI</b> ⛔️\n\n"
            f"L'Intelligenza Artificiale ha bloccato gli acquisti a causa di un grave rischio macroeconomico:\n"
            f"<i>{reason}</i>\n\n"
            f"🌍 <b>Flash News Sintetiche dal Mondo:</b>\n{news_summary}\n\n"
            f"Protezione del capitale attivata."
        )
        print("Operatività sospesa. Inviando notifica agli iscritti...")
        send_general_message(warning_msg)
        return # Ferma tutto lo script
        
    # Allarme API
    if reason == "Impossibile analizzare il sentiment tramite AI":
        send_general_message("⚠️ <b>ALLARME API:</b> Errore di comunicazione con Google Gemini. Possibile quota esaurita o chiave invalida. Le Flash News sono disattivate temporaneamente.")

    print("\nCondizioni di mercato stabili. Procedo con lo scan dei titoli...")

    # 1.5. Rotazione Settoriale
    strong_sectors = get_strong_sectors()
    if not strong_sectors:
        print("NESSUN settore in trend rialzista! Mercato in crollo generale.")
        send_general_message("⚠️ <b>MERCATO DEBOLE:</b> Nessun settore è in trend rialzista (Tutti gli ETF sotto SMA200). Blocco acquisti azionari preventivo.")
        return
        
    print(f"Settori Forti ammessi per l'acquisto: {', '.join(strong_sectors)}")

    # 2. Scarica i ticker con i relativi settori
    ticker_sectors = get_sp500_with_sectors()
    if not ticker_sectors:
        print("Impossibile recuperare i ticker.")
        return
        
    tickers = list(ticker_sectors.keys())[:config.TOP_STOCKS_COUNT]
    
    # 5. Caricamento modello ML (una sola volta)
    model = None
    model_path = 'ml_model.joblib'
    if os.path.exists(model_path):
        import joblib
        model = joblib.load(model_path)
        print("[AI] Modello ML caricato da disco.")
    else:
        print("[AI] Modello ML non trovato, verrà addestrato dinamicamente al primo segnale.")
    
    segnali_trovati = 0
    
    for ticker in tickers:
        sector = ticker_sectors.get(ticker, "Unknown")
        print(f"\nAnalizzo {ticker} [{sector}]...")
        
        if sector not in strong_sectors:
            print(f"Scartato: il settore {sector} è attualmente DEBOLE e in trend ribassista.")
            continue
        
        # 3. Scarica dati e valida
        df = get_historical_data(ticker, years=config.YEARS_HISTORY)
        if df is None:
            time.sleep(config.PAUSE_BETWEEN_STOCKS)
            continue
            
        # 4. Testa strategia e calcola win rate
        risultato = test_strategy(df)
        
        if risultato:
            win_rate, past_cases, buy_price, target_price, features = risultato
            print(f"!!! SEGNALE TROVATO SU {ticker} !!!")
            print(f"Storico: {win_rate:.1f}% Win Rate su {past_cases} casi simili.")
            
            # 5. Machine Learning Prediction (using preloaded model)
            try:
                if model is None:
                    # train on demand and load
                    from ml_trainer import train_model
                    train_model()
                    import joblib
                    model = joblib.load(model_path)
                
                X_new = [[features['RSI'], features['BB_Width'], features['Dist_SMA200'], features['Dist_BBLower'], features['Volume_Ratio']]]
                import pandas as pd
                X_df = pd.DataFrame(X_new, columns=['RSI', 'BB_Width', 'Dist_SMA200', 'Dist_BBLower', 'Volume_Ratio'])
                
                prob_win = model.predict_proba(X_df)[0][1] # Probabilità della classe 1 (Vittoria)
                print(f"[AI] Probabilità predittiva di successo (Machine Learning): {prob_win*100:.1f}%")
                
                if prob_win < 0.60:
                    print(f"Scartato dall'Intelligenza Artificiale (Probabilità < 60%).")
                    continue
            except Exception as e:
                print(f"Errore durante l'analisi ML: {e}")
                continue
                
            # 6. Verifica filtro win rate storico
            if win_rate >= config.MIN_WIN_RATE:
                
                # 7. Intelligenza Artificiale Specifica (Value Trap Check)
                print(f"[{ticker}] Win Rate OK ({win_rate:.1f}%). Consulto l'AI per Value Trap...")
                is_safe_ticker, reason_ticker = get_ticker_sentiment(ticker)
                
                if not is_safe_ticker:
                    print(f"[{ticker}] SEGNALE BLOCCATO DALL'AI: {reason_ticker}")
                    continue
                    
                print(f"[{ticker}] AI approva il trade. Invio segnale.")
                
                segnali_trovati += 1
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
        
    # Se non è stato trovato nessun segnale oggi, mandiamo il Daily Report di "Buonanotte"
    if segnali_trovati == 0:
        report_msg = (
            f"📊 <b>REPORT GIORNALIERO BOT</b>\n\n"
            f"Analisi su {len(tickers)} titoli completata.\n"
            f"Nessun segnale ad alta probabilità (>={config.MIN_WIN_RATE}%) rilevato per oggi.\n\n"
            f"🌍 <b>Flash News Macroeconomiche:</b>\n{news_summary}\n\n"
            f"Ci aggiorniamo a domani! 💤"
        )
        send_general_message(report_msg)
        
    print("\nAnalisi completata!")

if __name__ == "__main__":
    main()
