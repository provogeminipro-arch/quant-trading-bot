import requests
import json
import config
import pandas as pd
from google import genai

def _call_gemini(prompt):
    """Helper centralizzato per chiamare Gemini AI con il nuovo SDK google-genai."""
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    ai_text = response.text.strip()
    # Pulisci eventuali formattazioni markdown restituite dall'AI
    if ai_text.startswith("```json"):
        ai_text = ai_text[7:]
    if ai_text.endswith("```"):
        ai_text = ai_text[:-3]
    ai_text = ai_text.strip()
    return json.loads(ai_text)

def get_macro_sentiment():
    """
    Scarica le ultime news da Finnhub e usa Gemini AI per valutarle.
    Ritorna SEMPRE una tupla di 3 elementi: (bool, str, str)
    - (True/False, "Motivo", "News Summary")
    """
    if not config.FINNHUB_API_KEY or not config.GEMINI_API_KEY:
        print("API Keys mancanti. Salto analisi macro.")
        return True, "API Key non configurate", "Nessuna notizia disponibile."

    # 1. Scarica le notizie generali del mercato americano tramite Finnhub
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={config.FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        news_data = response.json()
        
        # Prendi solo i titoli e i riassunti delle prime 15 notizie più rilevanti
        top_news = news_data[:15]
        news_text = ""
        for item in top_news:
            news_text += f"- Titolo: {item.get('headline', '')}\n  Riassunto: {item.get('summary', '')}\n\n"
            
    except Exception as e:
        print(f"Errore durante il fetch delle notizie Finnhub: {e}")
        return True, "Impossibile scaricare le notizie", "Nessuna notizia disponibile."

    # 2. Usa Gemini AI per analizzare il sentiment
    try:
        prompt = f"""
        Agisci come un Risk Manager per un fondo di investimento azionario quantitativo (NASDAQ e S&P 500).
        Di seguito trovi le notizie finanziarie e geopolitiche di oggi:
        {news_text}
        
        Valuta il rischio macro-economico globale. C'è il rischio imminente di un crollo (crash) di mercato a causa di guerre, pandemie o crisi finanziarie?
        
        Devi rispondere ESATTAMENTE e SOLO con un oggetto JSON valido (senza backtick o formattazioni Markdown), avente questa precisa struttura:
        {{
            "decision": "PROCEED" oppure "BLOCK",
            "reason": "motivo della decisione in una frase",
            "news_summary": "Un riassunto SINTETICO in ITALIANO (max 3 punti elenco, usa le emoji) delle notizie più rilevanti di oggi."
        }}
        """
        
        decision_data = _call_gemini(prompt)
        
        news_summary = decision_data.get("news_summary", "")
        
        if decision_data.get("decision") == "BLOCK":
            return False, decision_data.get("reason", "Condizioni macro avverse"), news_summary
        else:
            return True, decision_data.get("reason", "Condizioni macro stabili"), news_summary
            
    except Exception as e:
        print(f"Errore Gemini AI: {e}")
        return True, "Impossibile analizzare il sentiment tramite AI", "Nessuna notizia disponibile."

def get_ticker_sentiment(ticker):
    """
    Scarica le ultime news per il singolo ticker e usa Gemini AI per valutarle.
    Ritorna (True, "Motivo") se le news sono normali/fisiologiche.
    Ritorna (False, "Motivo") se ci sono scandali, utili disastrosi o "Value Trap".
    """
    if not config.FINNHUB_API_KEY or not config.GEMINI_API_KEY:
        return True, "API Key mancanti. Salto analisi specifica."

    try:
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={(pd.Timestamp.now() - pd.DateOffset(days=3)).strftime('%Y-%m-%d')}&to={pd.Timestamp.now().strftime('%Y-%m-%d')}&token={config.FINNHUB_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        news_data = response.json()
        
        top_news = news_data[:5] # Le ultime 5 notizie
        if not top_news:
            return True, "Nessuna news rilevante recente."
            
        news_text = ""
        for item in top_news:
            news_text += f"- Titolo: {item.get('headline', '')}\n  Riassunto: {item.get('summary', '')}\n\n"
            
    except Exception as e:
        print(f"Errore Finnhub Ticker {ticker}: {e}")
        return True, "Impossibile scaricare le notizie del ticker."

    try:
        prompt = f"""
        Agisci come un analista fondamentale per un fondo quantitativo.
        L'algoritmo matematico ha appena rilevato un crollo di prezzo interessante per il titolo {ticker} e vorrebbe comprare (Mean-Reversion).
        
        Tuttavia, dobbiamo evitare le "Value Trap" (aziende fallimentari o in crollo per motivi gravi).
        Ecco le ultime notizie su {ticker}:
        {news_text}
        
        Valuta se il calo è ingiustificato (fisiologico) oppure se c'è un rischio enorme (es. truffe contabili, cause legali miliardarie, utili disastrosi, dimissioni del CEO).
        
        Devi rispondere ESATTAMENTE e SOLO con un oggetto JSON valido (senza backtick o formattazioni), avente questa struttura:
        {{
            "decision": "PROCEED" oppure "BLOCK",
            "reason": "motivo sintetico della decisione"
        }}
        """
        
        decision_data = _call_gemini(prompt)
        
        if decision_data.get("decision") == "BLOCK":
            return False, decision_data.get("reason", "Notizie aziendali negative")
        else:
            return True, decision_data.get("reason", "Notizie aziendali stabili")
            
    except Exception as e:
        print(f"Errore Gemini Ticker {ticker}: {e}")
        return True, "Impossibile analizzare il ticker tramite AI"

if __name__ == "__main__":
    is_safe, reason, summary = get_macro_sentiment()
    print(f"Safe to trade? {is_safe}\nReason: {reason}\nSummary:\n{summary}")
