# 🤖 Tutorial: Il Tuo Primo Agente (Passo dopo Passo)

Segui questi passaggi nell'ordine esatto. Non saltarne nessuno.

---

## ⬛ Parte 0: Il Terminale (La Console)

Prima di iniziare, dobbiamo capire dove scrivere i comandi.
Il Terminale è quella finestra nera dove parli direttamente al computer.

### Come aprirlo

* **VS Code:** Vai nel menu in alto -> `Terminal` -> `New Terminal`. (Oppure premi `Ctrl + ò`).
* **Mac:** Cerca "Terminal" con la lente d'ingrandimento (Spotlight).
* **Windows:** Cerca "PowerShell" o "Command Prompt".

### I 3 Comandi Essenziali

1. **`ls`** (o `dir` su Windows):
    * Significa: "Fammi vedere cosa c'è in questa cartella".
    * Usalo spesso per capire dove sei.
2. **`cd`** (Change Directory):
    * Significa: "Entra in questa cartella".
    * Esempio: `cd Mio_Agente` (Entra nella cartella Mio_Agente).
    * Trucco: `cd ..` (Torna indietro di una cartella).
3. **`pwd`** (Print Working Directory):
    * Significa: "Dove sono?". Ti dice il percorso completo.

---

## 📅 Passo 1: La Cartella

Crea una nuova cartella sul desktop (o dove vuoi) e chiamala `Mio_Agente`.
Apri questa cartella col tuo editor di codice (VS Code, Cursor, ecc.).

---

## 🔐 Passo 2: Il File Segreto (`.env`)

**Attenzione:** Hai chiesto "come si crea la cartella .env".
⛔ **NON è una cartella!**
✅ **È un file di testo.**

1. Nel tuo editor, fai clic destro nello spazio vuoto -> **New File**.
2. Chiamalo esattamente: `.env` (inizia col punto, scritto minuscolo).
3. Incollaci dentro questo testo:

```text
# Qui ci vanno le chiavi. Sostituisci "sk-..." con la tua vera chiave.
OPENAI_API_KEY=sk-proj-1234567890abcdef...
GROQ_API_KEY=gsk_8H...
```

*Nota: Se usi Windows, il file potrebbe sembrarti senza nome. È normale.*

---

## 🛒 Passo 3: Gli Ingredienti (`requirements.txt`)

Dobbiamo dire al computer cosa serve.

1. Crea un nuovo file chiamato: `requirements.txt`
2. Incolla questo:

```text
openai
langchain
langchain-openai
python-dotenv
streamlit
```

1. Ora apri il **Terminale** (spesso è in basso nell'editor) e scrivi questo comando magico per installare tutto:
    `pip install -r requirements.txt`
    *(Premi Invio e aspetta che finisca le scritte bianche)*

---

## 🧠 Passo 4: Il Cervello (`agent.py`)

Ora creiamo l'intelligenza. Useremo **OpenAI (GPT)** per questo esempio, come hai chiesto.

1. Crea un nuovo file chiamato: `agent.py`
2. Incolla questo codice:

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 1. Carica la chiave dal file .env che abbiamo creato prima
load_dotenv() 

# 2. Crea il Cervello (qui scegliamo GPT-4o)
# Se volessi usare un altro modello (es. Claude), cambieresti solo queste righe.
il_cervello = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7  # Creatività (0=Serio, 1=Pazzo)
)

def chiedi(domanda):
    """Questa funzione prende una domanda e restituisce la risposta dell'AI"""
    risposta = il_cervello.invoke(domanda)
    return risposta.content

# 3. Test Rapido (Solo se lanci questo file direttamente)
if __name__ == "__main__":
    print(chiedi("Ciao! Dimmi una barzelletta."))
```

---

## 🎨 Passo 5: La Faccia (`app.py`)

Ora facciamo il sito web per usarlo comodamente.

1. Crea un nuovo file chiamato: `app.py`
2. Incolla questo codice:

```python
import streamlit as st
import agent  # Importiamo il file 'agent.py' che abbiamo appena scritto

# 1. Titolo del sito
st.title("🤖 Il Mio Assistente AI")

# 2. Casella per scrivere
testo_utente = st.text_input("Scrivi qui la tua domanda:")

# 3. Bottone
if st.button("Chiedi all'AI"):
    if testo_utente:
        st.write("🧠 Sto riflettendo...")
        
        # Chiamiamo la funzione 'chiedi' dal nostro file agent.py
        risposta = agent.chiedi(testo_utente)
        
        st.success(risposta)
    else:
        st.warning("Devi scrivere qualcosa prima!")
```

---

## 🚀 Passo 6: Accensione

Hai finito. Ora accendiamo tutto.

1. Nel terminale, assicurati di essere nella cartella giusta (scrivi `ls` e controlla se vedi `app.py`).
2. Scrivi:
    `streamlit run app.py`
3. Premi Invio.
4. Si aprirà automaticamente una pagina internet.

**Ecco fatto!** Hai creato un'app AI funzionante con un file per la chiave, un cervello separato e un'interfaccia grafica. 🦞🎉
