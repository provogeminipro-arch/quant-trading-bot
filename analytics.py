import pandas as pd
import os
import csv
from datetime import datetime
import yfinance as yf

def yfinance_download_safe(ticker, start, end):
    """Download sicuro con gestione MultiIndex."""
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        return df
    except:
        return None

def aggiorna_portafoglio():
    """
    Legge il registro_segnali.csv, individua i trade "scaduti" (passati 5 giorni solari dal segnale),
    scarica i dati storici reali di quei giorni e controlla se il target è stato colpito.
    Salva il risultato in portafoglio_virtuale.csv.
    """
    registro_file = 'registro_segnali.csv'
    portafoglio_file = 'portafoglio_virtuale.csv'
    
    if not os.path.exists(registro_file):
        print("Nessun registro segnali trovato da analizzare.")
        return
        
    try:
        df_segnali = pd.read_csv(registro_file)
    except:
        return
        
    if df_segnali.empty:
        return
        
    # Carica i trade già analizzati per non ricalcolarli
    trade_conclusi = set()
    if os.path.exists(portafoglio_file):
        try:
            df_port = pd.read_csv(portafoglio_file)
            if not df_port.empty:
                # Usa Data+Ticker come ID unico per il trade
                for index, row in df_port.iterrows():
                    trade_conclusi.add(f"{row['Data']}_{row['Ticker']}")
        except:
            pass
            
    now = datetime.now()
    
    nuovi_risultati = []
    
    for index, row in df_segnali.iterrows():
        trade_id = f"{row['Data']}_{row['Ticker']}"
        if trade_id in trade_conclusi:
            continue
            
        try:
            # Es: 2026-06-01 15:45:00
            data_segnale = datetime.strptime(row['Data'], '%Y-%m-%d %H:%M:%S')
            giorni_passati = (now - data_segnale).days
            
            # Se sono passati almeno 5 giorni (consideriamo 7 solari per i weekend)
            if giorni_passati >= 7:
                print(f"Analizzo l'esito reale del trade su {row['Ticker']} del {row['Data']}...")
                
                # Scarichiamo i dati di quei 7 giorni
                ticker = row['Ticker']
                target = float(row['Target Price'])
                buy_price = float(row['Prezzo Acquisto'])
                
                # yfinance end date is non-inclusive, so we add 10 days to be sure we get the full week
                end_date = data_segnale + pd.Timedelta(days=10)
                df_storico = yfinance_download_safe(ticker, start=data_segnale.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
                
                if df_storico is None or df_storico.empty:
                    continue
                    
                # Vogliamo solo i 5 giorni di borsa successivi alla data del segnale
                df_storico = df_storico.iloc[1:6] # Il giorno 0 è il giorno del segnale, guardiamo i prossimi 5
                
                # FIX RISK 1: Controlliamo che lo slice non sia vuoto
                if df_storico.empty:
                    print(f"  Dati insufficienti per {ticker}, impossibile verificare l'esito.")
                    continue
                
                vinto = False
                for i in range(len(df_storico)):
                    high_price = float(df_storico.iloc[i]['High'])
                    if high_price >= target:
                        vinto = True
                        break
                
                esito = "VINTO" if vinto else "PERSO"
                if vinto:
                    prof_perc = (target - buy_price) / buy_price * 100
                else:
                    last_close = float(df_storico.iloc[-1]['Close'])
                    prof_perc = -((buy_price - last_close) / buy_price * 100)
                
                nuovi_risultati.append([
                    row['Data'],
                    row['Ticker'],
                    row['Win Rate'], # Previsto
                    esito,
                    f"{prof_perc:.2f}%"
                ])
                print(f"Esito {ticker}: {esito} ({prof_perc:.2f}%)")
        except Exception as e:
            print(f"Errore analisi trade vecchio {row['Ticker']}: {e}")
            
    # Salva i nuovi risultati
    if nuovi_risultati:
        file_exists = os.path.exists(portafoglio_file)
        with open(portafoglio_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Data', 'Ticker', 'Win Rate Previsto', 'Esito Reale', 'Profitto/Perdita %'])
            for res in nuovi_risultati:
                writer.writerow(res)
