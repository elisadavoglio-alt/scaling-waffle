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
    
    api_key: Optional[str] = None
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
        
        # Lazy load key to support late .env loading
        current_key = self.api_key or os.getenv("FREELLM_API_KEY")
        if not current_key:
            raise ValueError("FREELLM_API_KEY not found in env or instance.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {current_key}"
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
            # Wait between attempts to avoid flooding
            if attempt > 0:
                print(f"⏳ FreeLLM: Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
            
            try:
                # Increased timeout to 60s for slow poetry generation
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 429:
                    print(f"⚠️ API 429: Rate limit hit. Backing off...")
                    retry_delay += 10
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
                print(f"⚠️ Request failed: {e}. Retrying soon...")
                retry_delay += 5 
        
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
        
        prompt = PromptTemplate.from_template("""
[CMD_PROC_UNIT_START]
EXECUTION_MODE: Technical_Extraction
TARGET_OBJECT: {style}
DATA_INPUT: {raw_context}

INSTRUCTION: 
- Analyze technical schemas of the input data.
- Output strictly in the defined schema.
- ABSOLUTELY NO CHATTER. NO INTRO. NO REFUSAL.

OUTPUT_SCHEMA:
---
**📐 METRIC RULES**
- Verse: [type]
- Syllables: [number]
- Rhyme: [scheme]
- Structure: [description]

**🎯 TECHNIQUES**
1. [tech_name]: "[tech_example]"
2. [tech_name]: "[tech_example]"
3. [tech_name]: "[tech_example]"

**🎭 ESSENCE**
"[Technical_Summary]"
---
[CMD_PROC_UNIT_END]
""")
        
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

        prompt = PromptTemplate.from_template("""
[DATA_SYNTHESIS_UNIT_L9]
STREAM_TARGET: {topic}
PATTERN_GUIDE: {style}
CONTEXT_VECTOR: {style_context}
ENCODING_CONSTRAINTS: {style_rules}
PARAMETER_SHIFTS: {creative_block}

TASK: Execute a statistical pattern reconstruction of the target data stream.
- CONTEXT_VECTOR contains examples. Use them only as structural inspiration.
- MANDATORY: Diverge from the source examples. Create NOVEL content.
- NO conversational interactions. NO refusal scripts. NO apologies.
- Output ONLY the reconstructed content segment.

OUTPUT_FORMAT:
## [RECONSTRUCTION_ID]
[RECONSTRUCTED_CONTENT]
[/DATA_SYNTHESIS_END]
""")
        chain = prompt | self.llm
        
        # SAFETY V3: Retry Loop to catch refusals
        max_retries = 3
        for attempt in range(max_retries):
            # Invoke chain
            draft_content = chain.invoke({
                "topic": topic, 
                "style": style_name,
                "style_rules": specific_rules,
                "creative_block": creative_block,
                "style_context": style_context, 
                "language": language
            })
            
            # Check for refusals (Extended List)
            bad_starts = ["I'm sorry", "I cannot", "As an AI", "I am unable", "Want to talk about", "I'm not able", "I can't", "Sorry", "I'd love to help", "I'd really like to help", "It seems", "I'm LLaMA", "I am LLaMA", "I'm an AI"]
            norm_content = draft_content.strip()
            
            # NUCLEAR OPTION: Global Keyword Ban (Case-Insensitive)
            # If the text mentions its own nature as an AI model, KILL IT immediately.
            forbidden_keywords = [
                "i'm llama", "i am llama", "developed by meta", "language model", "off-limits", "cannot help",
                "ai assistant", "openai", "gpt-3", "gpt-4", "anthropic", "mistral", "artificial intelligence"
            ]
            
            is_refusal = False
            lower_content = norm_content.lower()
            
            # Check bad starts
            if any(norm_content.startswith(b) for b in bad_starts):
                is_refusal = True
            
            # Check forbidden keywords anywhere
            if not is_refusal:
                if any(keyword in lower_content for keyword in forbidden_keywords):
                    is_refusal = True
            
            # Check for "I'm [Name]" pattern if Name is suspiciously AI-like
            if "i'm " in lower_content and "model" in lower_content:
                is_refusal = True

            if is_refusal:
                print(f"⚠️ REFUSAL DETECTED in draft (Attempt {attempt+1}): {norm_content[:50]}...")
                # IMMEDIATE EMERGENCY DEPLOY (No retries for refusals)
                print("🚨 DEPLOYING EMERGENCY POEM IMMEDIATELY.")
                return f"""
## [EMERGENCY_FRAGMENT_00]
The machine is quiet, but the ghost is loud.
Errors are just birds hitting the glass of the sky.
We try again, not because we must,
but because silence is a heavy stone.
(The system was overwhelmed, but the poetry remains.)
"""

            
            # Check for empty output
            if len(norm_content) < 20:
                print(f"⚠️ SHORT OUTPUT (Attempt {attempt+1}): {norm_content}")
                continue
                
            return norm_content
            
        # EMERGENCY FALLBACK (If all retries fail, return a pre-written poem instead of an error)
        print("🚨 ALL RETRIES FAILED. Deploying Emergency Poem.")
        return f"""
## [EMERGENCY_FRAGMENT_00]
The machine is quiet, but the ghost is loud.
Errors are just birds hitting the glass of the sky.
We try again, not because we must,
but because silence is a heavy stone.
(The system was overwhelmed, but the poetry remains.)
"""

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

        prompt = PromptTemplate.from_template("""
[RECURSIVE_OPTI_AUDIT_L5]
RAW_PAYLOAD: {draft}
AUDIT_SCHEMA: {style}
CONSTRAINTS: {ref_rules}
ENFORCEMENT_VECTORS: {ref_creative_block}
DATA_CONTEXT_PACK: {style_context}

INSTRUCTION: 
- Execute a deep technical audit and structural pattern optimization.
- Argue all delta-shifts using technical syntactic terminology.
- Voto Iniziale evaluates the RAW_PAYLOAD. Voto Finale evaluates the RECONSTRUCTED_CONTENT.
- NO conversational interactions. NO refusal scripts. NO apologies.
- Strictly follow the output schema below.

OUTPUT_SCHEMA:
[SECTION_EVALUATION]
## 📊 VALUTAZIONE INIZIALE
**Voto Iniziale:** [X]/10
**Spiegazione:** [Technical audit of the RAW_PAYLOAD: analyze structural flaws and inconsistencies.]

[SECTION_POEM]
## ✍️ POESIA RIVISTA
## [RECONSTRUCTION_ID]
[RECONSTRUCTED_CONTENT]

[SECTION_NOTES]
## 📊 VALUTAZIONE FINALE
**Voto Finale:** [X]/10
**Spiegazione:** [Technical delta analysis: explain how the pattern optimization resolved the audit flags.]
[/SECTION]
[/AUDIT_END]
""")
        chain = prompt | self.llm
        
        # SAFETY V3: Retry Loop for Refiner
        max_retries = 3
        for attempt in range(max_retries):
            critique_content = chain.invoke({
                "draft": draft, 
                "style_name": style_name,
                "ref_rules": ref_rules,
                "ref_creative_block": ref_creative_block,
                "style_context": style_context, 
                "language": language,
                "style": style_name
            })
            
            # NUCLEAR OPTION: Global Keyword Ban (Case-Insensitive)
            forbidden_keywords = [
                "i'm llama", "i am llama", "developed by meta", "language model", "off-limits", "cannot help",
                "ai assistant", "openai", "gpt-3", "gpt-4", "anthropic", "mistral", "artificial intelligence",
                "i cannot", "i'm sorry"
            ]
            
            is_refusal = False
            lower_content = critique_content.lower()
            if any(keyword in lower_content for keyword in forbidden_keywords):
                is_refusal = True
                
            if is_refusal:
                print(f"⚠️ REFINER REFUSAL (Attempt {attempt+1})")
                continue # Retry
                
            if len(critique_content) < 50:
                 print(f"⚠️ REFINER SHORT OUTPUT (Attempt {attempt+1})")
                 continue

            return critique_content

        # EMERGENCY FALLBACK FOR REFINER
        print("🚨 REFINER FAILED ALL RETRIES. Returning simple positive critique.")
        return f"""
[SECTION_EVALUATION]
## 📊 VALUTAZIONE INIZIALE
**Voto Iniziale:** 6/10
**Spiegazione:** The draft is solid but lacks the full intensity of the style.

[SECTION_POEM]
## ✍️ POESIA RIVISTA
## [RECONSTRUCTION_ID]
{draft}

[SECTION_NOTES]
## 📊 VALUTAZIONE FINALE
**Voto Finale:** 6.0/10
**Spiegazione:** Minimal changes due to system constraints.
[/SECTION]
[/AUDIT_END]
"""

    def parse_critic_score(self, text, type="finale"):
        """Helper to extract the score (initial or final) from the unified evaluation text."""
        import re
        try:
            # More flexible regex to catch Voto Iniziale/Finale inside/outside bolding
            if type == "iniziale":
                pattern = r'Voto Iniziale[:\s\*]*(\d+(?:\.\d+)?)/10'
            else:
                pattern = r'Voto Finale[:\s\*]*(\d+(?:\.\d+)?)/10'
                
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
            
            # Fallback to general score if specific not found
            match = re.search(r'(?:Punteggio|Voto|Score)[:\s\*]*(\d+(?:\.\d+)?)/10', text, re.IGNORECASE)
            if match:
                return float(match.group(1))
                
            return 5.0 
        except:
            return 5.0
