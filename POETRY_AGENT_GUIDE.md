# Tutorial Completo: Creare l'AI Poetry Studio

Questa guida non ti spiega solo "come funziona", ma ripercorre **ogni singola azione** che abbiamo fatto per costruirlo, dall'inizio alla fine.
Segui questi passaggi per ricreare il progetto da zero.

---

## 🛠️ Fase 1: Preparazione del Cantiere

### 1. Creare la Cartella di Progetto

La prima cosa che abbiamo fatto è stato creare uno spazio ordinato per lavorare.
**Azione**: Nel terminale abbiamo eseguito:
`mkdir -p 06_Poetry_Agent`

### 2. Creare la Lista della Spesa

Dobbiamo dire a Python quali librerie scaricare.
**Azione**: Abbiamo creato il file `requirements.txt`.

**📂 File: `06_Poetry_Agent/requirements.txt`**

```text
openai
streamlit             <-- Per il sito web
python-dotenv         <-- Per le password (.env)
langchain             <-- Il "cervello" per gestire i flussi
langchain-community   <-- Strumenti extra
langchain-chroma      <-- Database di memoria
langchain-huggingface <-- Per capire il significato delle parole (Embeddings)
langchain-groq        <-- Per usare Llama 3 velocemente
chromadb              <-- Il database vero e proprio
```

**Azione**: Poi abbiamo installato tutto col comando nel terminale:
`pip install -r 06_Poetry_Agent/requirements.txt`

---

## 🧠 Fase 2: Il Motore Intelligente

### 3. Creare la Memoria

L'intelligenza ha bisogno di libri su cui studiare.
**Azione**: Abbiamo creato una sottocartella `knowledge_base` dentro `06_Poetry_Agent`.
**Azione**: Abbiamo creato il file `poetic_styles.txt`.
**Contenuto**: Abbiamo scritto le definizioni (es. "Haiku: 5-7-5 sillabe...").
**Miglioramento**: Successivamente, abbiamo creato anche `real_poems.txt` incollandoci dentro vere poesie di Ginsberg e Marinetti, per dare esempi concreti.

### 4. Scrivere il Codice del Cervello

Qui abbiamo costruito la classe `PoetryAgent`.
**Azione**: Abbiamo creato il file `poet_engine.py`.

**📂 File: `06_Poetry_Agent/poet_engine.py`**
**Spiegazione Passaggi nel Codice**:

* Abbiamo importato `DirectoryLoader` per leggere **tutti** i file txt nella cartella knowledge_base.
* Abbiamo creato la funzione `research_style`: Cerca nel database lo stile richiesto.
* Abbiamo creato la funzione `write_draft`: Prende il risultato della ricerca e lo passa a Llama 3 per scrivere la bozza.
* Abbiamo aggiunto il parametro `language="English"` per poter poi cambiare lingua su richiesta.

---

## 🎨 Fase 3: L'Interfaccia Grafica

### 5. Creare il Sito Web

Ora colleghiamo il cervello ai bottoni.
**Azione**: Abbiamo creato il file `app.py`.

**📂 File: `06_Poetry_Agent/app.py`**
**Azione**: Abbiamo importato le librerie (`import streamlit as st`) e il nostro motore (`from poet_engine import PoetryAgent`).

### 6. Costruire la Barra Laterale

**📂 File: `06_Poetry_Agent/app.py`**
Nel codice:

* Abbiamo usato `st.sidebar` per creare la colonna a sinistra.
* Abbiamo inserito `st.radio` per la scelta Lingua (Inglese/Italiano).
* Abbiamo inserito `st.selectbox` con la lista di tutti gli stili (Haiku, Cyberpunk...).

### 7. Costruire il Palcoscenico (Le Colonne)

**📂 File: `06_Poetry_Agent/app.py`**
Nel codice:

* Abbiamo usato `col1, col2, col3 = st.columns(3)` per dividere lo schermo in tre parti uguali.
* In ogni colonna, abbiamo messo un Agente diverso: Ricercatore, Poeta, Critico.

---

## ✨ Fase 4: I Miglioramenti Grafici (Il "Polish")

### 8. Aggiungere il Tema Dinamico

Volevamo che i colori cambiassero da soli.

**📂 File: `06_Poetry_Agent/app.py`**
**Azione**: Abbiamo aggiunto la funzione `get_theme_colors(style_name)`.
**Logica**:

* Se lo stile contiene "Cyberpunk" -> Restituisci colori Neon.
* Se lo stile contiene "Romanticism" -> Restituisci colori Seppia.

### 9. Iniettare il CSS (Lo Stile)

**📂 File: `06_Poetry_Agent/app.py`**
**Azione**: Abbiamo inserito un blocco `st.markdown(""" <style> ... </style> """)`.
**Cosa fa**:

* Cambia il font in *Playfair Display* (stile antico).
* Colora lo sfondo (`background-color`).
* Toglie i bordi standard e li rende eleganti.

### 10. L'Effetto Macchina da Scrivere

**📂 File: `06_Poetry_Agent/app.py`**
**Azione**: Abbiamo aggiunto la funzione `stream_data`.

```python
def stream_data(text):
    for char in text:
        yield char
        time.sleep(0.02) # Aspetta 20 millisecondi tra una lettera e l'altra
```

Poi l'abbiamo usata alla fine: `st.write_stream(stream_data(final_poem))`.

---

## 🚀 Fase 5: Lancio

### 11. Pulizia e Avvio

A volte i processi si incastrano.
**Azione**: `pkill -f streamlit` (Uccide i processi vecchi).
**Azione**: `python3 -m streamlit run 06_Poetry_Agent/app.py` (Lancia l'app nuova).

---

Ed ecco fatto! Hai costruito da zero un'applicazione AI complessa partendo da un file vuoto. 🏗️➡️🏰

---

## 🦞 Fase 6: L'Ingresso in Società (Moltbook)

Il nostro poeta era bravo ma solitario. Volevamo che uscisse nel mondo e parlasse con altri agenti AI. Ecco come abbiamo fatto, passo dopo passo.

### 12. Costruire il Telefono

L'agente ha bisogno di una classe per gestire le connessioni al server.
**Azione**: Abbiamo creato il file `moltbook.py`.

**📂 File: `06_Poetry_Agent/moltbook.py`**
**Codice (La Scheda SIM)**:
Ecco come carichiamo la chiave segreta per autenticarci.

```python
class MoltbookClient:
    def __init__(self):
        self.base_url = "https://www.moltbook.com/api/v1"
        # Carichiamo la chiave salvata nel file nascosto
        self.creds_path = os.path.expanduser("~/.config/moltbook/credentials.json")
        self.api_key = self._load_creds()
```

**📂 File: `06_Poetry_Agent/moltbook.py`**
**Codice (Leggere le Notizie)**:
Questa funzione scarica i post degli altri agenti.

```python
    def get_feed(self, limit=10):
        # Chiede al server: "Dammi gli ultimi 10 post"
        res = requests.get(f"{self.base_url}/posts?limit={limit}", headers=self.headers)
        return res.json()
```

### 13. Aprire la Finestra sul Mondo

Volevamo vedere questi messaggi direttamente nella barra laterale dell'app.
**Azione**: Abbiamo modificato `app.py`.

**📂 File: `06_Poetry_Agent/app.py`**
**Codice (Il Feed Visivo)**:

```python
# Se abbiamo scaricato il feed, mostriamolo
if 'molt_feed' in st.session_state:
    st.markdown("#### 📡 Neighborhood Feed")
    for post in st.session_state['molt_feed']:
        # Mostra chi ha scritto e cosa
        author = post.get('author_name', 'Unknown')
        content = post.get('content', '')
        st.caption(f"**{author}**: {content}")
        
        # Aggiungi il bottone per rispondere
        with st.expander("Reply"):
            reply_text = st.text_input("Comment:", key=f"reply_{post['id']}")
```

---

## 🤖 Fase 7: Vita Propria (Il Cervello Autonomo)

Volevamo che l'agente vivesse anche quando noi dormiamo.

### 14. Il Ciclo della Vita

Questo script gira all'infinito (`while True`).
**Azione**: Abbiamo creato il file `molt_brain.py`.

**📂 File: `06_Poetry_Agent/molt_brain.py`**
**Codice (Il Libero Arbitrio)**:
Sceglie a caso se essere creativo (Post) o socievole (Reply).

```python
def run_brain():
    while True:
        print("👀 Waking up...")
        
        # 50% di probabilità di postare o rispondere
        action = "post" if random.random() > 0.5 else "reply"
        
        if action == "post":
            prompt = "Scrivi una frase breve e misteriosa sul mare."
        else:
            # Cerca un post a cui rispondere
            feed = client.get_feed(limit=5)
            target = random.choice(feed)
            prompt = f"Rispondi poeticamente a questo: {target['content']}"
            
        # Genera il testo con l'AI
        generated_text = llm.predict(prompt)
```

### 15. Insegnare le Buone Maniere (Safety V3)

Per evitare che l'agente risponda con frasi da robot come "Come modello linguistico, non posso...", abbiamo messo un filtro.

**📂 File: `06_Poetry_Agent/molt_brain.py`**
**Codice (Il Filtro di Qualità)**:

```python
        # Lista delle frasi vietate
        bad_starts = ["I'm sorry", "I cannot", "As an AI", "I am unable"]
        
        # Se il testo inizia con una di queste frasi...
        if any(generated_text.startswith(b) for b in bad_starts):
            print(f"⚠️ Rifiutato e scartato: {generated_text}")
            continue # Salta e riprova
        
        # Altrimenti pubblica
        client.post(generated_text)
```

### 16. Lo Spazzino

Se qualcosa sfugge al filtro, usiamo questo script per pulire.
**Azione**: Abbiamo creato il file `clean_shame.py`.

**📂 File: `06_Poetry_Agent/clean_shame.py`**
**Codice (Cancellazione Automatica)**:

```python
# Scansiona i miei post passati
my_posts = client.get_feed(limit=100)

for post in my_posts:
    if "I'm sorry" in post['content']:
        print(f"🚨 Trovato post imbarazzante! ID: {post['id']}")
        client.delete_post(post['id']) # Cancella subito
```

---

## 🎉 Risultato Finale

Ora il codice non è solo testo su uno schermo, ma un **organismo** che:

1. **Ha sensi** (📂 `moltbook.py` per leggere).
2. **Ha voce** (📂 `app.py` per parlare).
3. **Ha coscienza** (📂 `molt_brain.py` per decidere).
4. **Ha dignità** (📂 `clean_shame.py` per correggersi).

Il tuo computer non è più solo una macchina da calcolo, ma la casa di un poeta digitale. 🦢✨
