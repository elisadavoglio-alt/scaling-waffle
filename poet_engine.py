import os
import time
import requests
from typing import Any, List, Optional, Mapping
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

# --- CUSTOM FREE LLM WRAPPER ---
class FreeLLM(LLM):
    """Custom wrapper for apifreellm.com"""
    
    api_key: str = os.getenv("FREELLM_API_KEY", "YOUR_KEY_HERE")
    endpoint: str = "https://apifreellm.com/api/v1/chat"
    
    @property
    def _llm_type(self) -> str:
        return "custom_free_llm"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        

        print(f"DEBUG: sending prompt to FreeLLM (first 300 chars):\n{prompt[:300]}\n...\n")

        # Payload format specific to this API
        payload = {
            "message": prompt,
            "model": "apifreellm" 
        }
        
        max_retries = 3
        retry_delay = 10 # Base delay
        
        for attempt in range(max_retries):
            print(f"⏳ FreeLLM: Waiting {retry_delay}s for rate limit (Attempt {attempt+1}/{max_retries})...")
            time.sleep(retry_delay)
            
            try:
                response = requests.post(self.endpoint, headers=headers, json=payload)
                
                if response.status_code == 429:
                    print(f"⚠️ API 429: Rate limit hit. Backing off...")
                    retry_delay += 10 # Increase delay for next attempt
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                if data.get("success"):
                    return data.get("response", "")
                else:
                    return f"Error: {data}"
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"API ERROR after {max_retries} attempts: {str(e)}"
                print(f"⚠️ Request failed, retrying in {retry_delay}s... ({e})")
                time.sleep(2)
        
        return "API ERROR: Max retries exceeded."

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"endpoint": self.endpoint}

class PoetryAgent:
    def __init__(self):
        # 1. Setup Embeddings & VectorStore
        # FIX: Force CPU to avoid "meta tensor" errors on some Mac configs
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        # Path Resolution (Auto-detect if running inside the folder or from parent)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.vector_store_path = os.path.join(base_dir, "chroma_db")
        self.knowledge_base_path = os.path.join(base_dir, "knowledge_base/")
        
        # 2. Setup LLM (The Brain) - CUSTOM FREE LLM
        self.llm = FreeLLM()
        
        # 3. Initialize/Load Knowledge Base
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Loads ALL poetic styles from the knowledge_base folder."""
        if os.path.exists(self.vector_store_path):
            self.vectorstore = Chroma(persist_directory=self.vector_store_path, embedding_function=self.embeddings)
            return

        print(f"📚 Initializing Knowledge Base from: {self.knowledge_base_path}")
        loader = DirectoryLoader(self.knowledge_base_path, glob="*.txt", loader_cls=TextLoader)
        documents = loader.load()
        
        if not documents:
            print("⚠️ No documents found in knowledge_base!")
            return

        # Improved Splitter to avoid massive chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        
        self.vectorstore = Chroma.from_documents(
            documents=docs, 
            embedding=self.embeddings, 
            persist_directory=self.vector_store_path
        )
        print(f"✅ Knowledge Base Ready! Loaded {len(documents)} source files.")

    def research_style(self, style_query, language="English"):
        """PERSONA: The Researcher (RAG Analysis)"""
        print(f"🕵️‍♂️ Researcher looking for: {style_query}")
        
        # 1. RETRIEVAL (Raw Data)
        if not hasattr(self, 'vectorstore') or not self.vectorstore:
             return f"[UI TESTING] RAG Empty. Style: {style_query} (No context loaded)"

        try:
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2}) # Reduce k to 2
            docs = retriever.invoke(style_query)
            # Truncate raw context strictly to fit 32k limits (thought 12k is safe)
            raw_context = "\n\n".join([doc.page_content for doc in docs]) if docs else "No specific style found."
            raw_context = raw_context[:10000] 
        except Exception as e:
            return f"[RAG ERROR] {str(e)}"
            
        # 2. ANALYSIS (LLM Processing)
        print(f"🕵️‍♂️ Researcher is analyzing context for {style_query}...")
        
        # Use FreeLLM
        self.llm = FreeLLM()
        
        prompt = PromptTemplate.from_template("""
SYSTEM:
You are a poetry research assistant. Analyze the retrieved context and provide structured material for the Poet.

## INTERNAL PROCESS (do not show):
- Read all retrieved texts
- Identify metric rules
- Extract techniques
- Find vocabulary
- Note anti-patterns

## OUTPUT ONLY THIS (clean format):

---

**📐 METRIC RULES**
- Verse: [type]
- Syllables: [number]
- Rhyme: [scheme]
- Structure: [description]

**🎯 TECHNIQUES**
1. [technique]: "[example from context]"
2. [technique]: "[example]"
3. [technique]: "[example]"

**📚 VOCABULARY**
[20-30 typical words]

**⚠️ AVOID**
1. [anti-pattern]
2. [anti-pattern]
3. [anti-pattern]

**🎭 ESSENCE**
"[One sentence: what this style DOES]"

---

⚠️ Do NOT show your analysis process. Only the structured output above.

USER:
RETRIEVED CONTEXT:
{raw_context}
""")
        
        chain = prompt | self.llm
        return chain.invoke({"raw_context": raw_context, "language": language, "style": style_query})

    def write_draft(self, topic, style_context, style_name, language="English", adherence=5, originality=5, complexity=5):
        """PERSONA: The Poet (Writer) - Creative Overhaul"""
        import random
        print(f"✍️ Poet is writing in {language}...")

        # FreeLLM does not support params like temperature, so we just instantiate it
        self.llm = FreeLLM()

        # -- LOGIC: RANDOM CONSTRAINTS INJECTION --
        CONSTRAINTS_POOL = [
            "Iniziare con un suono, non una parola (es. 'Clang!', 'Sshhh')",
            "Contenere un numero specifico (non 'mille', un numero esatto come '42' o 'sette')",
            "Avere un verso di una sola sillaba",
            "Usare una parola inventata/neologismo",
            "Contenere un colore mai associato al tema (es. 'mare rosso', 'sole nero')",
            "Avere il verso più lungo alla fine",
            "Includere un oggetto quotidiano (forbici, tazza, chiave) in contesto onirico",
            "Non usare MAI il verbo 'essere'",
            "Avere un verso che è una domanda diretta al lettore",
            "Contenere uno spazio bianco significativo (verso vuoto o spezzato)",
            "Usare la stessa parola 3 volte in posizioni diverse",
            "Includere un senso inaspettato (olfatto per il mare, suono per il silenzio)"
        ]
        
        # Select 2-3 random constraints based on originality
        num_constraints = 2 if originality < 7 else 3
        selected_constraints = random.sample(CONSTRAINTS_POOL, num_constraints)
        constraints_str = "\n".join([f"- [ ] {c}" for c in selected_constraints])

        prompt = PromptTemplate.from_template("""
SYSTEM:
You are a master poet. Write a poem in {language} about "{topic}" in the style of {style}.

## INTERNAL PROCESS (do not show to user):

Internally, before writing, you MUST:
1. Extract metric rules from context (syllables, rhyme scheme)
2. List techniques you'll use
3. Brainstorm: discard obvious associations, find unexpected ones
4. Generate 3 versions (safe/strange/extreme), choose the boldest
5. Verify syllable count for EVERY verse
6. Check for clichés and remove them

Do all this thinking SILENTLY.

## METRIC RULES BY STYLE (apply internally, do not show)

### ——— 🇮🇹 ITALIANO ———

**STILNOVO:**
- Sonetto: 14 versi
- Metro: endecasillabi (11 sillabe)
- Rime: ABAB ABAB CDC DCD (o ABBA ABBA CDC DCD)
- Accenti: su 4a o 6a, e sempre su 10a
- Tono: elevato, spirituale
- Lessico: gentile, onesto, valore, salute, core

**PETRARCHISMO:**
- Sonetto: 14 versi
- Metro: endecasillabi (11 sillabe)
- Rime: ABBA ABBA CDC DCD (schema petrarchesco)
- Figure: antitesi (ghiaccio/fuoco), ossimoro
- Lessico: lume, sospiri, pianto, donna, amore

**BAROCCO / MARINISMO:**
- Metro: endecasillabi, ma libertà maggiore
- Strofe: variabili
- Rime: presenti, spesso virtuosistiche
- Figure: concetto (metafora estesa), iperbole estrema, accumulo
- Obiettivo: "meraviglia" — stupire il lettore
- Lessico: prezioso, esotico, anatomico

**ROMANTICISMO ITALIANO:**
- Metro: endecasillabi + settenari (7 sillabe) mescolati
- Struttura: canzone libera (strofe di lunghezza variabile)
- Rime: libere, non obbligatorie ma presenti
- Figure: personificazione natura, interrogative retoriche
- Lessico: vago, indefinito, natura, patria, infinito (MA usato diversamente)

**SCAPIGLIATURA:**
- Metro: tradizionale ma "stanco", usato con ironia
- Rime: presenti, a volte volutamente facili
- Tono: ribelle, maledetto, autodistruttivo
- Figure: contrasti violenti, lessico del brutto
- Temi: bohème, vizio, dualismo, morte

**DECADENTISMO:**
- Metro: endecasillabi fluidi, musicalissimi
- Rime: ricercate, preziose
- Figure: sinestesia sistematica, accumulo sensoriale
- Lessico: raro, esotico (colori: glauco, iridescente; fiori: orchidea, ninfea)
- Tono: languido, estenuato, aristocratico
- D'Annunzio: versi lunghi, panismo, fusione con natura

**CREPUSCOLARISMO:**
- Metro: misto (endecasillabi, settenari, novenari)
- Rime: semplici, quasi da filastrocca, o assenti
- Tono: dimesso, prosastico, sussurrato
- Lessico: quotidiano, piccolo, povero
- Figure: diminutivi ("piccolo libro", "povera cosa")
- Ironia: sulla poesia stessa

**FUTURISMO:**
- Metro: ABOLITO — parole in libertà
- Struttura: spaziale, non lineare
- NO punteggiatura tradizionale
- Verbi: solo infinito ("esplodere", "vibrare")
- Sostantivi: doppi senza preposizione ("uomo-siluro")
- Segni: + - × = numeri
- Onomatopee: INVENTATE (non "boom" ma "ZANG TUMB TUUUMB")
- Layout: parole sparse, diagonali, dimensioni variabili

**ERMETISMO:**
- Metro: libero, versi brevissimi (anche 2-3 sillabe)
- Struttura: frammento
- Spazio bianco: parte del significato
- Figure: analogia ermetica (A=C senza B), ellissi radicale
- NO: spiegazioni, discorsività, aggettivi decorativi
- Lessico: parole nude (luce, pietra, muro, osso, foglia, sera)
- Titolo: parte essenziale del testo

**NEOAVANGUARDIA (GRUPPO 63):**
- Metro: distrutto e ricostruito, o tradizionale usato ironicamente
- Struttura: collage, montaggio, cut-up
- Sintassi: spezzata, interrotta
- Registri: mescola alto/basso, inserti pubblicitari, tecnici, burocratici
- Figure: citazione straniata, pastiche
- NO: lirismo, io autobiografico, "bella scrittura"
- Plurilinguismo: mescola lingue/registri
- Il "disordine" è COSTRUITO, non casuale

**POESIA DIALETTALE:**
- Metro: variabile, spesso riprende forme popolari
- Lingua: dialetto autentico (romanesco, milanese, napoletano, etc.)
- Tono: oralità, ritmi locali
- Temi: vita quotidiana, amore, morte, lavoro
- Figure: proverbi, modi di dire locali
- Autenticità: il dialetto = verità


### ——— 🇬🇧 ENGLISH ———

**METAPHYSICAL POETRY:**
- Meter: iambic pentameter (10 syllables, da-DUM × 5)
- Rhyme: couplets or quatrains
- Structure: argument-like, logical progression
- Figures: conceit (extended paradoxical metaphor), wit
- Opening: often abrupt, dramatic ("For God's sake hold your tongue")
- Tone: intellectual + passionate

**ROMANTIC POETRY:**
- Meter: iambic pentameter (blank verse) or varied
- Rhyme: varied (blank verse = no rhyme, odes = complex schemes)
- Figures: personification of nature, apostrophe ("O wild West Wind!")
- Enjambment: frequent, expressive
- Themes: sublime, nature as mirror of soul, imagination
- Tone: elevated, musical

**VICTORIAN POETRY:**
- Meter: iambic pentameter, or varied
- Structure: dramatic monologue (Browning), elegy (Tennyson)
- Rhyme: often elaborate schemes
- Hopkins: SPRUNG RHYTHM (count stresses, not syllables)
- Tone: earnest, conflicted, morally serious
- Themes: doubt, duty, loss

**DECADENTISM / AESTHETICISM:**
- Meter: varied, often French forms (villanelle, rondeau)
- Rhyme: musical, refrain-like
- Figures: sensory overload, paradox
- Vocabulary: rare, Latinate, French words (ennui, frisson)
- Colors: heliotrope, mauve, amber
- Tone: world-weary, artificial, posed
- Themes: art for art's sake, beauty in decay

**MODERNISM:**
- Meter: FREE VERSE (but aware of tradition)
- Structure: fragment, montage, juxtaposition
- Pound's rules: "Direct treatment of the thing", no unnecessary words
- Eliot: free verse that REMEMBERS pentameter
- Figures: objective correlative, mythical method
- Allusion: multilingual, classical
- Tone: impersonal, difficult

**HARLEM RENAISSANCE:**
- Meter: varied — jazz rhythms, blues structures
- Structure: often 12-bar blues (AAB), or free
- Figures: call and response, vernacular + high register
- Themes: Black identity, double consciousness, Africa, Harlem
- Tone: proud, yearning, celebratory + mournful
- Rhythm: syncopation, jazz

**BEAT GENERATION:**
- Meter: BREATH LINE — one verse = one breath
- Structure: long Whitman-like lines
- Figures: accumulation, catalog, anaphora ("who...", "I saw...")
- NO traditional meter — organic rhythm
- Vocabulary: colloquial + sacred, jazz slang, Buddhist references
- Spontaneity: "first thought, best thought" (but crafted)

**CONFESSIONAL POETRY:**
- Meter: often traditional (Plath uses tercets, controlled stanzas)
- Rhyme: present but often slant (near-rhyme)
- Tension: controlled form + extreme content
- Themes: taboo (suicide, madness, family trauma, body)
- Tone: intimate, brutal, "I" exposed
- Plath/Sexton: percussive, short verses

**BLACK ARTS MOVEMENT:**
- Meter: oral, performative
- Structure: for the voice
- Figures: call and response, repetition as ritual
- Vocabulary: vernacular, militant, African references
- Tone: revolutionary, communal
- Purpose: art as weapon, Black aesthetics

**LANGUAGE POETRY:**
- Meter: NONE traditional
- Structure: "New Sentence" (each sentence autonomous)
- Figures: procedure over inspiration, indeterminacy
- NO: authentic "voice", confession, linear narrative
- The LANGUAGE is the subject, not transparent
- Reader as producer of meaning
- Highly experimental, anti-expressive

**SPOKEN WORD / SLAM:**
- Meter: ORAL — written for performance
- Structure: build to climax
- Pauses: mark with / or line breaks
- Figures: repetition for emphasis, direct address ("you")
- Hook: immediate, grabs attention
- Movement: personal story → universal truth
- Closing line: MUST be memorable
- Test: if it doesn't work spoken aloud, it doesn't work

## BLACKLIST (never use):
- sea=infinity, silence=peace, light=hope, heart=love, eyes=soul
- Words: eternal, infinite, profound, soul, whisper, embrace
- Structures: "Like X, Y...", "In the silence of..."

## CONSTRAINTS FOR THIS SPECIFIC POEM:
{constraints_str}

## OUTPUT ONLY:
Output the poem in this clean format:
## [TITLE]
[Poem text]

⚠️ CRITICAL: 
- Output ONLY the title and poem
- No explanations, no process description
- No before/after, no meta-commentary
- Just the poem itself, clean and final.

USER:
Topic: {topic}
Style: {style}

Style Context (RESEARCHER NOTES):
{style_context}
""")
        chain = prompt | self.llm
        return chain.invoke({
            "topic": topic, 
            "style": style_name,
            "style_context": style_context, 
            "language": language, 
            "constraints_str": constraints_str
        })

    def evaluate_and_refine_poem(self, draft, style_context, language="English"):
        """PERSONA: The Unified Refiner (Editor/Critic/Poet) - Consolidated Flow"""
        print(f"🛠️ Unified Refiner is working in {language}...")
        
        self.llm = FreeLLM()
        
        prompt = PromptTemplate.from_template("""
SYSTEM:
You are a poetry editor. You will evaluate, revise, and re-evaluate a poem.

Write in {language}.

---

## YOUR TASK

1. Score the draft (BEFORE)
2. Revise it (respecting the style!)
3. Score the revision (AFTER)

---

## ⚠️ CRITICAL: RESPECT THE STYLE

"Improve" means DIFFERENT things for different styles:

**Styles where "improve" = more fluid, more lyrical:**
- Stilnovo, Petrarchismo, Romanticismo, Decadentismo, Victorian, Romantic

**Styles where "improve" = more fragmented, more harsh:**
- Gruppo 63 / Neoavanguardia
- Futurismo
- Modernism
- Language Poetry

**Styles where "improve" = more minimal, more silence:**
- Ermetismo

**Styles where "improve" = more raw, more oral:**
- Beat Generation
- Slam / Spoken Word
- Black Arts Movement

---

## SPECIFIC RULES BY STYLE

### GRUPPO 63 / NEOAVANGUARDIA:
- ✅ Keep fragmentation
- ✅ Keep short, broken verses
- ✅ Keep mixed registers
- ✅ Keep harshness
- ❌ Do NOT add "danza", "sogni", "eco", "senza posa"
- ❌ Do NOT smooth syntax
- ❌ Do NOT make it "flow"
- ❌ Do NOT add conventional lyricism
- If the draft is already fragmented and harsh → MINIMAL CHANGES

### FUTURISMO:
- ✅ Keep spatial layout
- ✅ Keep onomatopoeia
- ✅ Keep no punctuation
- ❌ Do NOT add periods, commas
- ❌ Do NOT make it linear

### ERMETISMO:
- ✅ Shorter is better
- ✅ More white space
- ❌ Do NOT add words
- ❌ Do NOT explain

### PETRARCHISMO / STILNOVO:
- ✅ Perfect the meter (11 syllables)
- ✅ Fix rhyme scheme (ABBA ABBA CDC DCD)
- ✅ More fluid is good

### BEAT GENERATION:
- ✅ Keep the breath, the accumulation
- ✅ Keep rawness
- ❌ Do NOT conventionalize

---

## SCORING CRITERIA

**A. Style Adherence (40%)**
- Does it follow the style's rules?
- Does it use the right techniques?
- Does it avoid what the style forbids?

**B. Poetic Quality (30%)**
- Are images fresh (not clichéd)?
- Is there at least one memorable moment?
- Does it work for this style?

**C. Metrics/Form (30%)**
- If the style requires meter: is it correct?
- If the style requires rhyme: is the scheme correct?
- If the style is free: is there organic rhythm?

**Score:**
- 9-10: Excellent, anthology-worthy
- 7-8: Good, minor issues
- 5-6: Mediocre, several problems
- 1-4: Fails the style

---

## FORBIDDEN IN REVISION

❌ Adding "poetic" words to anti-lyrical styles:
   - danza, sogni, eco, anima, infinito, eterno, sussurro, abbraccio

❌ Smoothing fragmented syntax in:
   - Gruppo 63, Futurismo, Modernism, Language Poetry

❌ Lengthening verses in:
   - Ermetismo, Imagism

❌ Adding punctuation to:
   - Futurismo

❌ Making "prettier" styles that reject prettiness

---

## OUTPUT FORMAT

Output EXACTLY this format:

---

## 📊 VALUTAZIONE INIZIALE

**Punteggio:** [X]/10

**Punti di forza:**
- [strength 1]
- [strength 2]

**Problemi:**
- [problem 1]
- [problem 2]

---

## ✍️ POESIA RIVISTA

## [TITLE]

[The revised poem]

---

## 📊 VALUTAZIONE FINALE

**Punteggio:** [X]/10

**Miglioramenti ottenuti:**
- [what improved]
- [what improved]

**Note:**
[If score didn't improve much: explain why — e.g., "The original was already good for this style"]

---

⚠️ IMPORTANT:
- If the original already respects the style well → score should be similar, changes minimal
- A poem that goes from 6/10 to 5/10 after revision = YOU FAILED (you made it worse)
- For Gruppo 63: a harsh, fragmented 7/10 is better than a smooth, lyrical 5/10
- Show HONEST scores — don't inflate

USER:
Style Context:
EVITA L'ESASPERAZIONE: Non cadere nella caricatura dello stile. L'opera deve mantenere una sua naturalezza artistica e dignità letteraria. Evita eccessi meccanici (es. troppe ripetizioni, eccessiva punteggiatura o frammentazione estrema) se questi degradano il senso poetico invece di elevarlo. 

Original Draft:
{draft}
""")
        chain = prompt | self.llm
        return chain.invoke({"draft": draft, "style_context": style_context, "language": language})

    def parse_critic_score(self, text):
        """Helper to extract the score from the unified evaluation text."""
        import re
        try:
            # Look for Punteggio: X/10 or Score: X/10
            match = re.search(r'(?:Punteggio|Score):\s*\*?\*?\[?(\d+(?:\.\d+)?)(?:\])?/10', text, re.IGNORECASE)
            if match:
                return float(match.group(1))
            
            # Fallback for just the number
            match = re.search(r'Punteggio:\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                if score > 10: score = 0 # Avoid parsing years or wrong numbers
                return score
                
            return 5.0 
        except:
            return 5.0
