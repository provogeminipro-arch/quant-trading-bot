import pandas as pd
import numpy as np

def test_strategy(df):
    """
    Ritorna una tupla (win_rate, past_cases, buy_price, target_price, features) 
    se c'è un segnale OGGI, altrimenti None.
    """
    df = df.copy()
    
    # Calcolo indicatori con pandas nativo (senza pandas_ta)
    # 1. RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 2. ATR 14
    high = df['High']
    low = df['Low']
    close_prev = df['Close'].shift(1)
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # 3. SMA 200 (Prezzo)
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    # 4. SMA Volume 20 (Filtro Volumi)
    df['SMA_Volume'] = df['Volume'].rolling(window=20).mean()
    
    # 5. Bollinger Bands (20, 2)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    std_20 = df['Close'].rolling(window=20).std()
    df['BB_Lower'] = df['SMA_20'] - (2 * std_20)
    df['BB_Upper'] = df['SMA_20'] + (2 * std_20)
    
    # FIX BUG 6: BB_Width coerente con ml_trainer.py = (BB_Upper - BB_Lower) / SMA_20
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['SMA_20']
    
    df = df.dropna()
    
    if len(df) < 50:
        return None
        
    # Condizioni del trigger
    df['Prev_RSI'] = df['RSI'].shift(1)
    df['Prev_Low'] = df['Low'].shift(1)
    
    # Eliminiamo la prima riga che ha NaN dopo lo shift (FIX RISK 3)
    df = df.iloc[1:]
    
    # 1. Prezzo sopra SMA 200 (Trend rialzista primario)
    # 2. Ieri RSI < 30 (Ipervenduto)
    # 3. Oggi RSI > Ieri RSI (in risalita)
    # 4. Oggi Low >= Ieri Low (tiene i minimi)
    # 5. Volume > SMA Volume (Interesse istituzionale)
    # 6. Candela Verde: Close > Open (Conferma compratori)
    # 7. Elastico: Prezzo sotto o che tocca la banda inferiore di Bollinger
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
    
    if len(trigger_dates) == 0:
        return None
        
    wins = 0
    total_trades = 0
    
    # Simulazione storica
    # Ignoriamo l'ultima riga perché potrebbe essere il segnale di oggi che non ha ancora risultato
    historical_triggers = trigger_dates[:-1] if df.iloc[-1]['Trigger'] else trigger_dates
    
    for date in historical_triggers:
        idx = df.index.get_loc(date)
        if idx + 5 >= len(df):
            continue
            
        buy_price = df.iloc[idx]['Close']
        target_price = buy_price + (2.0 * df.iloc[idx]['ATR']) # Target raddoppiato (V4)
        stop_loss = buy_price - (1.0 * df.iloc[idx]['ATR'])
        
        total_trades += 1
        trade_won = False
        
        # Controlliamo i successivi 5 giorni
        for i in range(1, 6):
            if df.iloc[idx + i]['Low'] <= stop_loss:
                break # Colpito stop loss, si esce in perdita
            if df.iloc[idx + i]['High'] >= target_price:
                trade_won = True
                break # Colpito target, vittoria
                
        if trade_won:
            wins += 1
            
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    
    # Verifichiamo se OGGI si è acceso il segnale
    if df.iloc[-1]['Trigger']:
        current_buy_price = df.iloc[-1]['Close']
        current_target_price = current_buy_price + (2.0 * df.iloc[-1]['ATR']) # Target raddoppiato (V4)
        
        # Estrai le features per il Machine Learning
        row = df.iloc[-1]
        dist_sma = (row['Close'] - row['SMA_200']) / row['SMA_200']
        dist_bb = (row['Close'] - row['BB_Lower']) / row['BB_Lower']
        vol_ratio = row['Volume'] / (row['SMA_Volume'] + 1)
        
        # FIX BUG 6: BB_Width ora è coerente con ml_trainer.py
        features = {
            'RSI': row['RSI'],
            'BB_Width': row['BB_Width'],
            'Dist_SMA200': dist_sma,
            'Dist_BBLower': dist_bb,
            'Volume_Ratio': vol_ratio
        }
        
        return win_rate, total_trades, current_buy_price, current_target_price, features
        
    return None
