import pandas as pd
import numpy as np
from datetime import datetime
import os

from data_fetcher import get_sp500_tickers, get_historical_data

def run_global_backtest():
    print("Inizializzando Motore Backtest Globale...")
    print("Scaricando ticker S&P 500...")
    tickers = get_sp500_tickers()[:50] # Top 50 per test veloce (2 anni di dati ciascuno)
    
    global_wins = 0
    global_losses = 0
    global_timeouts = 0
    global_total = 0
    total_profit_pct = 0.0
    
    print(f"Esecuzione simulazione su {len(tickers)} titoli per gli ultimi 2 anni.")
    
    for idx, ticker in enumerate(tickers):
        print(f"[{idx+1}/{len(tickers)}] Backtest {ticker}...", end=" ", flush=True)
        df = get_historical_data(ticker, years=2)
        
        if df is None or len(df) < 200:
            print("Dati insufficienti.")
            continue
            
        # Calcolo indicatori nativi
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        high = df['High']
        low = df['Low']
        close_prev = df['Close'].shift(1)
        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()
        
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['SMA_Volume'] = df['Volume'].rolling(window=20).mean()
        
        sma_20 = df['Close'].rolling(window=20).mean()
        std_20 = df['Close'].rolling(window=20).std()
        df['BB_Lower'] = sma_20 - (2 * std_20)
        
        df = df.dropna()
        if len(df) < 50:
            print("Troppo corti dopo dropna.")
            continue
            
        df['Prev_RSI'] = df['RSI'].shift(1)
        df['Prev_Low'] = df['Low'].shift(1)
        
        df['Trigger'] = (
            (df['Close'] > df['SMA_200']) & 
            (df['Prev_RSI'] < 30) & 
            (df['RSI'] > df['Prev_RSI']) & 
            (df['Low'] >= df['Prev_Low']) & 
            (df['Volume'] > df['SMA_Volume']) &
            (df['Close'] > df['Open']) &
            (df['Low'] <= df['BB_Lower'])
        )
        
        trigger_dates = df[df['Trigger']].index
        
        ticker_trades = 0
        ticker_wins = 0
        
        for date in trigger_dates:
            trade_idx = df.index.get_loc(date)
            # Dobbiamo avere almeno 5 giorni di futuro per valutare il trade
            if trade_idx + 5 >= len(df):
                continue
                
            buy_price = df.iloc[trade_idx]['Close']
            current_atr = df.iloc[trade_idx]['ATR']
            target_price = buy_price + (2.0 * current_atr) # Target raddoppiato
            stop_loss = buy_price - (1.0 * current_atr)
            
            global_total += 1
            ticker_trades += 1
            
            trade_won = False
            trade_lost = False
            profit_pct = 0.0
            
            # Simulazione rigorosa dei successivi 5 giorni
            for i in range(1, 6):
                future_low = df.iloc[trade_idx + i]['Low']
                future_high = df.iloc[trade_idx + i]['High']
                
                # Check Stop Loss prima del Target (worst case scenario per anti-allucinazione)
                if future_low <= stop_loss:
                    trade_lost = True
                    profit_pct = ((stop_loss - buy_price) / buy_price) * 100
                    global_losses += 1
                    total_profit_pct += profit_pct
                    break
                    
                if future_high >= target_price:
                    trade_won = True
                    profit_pct = ((target_price - buy_price) / buy_price) * 100
                    global_wins += 1
                    ticker_wins += 1
                    total_profit_pct += profit_pct
                    break
                    
            if not trade_won and not trade_lost:
                global_timeouts += 1
                final_close = df.iloc[trade_idx + 5]['Close']
                profit_pct = ((final_close - buy_price) / buy_price) * 100
                total_profit_pct += profit_pct
                
        print(f"Completato. {ticker_trades} segnali trovati.")
        
    print("\n--- RISULTATI GLOBALI BACKTEST V3 PRO ---")
    print(f"Totale Segnali Verificati: {global_total}")
    if global_total > 0:
        print(f"Vittorie (Target Preso): {global_wins} ({(global_wins/global_total)*100:.1f}%)")
        print(f"Sconfitte (Stop Loss): {global_losses} ({(global_losses/global_total)*100:.1f}%)")
        print(f"Scaduti (5 Giorni): {global_timeouts} ({(global_timeouts/global_total)*100:.1f}%)")
        print(f"Profitto Netto Cumulativo Stimato: {total_profit_pct:.2f}%")
        print(f"Profitto Medio per Trade: {total_profit_pct/global_total:.2f}%")
    else:
        print("Il filtro è troppo severo: 0 trade trovati nel periodo.")
        
    with open('backtest_raw_results.txt', 'w') as f:
        f.write(f"Total:{global_total}\nWins:{global_wins}\nLosses:{global_losses}\nTimeouts:{global_timeouts}\nNetProfit:{total_profit_pct:.2f}")

if __name__ == "__main__":
    run_global_backtest()
