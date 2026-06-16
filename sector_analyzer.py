import yfinance as yf
import pandas as pd

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
    Ritorna una lista dei nomi dei settori forti.
    """
    strong_sectors = []
    
    print("\nAnalisi Rotazione Settoriale (Relative Strength)...")
    
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.DateOffset(years=2) # 2 anni per garantire la SMA 200
    
    for sector_name, etf_ticker in SECTOR_ETFS.items():
        try:
            df = yf.download(etf_ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty or len(df) < 200:
                print(f"  - {sector_name} ({etf_ticker}): Dati insufficienti")
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
                
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            df = df.dropna()
            
            # Controllo dell'ultimo giorno disponibile
            current_price = df['Close'].iloc[-1]
            sma_200 = df['SMA_200'].iloc[-1]
            
            if current_price > sma_200:
                print(f"  [+] {sector_name} ({etf_ticker}): FORTE (Prezzo {current_price:.2f} > SMA200 {sma_200:.2f})")
                strong_sectors.append(sector_name)
            else:
                print(f"  [-] {sector_name} ({etf_ticker}): DEBOLE (Prezzo {current_price:.2f} < SMA200 {sma_200:.2f})")
                
        except Exception as e:
            print(f"  - {sector_name}: Errore durante l'analisi ({e})")
            
    return strong_sectors

if __name__ == "__main__":
    strong = get_strong_sectors()
    print(f"\nSettori Forti totali: {len(strong)} / {len(SECTOR_ETFS)}")
