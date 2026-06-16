import pandas as pd
import yfinance as yf
import time
import config

def get_sp500_tickers():
    """Scarica la lista aggiornata delle aziende S&P 500 da Wikipedia."""
    try:
        import requests
        from io import StringIO
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0'}
        html = requests.get(url, headers=headers, timeout=10).text
        table = pd.read_html(StringIO(html))
        df = table[0]
        tickers = df['Symbol'].tolist()
        # Fix tickers that have dots instead of dashes (e.g. BRK.B -> BRK-B)
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except Exception as e:
        print(f"Errore nel recupero dei ticker: {e}")
        return []

def get_sp500_with_sectors():
    """Scarica la lista delle aziende S&P 500 con il rispettivo GICS Sector."""
    try:
        import requests
        from io import StringIO
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0'}
        html = requests.get(url, headers=headers, timeout=10).text
        table = pd.read_html(StringIO(html))
        df = table[0]
        # Return a dictionary: {'AAPL': 'Information Technology', ...}
        sector_map = {}
        for _, row in df.iterrows():
            ticker = row['Symbol'].replace('.', '-')
            sector = row['GICS Sector']
            sector_map[ticker] = sector
        return sector_map
    except Exception as e:
        print(f"Errore nel recupero dei settori: {e}")
        return {}

def get_historical_data(ticker, years=10):
    """Scarica i dati storici validandone la completezza."""
    try:
        import requests
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years)
        
        # Download data with custom session to prevent blocks
        df = yf.download(ticker, start=start_date, end=end_date, session=session, progress=False)
        
        if df.empty:
            print(f"{ticker}: Dati vuoti.")
            return None
        
        # FIX BUG 5: Prima flatten le colonne MultiIndex, POI dropna
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # Data validation
        # Circa 252 giorni di borsa in un anno
        min_required_days = int(252 * (years * 0.9)) # Richiediamo almeno il 90% dei dati attesi
        if len(df) < min_required_days:
            print(f"{ticker}: Dati storici incompleti (solo {len(df)} giorni trovati). Scartato.")
            return None
            
        # Drop any row with NaN to ensure genuine data
        df = df.dropna()
            
        return df
    except Exception as e:
        print(f"Errore durante il download dei dati per {ticker}: {e}")
        return None
