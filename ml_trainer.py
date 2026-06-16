import yfinance as yf
import pandas as pd
import numpy as np
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

def calculate_indicators(df):
    """Calcola gli indicatori tecnici necessari per l'AI."""
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands (20)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
    df['BB_Width'] = (df['SMA_20'] + (df['STD_20'] * 2) - df['BB_Lower']) / df['SMA_20']
    
    # Trend e Volumi
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['SMA_Volume'] = df['Volume'].rolling(window=20).mean()
    
    # Distanza percentuale dai supporti chiave
    df['Dist_SMA200'] = (df['Close'] - df['SMA_200']) / df['SMA_200']
    df['Dist_BBLower'] = (df['Close'] - df['BB_Lower']) / df['BB_Lower']
    
    return df

def generate_training_data():
    """Scarica 5 anni di dati per 20 titoli diversi e genera campioni di trading."""
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JNJ", "V", "WMT", "JPM",
               "PG", "NVDA", "HD", "CVX", "LLY", "MA", "ABBV", "PFE", "MRK", "PEP"]
    
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.DateOffset(years=5)
    
    all_features = []
    all_labels = []
    
    print("Scaricando dati per addestrare l'Intelligenza Artificiale (Machine Learning)...")
    
    for ticker in tickers:
        print(f"Estrazione dati storici: {ticker}")
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty: continue
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df = df.dropna()
        df = calculate_indicators(df)
        df = df.dropna()
        
        # Simuliamo una logica di acquisto più "allentata" per avere molti dati
        # Entriamo se il prezzo è sotto la SMA 20 (fase di debolezza)
        buy_signals = df[df['Close'] < df['SMA_20']].copy()
        
        for idx, row in buy_signals.iterrows():
            try:
                # Estraiamo i giorni successivi
                future_prices = df.loc[idx:].iloc[1:11] # Prossimi 10 giorni
                if future_prices.empty: continue
                
                max_future_high = future_prices['High'].max()
                min_future_low = future_prices['Low'].min()
                
                # Regola del backtest: Target +5%, Stop Loss -3%
                target_price = row['Close'] * 1.05
                stop_loss = row['Close'] * 0.97
                
                # Se tocca il target prima dello stop, è una Vittoria (1), altrimenti Sconfitta (0)
                win = 0
                for _, f_row in future_prices.iterrows():
                    if f_row['Low'] <= stop_loss:
                        win = 0
                        break
                    if f_row['High'] >= target_price:
                        win = 1
                        break
                
                # Salviamo le "Features" (le caratteristiche matematiche di quel giorno)
                features = {
                    'RSI': row['RSI'],
                    'BB_Width': row['BB_Width'],
                    'Dist_SMA200': row['Dist_SMA200'],
                    'Dist_BBLower': row['Dist_BBLower'],
                    'Volume_Ratio': row['Volume'] / (row['SMA_Volume'] + 1)
                }
                
                all_features.append(features)
                all_labels.append(win)
                
            except Exception:
                pass
                
    return pd.DataFrame(all_features), np.array(all_labels)

def train_model():
    print("\n--- INIZIO ADDESTRAMENTO MODELLO PREVISIONALE ---")
    X, y = generate_training_data()
    
    if len(X) < 100:
        print("Errore: Troppi pochi dati per l'addestramento.")
        return
        
    print(f"\nDati estratti con successo: {len(X)} simulazioni di trading.")
    
    # Dividiamo i dati in Training Set (80%) e Test Set (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Addestriamo l'algoritmo Random Forest (500 alberi decisionali)
    print("Addestrando Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Testiamo l'accuratezza
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"\n✅ Accuratezza del modello predittivo: {acc*100:.2f}%")
    print("\nReport di Classificazione:")
    print(classification_report(y_test, predictions))
    
    # Salviamo il modello addestrato su file per essere usato dal main.py
    joblib.dump(model, 'ml_model.joblib')
    print("Modello salvato con successo: 'ml_model.joblib'")

if __name__ == "__main__":
    train_model()
