import time
import yfinance as yf
import pandas as pd
import requests

# Mappatura dei settori GICS con i rispettivi ETF americani principali
SECTOR_ETFS = {
    "Information Technology": "XLK",
    "Health Care": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Communication Services": "XLC",
    "Industrials": "XLI",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB"
}

def get_strong_sectors():
    """
    Scarica i dati degli ETF settoriali e determina quali sono in trend rialzista.
    Un settore è considerato FORTE se il suo prezzo attuale è sopra la media mobile a 200 periodi (SMA 200).
    Ritorna una lista dei nomi dei settori forti. Se ci sono errori di connessione, ritorna None.
    """
    strong_sectors = []
    
    print("\nAnalisi Rotazione Settoriale (Relative Strength)...")
    
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.DateOffset(years=2) # 2 anni per garantire la SMA 200
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    valid_downloads = 0
    
    for sector_name, etf_ticker in SECTOR_ETFS.items():
        try:
            # Pausa per evitare di essere bloccati da Yahoo Finance
            time.sleep(1.0)
            
            # Scarichiamo i dati con yfinance usando la sessione personalizzata
            df = yf.download(etf_ticker, start=start_date, end=end_date, session=session, progress=False)
            
            if df is None or len(df) < 200:
                print(f"  - {sector_name} ({etf_ticker}): Dati insufficienti (len={len(df) if df is not None else 'None'})")
                continue
                
            valid_downloads += 1
                
            # Estrazione sicura della colonna Close per evitare problemi con MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                try:
                    close_series = df['Close', etf_ticker]
                except KeyError:
                    close_series = df['Close'].iloc[:, 0]
            else:
                close_series = df['Close']
                
            # Rimuoviamo eventuali NaN per essere sicuri
            close_series = close_series.dropna()
            
            if len(close_series) < 200:
                continue
                
            # Calcoliamo SMA 200
            sma_200 = close_series.rolling(window=200).mean()
            
            # Prendiamo gli ultimi valori validi (rimuovendo i NaN creati dalla SMA)
            valid_idx = sma_200.dropna().index
            if len(valid_idx) == 0:
                continue
                
            last_date = valid_idx[-1]
            current_price = close_series.loc[last_date]
            current_sma = sma_200.loc[last_date]
            
            # Se il prezzo attuale è un Series o DataFrame a causa di stranezze, prendiamo il primo elemento
            if isinstance(current_price, pd.Series): current_price = current_price.iloc[0]
            if isinstance(current_sma, pd.Series): current_sma = current_sma.iloc[0]
            
            if float(current_price) > float(current_sma):
                print(f"  [+] {sector_name} ({etf_ticker}): FORTE (Prezzo {current_price:.2f} > SMA200 {current_sma:.2f})")
                strong_sectors.append(sector_name)
            else:
                print(f"  [-] {sector_name} ({etf_ticker}): DEBOLE (Prezzo {current_price:.2f} < SMA200 {current_sma:.2f})")
                
        except Exception as e:
            print(f"  - {sector_name}: Errore durante l'analisi ({e})")
            
    if valid_downloads == 0:
        return None
        
    return strong_sectors

if __name__ == "__main__":
    strong = get_strong_sectors()
    if strong is None:
        print("\nErrore: Nessun dato valido scaricato.")
    else:
        print(f"\nSettori Forti totali: {len(strong)} / {len(SECTOR_ETFS)}")
