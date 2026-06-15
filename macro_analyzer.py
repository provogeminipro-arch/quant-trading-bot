import requests
import google.generativeai as genai
import config

def get_macro_sentiment():
    """
    Scarica le ultime news da Finnhub e usa Gemini AI per valutarle.
    Ritorna (True, "Motivo") se il mercato è buono per operare.
    Ritorna (False, "Motivo") se c'è un crollo imminente o panico geopolitico.
    """
    if not config.FINNHUB_API_KEY or not config.GEMINI_API_KEY:
        print("API Keys mancanti. Salto analisi macro.")
        return True, "API Key non configurate"

    # 1. Scarica le notizie generali del mercato americano tramite Finnhub
    try:
        # 'general' category gives general market news
        url = f"https://finnhub.io/api/v1/news?category=general&token={config.FINNHUB_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        news_data = response.json()
        
        # Prendi solo i titoli e i riassunti delle prime 15 notizie più rilevanti
        top_news = news_data[:15]
        news_text = ""
        for item in top_news:
            news_text += f"- Titolo: {item.get('headline', '')}\n  Riassunto: {item.get('summary', '')}\n\n"
            
    except Exception as e:
        print(f"Errore durante il fetch delle notizie Finnhub: {e}")
        return True, "Impossibile scaricare le notizie"

    # 2. Usa Gemini AI per analizzare il sentiment
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
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
        
        response = model.generate_content(prompt)
        ai_text = response.text.strip()
        # Pulisci eventuali formattazioni markdown restituite dall'AI
        if ai_text.startswith("```json"):
            ai_text = ai_text[7:]
        if ai_text.endswith("```"):
            ai_text = ai_text[:-3]
        ai_text = ai_text.strip()
        
        import json
        decision_data = json.loads(ai_text)
        
        news_summary = decision_data.get("news_summary", "")
        
        if decision_data.get("decision") == "BLOCK":
            return False, decision_data.get("reason", "Condizioni macro avverse"), news_summary
        else:
            return True, decision_data.get("reason", "Condizioni macro stabili"), news_summary
            
    except Exception as e:
        print(f"Errore Gemini AI: {e}")
        return True, "Impossibile analizzare il sentiment tramite AI", "Nessuna notizia disponibile."

if __name__ == "__main__":
    is_safe, reason, summary = get_macro_sentiment()
    print(f"Safe to trade? {is_safe}\nReason: {reason}\nSummary:\n{summary}")
