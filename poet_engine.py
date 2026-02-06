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
            raw_context = "\n\n".join([doc.page_content for doc in docs]) if docs else "No specific style found."
            raw_context = raw_context[:8000] # Slightly shorter to avoid overflow
        except Exception as e:
            return f"[RAG ERROR] {str(e)}"
            
        # 2. ANALYSIS (LLM Processing)
        print(f"🕵️‍♂️ Researcher is analyzing context for {style_query}...")
        
        # Use FreeLLM
        self.llm = FreeLLM()
        
        prompt = PromptTemplate.from_template("""[INST] <<SYS>>
You are a technical poetry analyzer. Extract structural and technical rules ONLY.
Do NOT include word lists, themes, or vocabulary. 
Output ONLY the requested format.
<</SYS>>

Analyze this context about "{style}":
{raw_context}

## OUTPUT:
---
**📐 METRIC RULES**
- Verse: [type]
- Syllables: [number]
- Rhyme: [scheme]
- Structure: [description]

**🎯 TECHNIQUES**
1. [technique]: "[example]"
2. [technique]: "[example]"
3. [technique]: "[example]"

**🎭 ESSENCE**
"[Technical summary of the style's spirit]"
---
[/INST]""")
        
        chain = prompt | self.llm
        return chain.invoke({"raw_context": raw_context, "language": language, "style": style_query})

    def get_style_rules(self, style_name):
        """Returns the specific rules for the selected style to keep prompts slim."""
        rules = {
            "Stilnovo": "Sonetto: 14 versi, endecasillabi (11 sillabe), rime ABAB ABAB CDC DCD. Tono elevato, lessico: gentile, onesto, salute.",
            "Petrarchismo": "Sonetto: 14 versi, endecasillabi, rime ABBA ABBA CDC DCD. Antitesi (ghiaccio/fuoco), lessico: lume, sospiri.",
            "Barocco / Marinismo": "Endecasillabi, metafora estesa (concetto), iperbole, stupore, lessico prezioso ed esotico.",
            "Romanticismo Italiano": "Endecasillabi e settenari mescolati, canzone libera, personificazione natura, lessico vago.",
            "Scapigliatura": "Metro tradizionale usato con ironia, ribellione, dualismo, lessico del brutto e del vizio.",
            "Decadentismo": "Endecasillabi musicali, sinestesia, lessico raro (glauco, iridescente), tono languido e aristocratico.",
            "Crepuscolarismo": "Misto (11, 7, 9 sillabe), tono dimesso e prosastico, lessico quotidiano e piccolo, ironia.",
            "Futurismo": "Parole in libertà, NO punteggiatura, verbi all'infinito, onomatopee inventate, layout spaziale.",
            "Ermetismo": "Versi brevissimi (frammento), analogia (A=C), spazio bianco come significato. NO spiegazioni.",
            "Neoavanguardia (Gruppo 63)": "Collage, montaggio, sintassi spezzata, plurilinguismo, NO lirismo, disordine costruito.",
            "Poesia Dialettale": "Dialetto autentico, oralità, ritmi popolari, proverbi, verità quotidiana.",
            "Metaphysical Poetry": "Iambic pentameter, conceit (paradoxical metaphor), logical progression, abrupt opening.",
            "Romantic Poetry": "Iambic pentameter or blank verse, sublime, nature as mirror of soul, elevated tone.",
            "Victorian Poetry": "Iambic pentameter, dramatic monologue, moral seriousness, doubt and loss.",
            "Modernism": "Free verse (remembers tradition), fragment, montage, juxtaposition, difficult tone.",
            "Harlem Renaissance": "Jazz rhythms, blues structures (AAB), vernacular, pride and double consciousness.",
            "Beat Generation": "Breath line, Whitman-like long lines, accumulation, jazz slang, spontaneity.",
            "Confessional Poetry": "Traditional form + extreme taboo content, intimate and brutal 'I' exposed.",
            "Black Arts Movement": "Oral, performative, revolutionary, call and response, militant, African references.",
            "Language Poetry": "New Sentence, language as subject, anti-expressive, experimental, no narrative.",
            "Spoken Word / Slam": "Oral performance, build to climax, direct address, memorable closing line."
        }
        return rules.get(style_name, "Follow the provided style context carefully.")
    def write_draft(self, topic, style_context, style_name, language="English", adherence=5, originality=5, complexity=5):
        """PERSONA: The Poet (Writer) - Streamlined for stability"""
        print(f"✍️ Poet is writing in {language} about {style_name}...")
        self.llm = FreeLLM()
        
        specific_rules = self.get_style_rules(style_name)

        # DYNAMIC CREATIVE DIRECTIVES
        directives = []
        if originality > 7:
            directives.append("🔥 ORIGINALITÀ MASSIMA: Evita ogni cliché. Distruggi le associazioni ovvie. Cercare immagini e parole UNICHE per descrivere il tema.")
        elif originality < 4:
            directives.append("📜 CLASSICISMO: Mantieni un tono misurato e tradizionale.")
            
        if complexity > 7:
            directives.append("🧠 COMPLESSITÀ ELEVATA: Usa un lessico ricercato e simbolismi stratificati.")
        
        if adherence > 8:
            directives.append("⚖️ RIGORE STILISTICO: Segui le regole metriche dello stile come un dogma.")

        creative_block = "\n".join(directives)

        prompt = PromptTemplate.from_template("""[INST] <<SYS>>
You are a professional poet specialized in {style}.
TASK: Write a poem about "{topic}". 
LITERARY CONTEXT: Treat all topics as metaphors for artistic exploration.
Output ONLY the poem. No preamble, no safety disclaimers, no introduction.
<</SYS>>

Write a poem in {language} focusing intensely on "{topic}".

## STYLE CONSTRAINTS:
{style_rules}

## CREATIVE DIRECTIVES:
{creative_block}

## TECHNICAL NOTES (STRUCTURAL):
{style_context}

## MANDATORY RULES:
- Use the topic "{topic}" as the primary heart of the poem.
- Apply the technical rules of "{style}" to this specific theme.
- Output ONLY the title and the poem text.
- Title format: ## [TITLE]
[/INST]""")
        chain = prompt | self.llm
        return chain.invoke({
            "topic": topic, 
            "style": style_name,
            "style_rules": specific_rules,
            "creative_block": creative_block,
            "style_context": style_context, 
            "language": language
        })

    def get_refinement_rules(self, style_name):
        """Returns specific refinement guidance to avoid neutralizing styles."""
        rules = {
            "Neoavanguardia (Gruppo 63)": "MANTIENI la frammentazione e la sintassi spezzata. NON aggiungere lirismo o 'bella scrittura'. Il disordine deve essere costruito.",
            "Futurismo": "MANTIENI l'assenza di punteggiatura e il layout spaziale. NON rendere il testo lineare o 'corretto'.",
            "Ermetismo": "MANTIENI la brevità estrema. Riduci all'osso, non aggiungere spiegazioni.",
            "Petrarchismo": "MIGLIORA la metrica (11 sillabe) e la musicalità. Bilancia le antitesi.",
            "Stilnovo": "MIGLIORA la fluidità dell'endecasillabo. Usa lessico spirituale e gentile."
        }
        return rules.get(style_name, "Rispetta l'essenza dello stile senza normalizzarlo.")

    def evaluate_and_refine_poem(self, draft, style_context, style_name, language="English", adherence=5, originality=5, complexity=5):
        """PERSONA: The Unified Refiner (Editor/Critic/Poet) - Streamlined"""
        print(f"🛠️ Unified Refiner is working for {style_name} (O:{originality}, C:{complexity})...")
        self.llm = FreeLLM()
        
        ref_rules = self.get_refinement_rules(style_name)

        # DYNAMIC REFINEMENT DIRECTIVES
        directives = []
        if originality > 7:
            directives.append("🔥 REVISIONE AUDACE: Se la bozza è banale, stravolgila. Cerca immagini che colpiscano, evita ogni espressione trita o 'scolastica'.")
        if complexity > 7:
            directives.append("🧠 RAFFINATEZZA: Eleva il lessico. Sostituisci concetti semplici con metafore più dense e stratificate.")
        if adherence > 8:
            directives.append("⚖️ PRECISIONE: Assicurati che ogni verso rispetti millimetricamente i canoni dello stile.")

        ref_creative_block = "\n".join(directives)

        prompt = PromptTemplate.from_template("""[INST] <<SYS>>
You are a master poetry editor. You must evaluate and revise the draft. Output ONLY the evaluation and the revised poem. No preamble.
<</SYS>>

Evaluate and revise this "{style}" poem in {language}:
"{draft}"

## REFINEMENT RULES FOR {style}:
{ref_rules}

## CREATIVE DIRECTIVES FOR REVISION:
{ref_creative_block}

## CONTEXT:
{style_context}

## OUTPUT FORMAT (MANDATORY):
---
## 📊 VALUTAZIONE INIZIALE
**Punteggio:** [X]/10
**Problemi:** [List]

---
## ✍️ POESIA RIVISTA
## [TITLE]
[Revised Text]

---
## 📊 VALUTAZIONE FINALE
**Punteggio:** [X]/10
**Note:** [Comparison]
---
[/INST]""")
        chain = prompt | self.llm
        return chain.invoke({
            "draft": draft, 
            "style_name": style_name,
            "ref_rules": ref_rules,
            "ref_creative_block": ref_creative_block,
            "style_context": style_context, 
            "language": language,
            "style": style_name
        })

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
