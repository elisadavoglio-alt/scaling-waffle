# � Tutorial Completo: Creare l'AI Poetry Studio

Questa guida non ti spiega solo "come funziona", ma ripercorre **ogni singola azione** che abbiamo fatto per costruirlo, dall'inizio alla fine.
Segui questi passaggi per ricreare il progetto da zero.

---

## 🛠️ Fase 1: Preparazione del Cantiere

### 1. Creare la Cartella di Progetto

La prima cosa che abbiamo fatto è stato creare uno spazio ordinato per lavorare.
**Azione**: Nel terminale abbiamo eseguito:
`mkdir -p 06_Poetry_Agent`

### 2. Creare la Lista della Spesa (`requirements.txt`)

Dobbiamo dire a Python quali librerie scaricare.
**Azione**: Abbiamo creato il file `06_Poetry_Agent/requirements.txt`.
**Contenuto Incollato**:

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

**Azione**: Poi abbiamo installato tutto col comando:
`pip install -r 06_Poetry_Agent/requirements.txt`

---

## 🧠 Fase 2: Il Motore Intelligente

### 3. Creare la Memoria (`knowledge_base`)

L'intelligenza ha bisogno di libri su cui studiare.
**Azione**: Abbiamo creato una sottocartella `knowledge_base` dentro `06_Poetry_Agent`.
**Azione**: Abbiamo creato il file `poetic_styles.txt`.
**Contenuto**: Abbiamo scritto le definizioni (es. "Haiku: 5-7-5 sillabe...").
**Miglioramento**: Successivamente, abbiamo creato anche `real_poems.txt` incollandoci dentro vere poesie di Ginsberg e Marinetti, per dare esempi concreti.

### 4. Scrivere il Codice del Cervello (`poet_engine.py`)

Qui abbiamo costruito la classe `PoetryAgent`.
**Azione**: Abbiamo creato il file `06_Poetry_Agent/poet_engine.py`.
**Spiegazione Passaggi nel Codice**:

* Abbiamo importato `DirectoryLoader` per leggere **tutti** i file txt nella cartella knowledge_base.
* Abbiamo creato la funzione `research_style`: Cerca nel database lo stile richiesto.
* Abbiamo creato la funzione `write_draft`: Prende il risultato della ricerca e lo passa a Llama 3 per scrivere la bozza.
* Abbiamo aggiunto il parametro `language="English"` per poter poi cambiare lingua su richiesta.

---

## 🎨 Fase 3: L'Interfaccia Grafica

### 5. Creare il Sito Web (`app.py`)

Ora colleghiamo il cervello ai bottoni.
**Azione**: Abbiamo creato il file `06_Poetry_Agent/app.py`.
**Azione**: Abbiamo importato le librerie (`import streamlit as st`) e il nostro motore (`from poet_engine import PoetryAgent`).

### 6. Costruire la Barra Laterale

Nel codice di `app.py`:

* Abbiamo usato `st.sidebar` per creare la colonna a sinistra.
* Abbiamo inserito `st.radio` per la scelta Lingua (Inglese/Italiano).
* Abbiamo inserito `st.selectbox` con la lista di tutti gli stili (Haiku, Cyberpunk...).

### 7. Costruire il Palcoscenico (Le Colonne)

* Abbiamo usato `col1, col2, col3 = st.columns(3)` per dividere lo schermo in tre parti uguali.
* In ogni colonna, abbiamo messo un Agente diverso: Ricercatore, Poeta, Critico.

---

## ✨ Fase 4: I Miglioramenti Grafici (Il "Polish")

### 8. Aggiungere il Tema Dinamico

Volevamo che i colori cambiassero da soli.
**Azione**: In `app.py` abbiamo aggiunto la funzione `get_theme_colors(style_name)`.
**Logica**:

* Se lo stile contiene "Cyberpunk" -> Restituisci colori Neon.
* Se lo stile contiene "Romanticism" -> Restituisci colori Seppia.

### 9. Iniettare il CSS (Lo Stile)

**Azione**: Abbiamo inserito un blocco `st.markdown(""" <style> ... </style> """)`.
**Cosa fa**:

* Cambia il font in *Playfair Display* (stile antico).
* Colora lo sfondo (`background-color`).
* Toglie i bordi standard e li rende eleganti.

### 10. L'Effetto Macchina da Scrivere

**Azione**: Abbiamo aggiunto la funzione `stream_data`.
**Codice**:

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
