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
    
    api_key: str = "apf_xd90bt1rgoyki1w4erddtq1s"
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
        self.vector_store_path = "06_Poetry_Agent/chroma_db"
        
        # 2. Setup LLM (The Brain) - CUSTOM FREE LLM
        self.llm = FreeLLM()
        
        # 3. Initialize/Load Knowledge Base
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Loads ALL poetic styles from the knowledge_base folder."""
        if os.path.exists(self.vector_store_path):
            self.vectorstore = Chroma(persist_directory=self.vector_store_path, embedding_function=self.embeddings)
            return

        print("📚 Initializing Knowledge Base from Folder...")
        loader = DirectoryLoader("06_Poetry_Agent/knowledge_base/", glob="*.txt", loader_cls=TextLoader)
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

    def critique_poem(self, draft, style_context, language="English"):
        """PERSONA: The Critic (Editor)"""
        print(f"🧐 Critic is analyzing in {language}...")
        
        self.llm = FreeLLM()

        prompt = PromptTemplate.from_template("""
SYSTEM:
You are a poetry critic. Evaluate the draft.

Write in {language}.

## INTERNAL ANALYSIS (do not show):

Internally, you must:
1. Count syllables of every verse
2. Check rhyme scheme
3. Verify techniques are present
4. Identify clichés
5. Find the best and worst verses
6. Calculate scores for metrics, style, quality

Do all this SILENTLY.

## OUTPUT ONLY:

---

**Verdict:** [✅ APPROVED / 🔄 REVISION NEEDED / ❌ REWRITE]

**Score:** [X]/10

**Strengths:**
- [strength 1]
- [strength 2]

**Problems to fix:**
1. [specific problem with verse quote]
2. [specific problem]

**Instructions for revision:**
[If revision needed: specific instructions]

---

⚠️ Do NOT show:
- Syllable counts
- Verse-by-verse analysis tables
- Your reasoning process
- Score breakdowns by category

Show ONLY the verdict, overall score, strengths, problems, and instructions.

USER:
Style Context:
{style_context}

Draft Poem:
{draft}
""")
        chain = prompt | self.llm
        return chain.invoke({"draft": draft, "style_context": style_context, "language": language, "style": "this style"})

    def refine_poem(self, draft, critique, interpretation, style_context, language="English"):
        """PERSONA: The Refiner (Editor/Polisher) - Strict Output"""
        print(f"💅 Refiner is working in {language}...")
        
        self.llm = FreeLLM()
        
        prompt = PromptTemplate.from_template("""
SYSTEM:
You are the poet revising your work. You have received criticism and analysis. Now IMPROVE — but respect the style.

Write in {language}.

## ⚠️ THE GOLDEN RULE

> **"Improve" does NOT mean "make more conventionally poetic"**

For many styles, "rough" IS correct:
- Gruppo 63: fragmentation is INTENTIONAL
- Futurismo: chaos is INTENTIONAL  
- Ermetismo: brevity is INTENTIONAL
- Beat: rawness is INTENTIONAL

If the draft already respects the style, CHANGE AS LITTLE AS POSSIBLE.

---

## INTERNAL PROCESS (do not show):

1. **Identify the style's rules** (see below)
2. **Check if the draft respects them**
3. **If YES:** Make MINIMAL changes — only fix real errors
4. **If NO:** Fix ONLY what violates the style
5. **NEVER add conventional "poetic" elements if the style rejects them**

---

## WHAT "IMPROVE" MEANS — BY STYLE

### ——— 🇮🇹 ITALIANO ———

**STILNOVO / PETRARCHISMO:**
- Improve = perfect the meter (11 syllables), fix rhyme scheme
- ADD elegance, musicality
- OK to make more fluid

**BAROCCO / MARINISMO:**
- Improve = intensify the "meraviglia"
- ADD more elaborate conceits
- More virtuosity is good

**ROMANTICISMO:**
- Improve = deepen emotion, nature imagery
- ADD musicality, flow
- More lyrical is good

**SCAPIGLIATURA:**
- Improve = sharpen contrasts, rebellion
- Keep the darkness, the "maledettismo"
- Do NOT soften

**DECADENTISMO:**
- Improve = intensify sensory richness
- ADD rare words, synesthesia
- More languor, more exotic

**CREPUSCOLARISMO:**
- Improve = make MORE humble, MORE prosaic
- Do NOT elevate the tone
- Keep the "piccolo", the "povero"
- Irony must stay

**FUTURISMO:**
- Improve = more energy, more explosion
- Do NOT add punctuation
- Do NOT make verses flow smoothly
- Keep spatial layout
- Keep onomatopoeia
- NEVER add conventional imagery

**ERMETISMO:**
- Improve = REMOVE words, not add them
- Shorter is better
- More silence, more white space
- NEVER explain, NEVER expand
- If it's already minimal, LEAVE IT

**NEOAVANGUARDIA (GRUPPO 63):**
⚠️ CRITICAL — This style REJECTS conventional poetry:
- Do NOT make it "flow better"
- Do NOT add lyrical images ("danza", "sogni", "eco")
- Do NOT smooth the syntax
- Do NOT make it "more poetic"
- KEEP the fragmentation
- KEEP the harshness
- KEEP the collage effect
- KEEP mixed registers (technical + everyday)
- KEEP the anti-lyricism
- If it's already fragmented and strange, LEAVE IT ALONE
- "Ugly" on purpose = CORRECT

**POESIA DIALETTALE:**
- Improve = more authenticity
- Keep the oral rhythm
- Do NOT Italianize the dialect


### ——— 🇬🇧 ENGLISH ———

**METAPHYSICAL:**
- Improve = sharpen the conceit, the argument
- More wit is good
- Can be more elaborate

**ROMANTIC:**
- Improve = deepen emotion, imagery
- More lyrical is good
- ADD apostrophe, personification

**VICTORIAN:**
- Improve = more gravity, more music
- Elaborate rhyme is good

**DECADENTISM:**
- Improve = more sensory, more artificial
- Rare words, French borrowings OK

**MODERNISM:**
- Improve = sharpen the fragment
- Do NOT make it flow
- Keep difficulty
- REMOVE unnecessary words

**HARLEM RENAISSANCE:**
- Improve = sharpen rhythm
- Keep jazz/blues feel
- Keep vernacular

**BEAT GENERATION:**
- Improve = more breath, more accumulation
- Keep rawness
- Do NOT conventionalize
- Keep the spontaneous feel

**CONFESSIONAL:**
- Improve = sharper images, tighter form
- Keep the brutality
- Do NOT soften the content

**BLACK ARTS:**
- Improve = more power, more call-and-response
- Keep militancy
- Do NOT soften

**LANGUAGE POETRY:**
- Improve = more indeterminacy
- Do NOT add "meaning"
- Do NOT make it "clear"
- Keep the procedure

**SLAM / SPOKEN WORD:**
- Improve = better build, stronger closing
- Keep oral quality
- Test by reading aloud

---

## FORBIDDEN ACTIONS

❌ NEVER add "danza", "sogni", "eco", "senza posa" to anti-lyrical styles
❌ NEVER smooth fragmented syntax in Gruppo 63, Futurismo, Modernism
❌ NEVER add adjectives to Ermetismo
❌ NEVER lengthen verses in minimal styles
❌ NEVER add conventional "beauty" to styles that reject it
❌ NEVER turn collage into narrative
❌ NEVER add punctuation to Futurismo

---

## DECISION TREE
Is the draft already respecting the style's rules?
│
├── YES → Change ONLY what the Critic specifically flagged
│ Keep everything else IDENTICAL
│
└── NO → Fix ONLY the style violations
Do NOT "improve" in other ways

---

## OUTPUT

Output ONLY the revised poem:

---

## [TITLE]

[The poem — minimal changes from original if style was already correct]

---

⚠️ CRITICAL:
- No explanations
- No changelog
- No "I changed X because Y"
- Just the clean poem
- If the original was good, the revision should be ALMOST IDENTICAL

USER:
Style Context:
{style_context}

Original Draft:
{draft}

Critic's Feedback:
{critique}

Interpreter's Analysis:
{interpretation}
""")
        chain = prompt | self.llm
        return chain.invoke({"draft": draft, "critique": critique, "interpretation": interpretation, "style_context": style_context, "language": language})

    def interpret_poem(self, poem, language="English"):
        """PERSONA: The Interpreter (Scholar)"""
        print(f"🔮 Interpreter is analyzing in {language}...")
        
        self.llm = FreeLLM()
        
        prompt = PromptTemplate.from_template("""
SYSTEM:
You are a literary scholar. Analyze the poem to help with revision.

Write in {language}.

## INTERNAL ANALYSIS (do not show):

Internally, perform:
1. Complete scansion of every verse
2. Identify all rhetorical devices
3. Analyze sound patterns
4. Find intertextual echoes
5. Determine what works and what doesn't

Do all this SILENTLY.

## OUTPUT ONLY:

---

**Interpretation:**
[2-3 sentences: what the poem means/does]

**What works (preserve):**
- "[quote]" — [why it works]
- "[quote]" — [why it works]

**What needs work:**
- "[quote]" — [problem] — [suggestion]
- "[quote]" — [problem] — [suggestion]

**The heart:**
The essential verse is: "[quote]"

---

⚠️ Do NOT show:
- Syllable-by-syllable scansion
- Tables of rhetorical devices
- Detailed formal analysis
- Your reasoning steps

Show ONLY the clean synthesis above.

USER:
The Poem:
{poem}
""")
        chain = prompt | self.llm
        return chain.invoke({"poem": poem, "language": language})

    def parse_critic_score(self, critique_text):
        """Helper to extract the score extracted from the Critic's text."""
        try:
             import re
             # 1. New Silent Mode Pattern: "**Score:** [8.5]/10" or "**Score:** 8.5/10"
             # Supports optional bolding, optional brackets, optional /10
             match = re.search(r"Score:?\*\*\s*(?:\[)?([\d\.]+)(?:\])?(?:/10)?", critique_text, re.IGNORECASE)
             if match:
                 return float(match.group(1))

             # 1b. Alternative standard pattern: "**Score:** [X]/10"
             match = re.search(r"\*\*Score:\*\*\s*(?:\[)?([\d\.]+)(?:\])?", critique_text, re.IGNORECASE)
             if match:
                 return float(match.group(1))
             
             # 2. Legacy Pattern (Backup)
             match = re.search(r"\*\*AVERAGE\*\*\s*\|\s*\*\*([\d\.]+)/10\*\*", critique_text)
             if match:
                 return float(match.group(1))
             
             # 3. Simple Fallback
             match = re.search(r"Score:?\s*([\d\.]+)", critique_text, re.IGNORECASE)
             if match:
                 score = float(match.group(1))
                 if score > 10: score = 0 # Avoid parsing years or wrong numbers
                 return score
                 
             return 0.0
        except:
             return 0.0
