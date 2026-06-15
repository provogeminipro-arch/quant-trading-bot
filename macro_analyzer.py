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
        # Scegliamo il modello pro
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Agisci come un Risk Manager per un fondo di investimento azionario quantitativo (NASDAQ e S&P 500).
        Il mio algoritmo sta per inviare dei segnali di acquisto "long" (rialzisti) che dureranno 5 giorni.
        
        Di seguito trovi le notizie finanziarie e geopolitiche di oggi:
        {news_text}
        
        Valuta il rischio macro-economico globale. C'è il rischio imminente di un crollo (crash) di mercato a causa di:
        - Guerre o gravi escalation geopolitiche fresche di giornata
        - Crisi bancarie improvvise
        - Annunci disastrosi su tassi di interesse o inflazione
        
        Rispondi ESATTAMENTE e SOLO con una di queste due stringhe JSON:
        {{"decision": "PROCEED", "reason": "breve motivazione..."}}
        oppure
        {{"decision": "BLOCK", "reason": "breve motivazione sul panico in corso..."}}
        """
        
        response = model.generate_content(prompt)
        ai_text = response.text.strip().strip('`').replace('json', '').strip()
        
        import json
        decision_data = json.loads(ai_text)
        
        if decision_data.get("decision") == "BLOCK":
            return False, decision_data.get("reason", "Condizioni macro avverse")
        else:
            return True, decision_data.get("reason", "Condizioni macro stabili")
            
    except Exception as e:
        print(f"Errore Gemini AI: {e}")
        return True, "Impossibile analizzare il sentiment tramite AI"

if __name__ == "__main__":
    # Test locale
    is_safe, reason = get_macro_sentiment()
    print(f"Safe to trade? {is_safe}\nReason: {reason}")
