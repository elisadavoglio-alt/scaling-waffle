import streamlit as st
import time
from dotenv import load_dotenv
from poet_engine import PoetryAgent

# Setup
st.set_page_config(page_title="Palimpsest | AI Poetry", page_icon="📜", layout="wide")
load_dotenv()

# Initialize Session State
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'gen_results' not in st.session_state:
    st.session_state['gen_results'] = None

# --- HELPER FUNCTIONS ---
def stream_data(text, delay=0.02):
    """Generator for typewriter effect."""
    for char in text:
        yield char
        time.sleep(delay)

# --- GLOBAL CSS ---
st.markdown("""
    <style>
    /* Better Font Targeting (Safe for Icons) */
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

    /* Target User Text Elements ONLY - Avoid generic div/span that breaks icons */
    .stMarkdown, .stButton, .stTextInput, .stTextArea, p, h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Mono', monospace !important;
    }
    
    /* Headers specific styling */
    h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] {
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Specific overrides for poem cards */
    .poem-card {
        font-family: 'Space Mono', monospace !important;
    }

    /* Force Scrollbars */
    ::-webkit-scrollbar {
        -webkit-appearance: none;
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-thumb {
        border-radius: 5px;
        background-color: rgba(0,0,0,.5);
        -webkit-box-shadow: 0 0 1px rgba(255,255,255,.5);
    }
    ::-webkit-scrollbar-track {
        background-color: rgba(0,0,0,0.05);
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DYNAMIC THEME ENGINE ---
# Maps specific words in style to a color palette
def get_theme_colors(style_name):
    style_name = style_name.lower()
    if any(x in style_name for x in ["futurism", "modernism", "language poetry", "neoavanguardia", "neo-avantgarde"]):
        return {"accent": "#00FF9D", "secondary": "#BC13FE", "bg_gradient": "linear-gradient(135deg, #0f0c29, #302b63, #24243e)", "text": "#E0E0E0", "card_bg": "rgba(16, 16, 18, 0.8)"}
    elif any(x in style_name for x in ["romantic", "stilnovo", "petrarch", "barocco", "victorian", "metaphysical"]):
        return {"accent": "#8B4513", "secondary": "#D2691E", "bg_gradient": "linear-gradient(to right, #ece9e6, #ffffff)", "text": "#2C3E50", "card_bg": "rgba(255, 255, 255, 0.9)"}
    elif any(x in style_name for x in ["ermetismo", "hermeticism", "crepuscolarismo", "imagism"]):
        return {"accent": "#4CAF50", "secondary": "#8BC34A", "bg_gradient": "linear-gradient(to top, #e6e9f0 0%, #eef1f5 100%)", "text": "#37474F", "card_bg": "rgba(255, 255, 255, 0.95)"}
    elif any(x in style_name for x in ["scapigliatura", "beat", "slam", "spoken", "confessional", "black arts"]):
        return {"accent": "#D93025", "secondary": "#C62828", "bg_gradient": "linear-gradient(45deg, #fff1eb 0%, #ace0f9 100%)", "text": "#1A1A1A", "card_bg": "rgba(255, 255, 255, 0.9)"}
    else:
        # Default Paper Theme
        return {"accent": "#2C3E50", "secondary": "#34495E", "bg_gradient": "#F9F7F2", "text": "#2C3E50", "card_bg": "#FFFFFF"}

# Title Section
# (Removed to avoid duplication with centered header)

# --- SIDEBAR & CONTROLS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    language = st.radio("Global Language", ["English", "Italiano"], horizontal=True)
    lang_code = "English" if language == "English" else "Italiano"
    
    # --- STYLE TAXONOMY ---
    STYLES_ENG = [
        "Metaphysical Poetry", "Romantic Poetry", "Victorian Poetry", "Modernism",
        "Harlem Renaissance", "Beat Generation", "Confessional Poetry",
        "Black Arts Movement", "Language Poetry", "Spoken Word / Slam"
    ]
    STYLES_ITA = [
        "Stilnovo", "Petrarchismo", "Barocco / Marinismo", "Romanticismo Italiano",
        "Scapigliatura", "Crepuscolarismo", "Decadentismo", "Futurismo", "Ermetismo",
        "Neoavanguardia (Gruppo 63)"
    ]
    
    current_style_list = STYLES_ITA if lang_code == "Italiano" else STYLES_ENG
    
    # Theme Input
    topic_label = "Theme / Argomento" 
    topic_value = "The silence of the sea" if lang_code == "English" else "Il silenzio del mare"
    # FIX: Add dynamic key to force re-render when language changes
    topic = st.text_input(topic_label, value=topic_value, key=f"topic_{lang_code}")
    
    # Style Selector
    # FIX: Add dynamic key to force re-render when language changes
    style_choice = st.selectbox("Poetic Style", current_style_list, key=f"style_{lang_code}")
    
    st.divider()
    
    # Advanced Controls
    st.markdown("### 🎚️ Advanced Controls")
    adherence = st.slider("Adherence (Aderenza)", 1, 10, 8, help="How strictly to follow the style rules.")
    originality = st.slider("Originality (Originalità)", 1, 10, 6, help="Higher values increase creativity (and chaos).")
    complexity = st.slider("Complexity (Complessità)", 1, 10, 7, help="Vocabulary richness and structural density.")


# --- MAIN STAGE ---
# Header
st.empty() # Spacer
# Header
st.empty() # Spacer
st.markdown("<h1 style='text-align: center; letter-spacing: 4px;'>PALIMPSEST</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; opacity: 0.7;'>\"These fragments I have shored against my ruins\" — T.S. Eliot</p>", unsafe_allow_html=True)
# Title Section
# (already handled)

# --- THEME SETUP ---
theme = get_theme_colors(style_choice)

# Generation Button
button_label = "✨ Compose New Masterpiece" if lang_code == "English" else "✨ Componi Nuova Opera"

# Center the button 
_, col_btn, _ = st.columns([1, 2, 1])
if col_btn.button(button_label, type="primary", use_container_width=True):
    
    # 1. Init Agent
    with st.spinner("Initializing Creative Agents..."):
        agent = PoetryAgent()
        # Reset current results to show fresh progress
        st.session_state.gen_results = None

    # 2. RESEARCHER
    with st.status("📚 Researcher working...", expanded=True) as status:
        st.write(f"Searching knowledge base for **{style_choice}**...")
        style_context = agent.research_style(style_choice, lang_code)
        
        if any(refusal in style_context for refusal in ["ERROR", "not able to discuss", "I'm sorry", "I am LLaMA", "happy to chat about other"]):
            st.error(f"Research Issue: {style_context}")
            status.update(label="⚠️ Research Failed", state="error", expanded=True)
            st.stop()
        else:
            st.success("Style context retrieved!")
            status.update(label="✅ Research Complete", state="complete", expanded=False)
    
    # 3. THE WRITER'S ROOM (2 Columns to fill space)
    col_src, col_poet = st.columns([1, 2])
    
    with col_src:
        st.markdown("#### 📚 Sources")
        st.caption("RAG Context")
        st.markdown(f"""
        <div style='background-color: #2b2b2b; padding: 15px; border-radius: 8px; border: 1px solid #444; color: #ccc; font-family: "Space Mono", monospace; font-size: 0.85em;'>
            <p><strong>🏛️ ARCHIVE ACCESSED</strong></p>
            <p>Retrieved structural blueprints for: <span style='color: #4CAF50;'>{style_choice}</span>.</p>
            <hr style='border: 0; border-top: 1px dashed #555; margin: 10px 0;'>
            <p style='font-style: italic;'>Metric rules and rhetorical strategies injected.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🔍 View Raw Analysis (Debug)"):
             st.text(style_context)

    # --- STEP 2: DRAFT ---
    with col_poet:
        st.markdown("#### ✍️ Poet (Bozza Originale)")
        with st.status("✍️ Drafting Verses...", expanded=True) as status:
            draft = agent.write_draft(topic, style_context, style_choice, lang_code, adherence, originality, complexity)
            
            # Ensure draft is a string to avoid AttributeErrors
            if draft is None:
                draft = "[ERROR] Generation failed. Please try again."
            elif not isinstance(draft, str):
                draft = str(draft)
            
            if any(refusal in draft for refusal in ["ERROR", "not able to discuss", "I'm sorry", "I am LLaMA", "happy to chat about other"]):
                st.error(f"Drafting Issue: {draft}")
                status.update(label="⚠️ Drafting Failed", state="error", expanded=True)
                st.stop()
            else:
                # PARSE: Extract content between [RECONSTRUCTED_CONTENT] and [/DATA_SYNTHESIS_END]
                import re
                if "[RECONSTRUCTED_CONTENT]" in draft:
                    match = re.search(r'\[RECONSTRUCTED_CONTENT\](.*?)(?=\[/DATA_SYNTHESIS_END\]|$)', draft, re.DOTALL)
                    if match:
                        draft = match.group(1).strip()
                
                # CLEANUP: Use the same logic as for final_poem (reused locally here)
                def quick_clean(text):
                    text = re.sub(r'\[/?RECONSTRUCTION_ID\]', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'\[/?RECONSTRUCTED_CONTENT\]', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'\[/?DATA_SYNTHESIS_END\]', '', text, flags=re.IGNORECASE)
                    text = re.sub(r'^##\s*.*?RECONSTRUCTION.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
                    text = re.sub(r'\[[A-Z0-9_/]{3,}\]', '', text)
                    return text.strip()

                draft = quick_clean(draft)

                st.markdown(f"""
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ddd; font-family: 'Roboto Mono', monospace; font-size: 0.9rem; white-space: pre-wrap; color: #333; max-height: 400px; min-height: 200px; overflow-y: auto;">
                    {draft.replace(chr(10), "<br>")}
                </div>
                """, unsafe_allow_html=True)
                status.update(label="✅ Initial Draft Ready", state="complete", expanded=False)

    # --- UNIFIED REFINER ---
    st.divider()
    st.markdown("### 🛠️ Unified Refinement (Valutazione & Revisione)")
    
    with st.status("🛠️ Unified Refiner at work...", expanded=True) as status:
        # A. Execute Unified Refinement
        refinement_pack = agent.evaluate_and_refine_poem(draft, style_context, style_choice, lang_code, adherence, originality, complexity)
        
        # Ensure refinement_pack is a string
        if refinement_pack is None:
            refinement_pack = "[ERROR] Refinement failed."
        elif not isinstance(refinement_pack, str):
            refinement_pack = str(refinement_pack)
            
        # B. Parse logic using new [SECTION] tags
        import re
        try:
            # Extract Poem
            poem_match = re.search(r'\[SECTION_POEM\](.*?)(?=\[SECTION_NOTES\]|\[/SECTION\]|\[/AUDIT_END\]|$)', refinement_pack, re.DOTALL)
            final_poem = poem_match.group(1).strip() if poem_match else draft
            
            # Extract Initial Evaluation (Corrections)
            eval_match = re.search(r'\[SECTION_EVALUATION\](.*?)(?=\[SECTION_POEM\])', refinement_pack, re.DOTALL)
            corrections = eval_match.group(1).strip() if eval_match else ""
            
            # Extract Final Notes
            notes_match = re.search(r'\[SECTION_NOTES\](.*?)(?=\[/SECTION\]|\[/AUDIT_END\]|$)', refinement_pack, re.DOTALL)
            final_notes = notes_match.group(1).strip() if notes_match else ""
            
            # --- ROBUST EXTRACTION ---
            # If the sectional extraction failed or returned something suspicious (just a header), try deep extraction
            if "[RECONSTRUCTED_CONTENT]" in refinement_pack:
                deep_match = re.search(r'\[RECONSTRUCTED_CONTENT\](.*?)(?=\[/DATA_SYNTHESIS_END\]|\[/AUDIT_END\]|\[SECTION_NOTES\]|$)', refinement_pack, re.DOTALL)
                if deep_match:
                    # Only override if the current final_poem looks like just a header or empty
                    if len(final_poem) < 50 or "POESIA RIVISTA" in final_poem:
                        final_poem = deep_match.group(1).strip()

            # 2. CLEANUP: Strip all technical noise
            def clean_technical_noise(text):
                # Remove common sectional markers
                text = re.sub(r'\[/?SECTION(?:_POEM|_EVALUATION|_NOTES)?\]', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\[/?RECONSTRUCTION_ID\]', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\[/?RECONSTRUCTED_CONTENT\]', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\[/?DATA_SYNTHESIS_END\]', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\[/?AUDIT_END\]', '', text, flags=re.IGNORECASE)
                # Remove header lines often hallucinated by the model
                text = re.sub(r'^##\s*.*?POESIA.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
                text = re.sub(r'^##\s*.*?RECONSTRUCTION.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
                # Remove anything in brackets that looks technical [XYZ_123]
                text = re.sub(r'\[[A-Z0-9_/]{3,}\]', '', text)
                # Remove redundant score labels
                text = re.sub(r'\**Voto (Iniziale|Finale):\**.*', '', text, flags=re.IGNORECASE)
                text = re.sub(r'\**Spiegazione:\**', '', text, flags=re.IGNORECASE)
                return text.strip()

            final_poem = clean_technical_noise(final_poem)
            corrections = clean_technical_noise(corrections)
            final_notes = clean_technical_noise(final_notes)
            
        except Exception as e:
            final_poem = draft
            corrections = f"Analisi non disponibile. Errore: {str(e)}"
            final_notes = ""
            
        initial_score = agent.parse_critic_score(refinement_pack, type="iniziale")
        final_score = agent.parse_critic_score(refinement_pack, type="finale")
        
        # Restore analysis_data for session state persistence
        analysis_data = {
            "SCHEME": "Style-Aware",
            "METRICS": "Technical",
            "DEVICES": "Integrated",
            "RATING_ADHERENCE": f"{int(final_score*10)}%",
            "INTERPRETATION": "Analysis integrated in refinement."
        }
        
        # C. Persistence and Rerun
        st.session_state.gen_results = {
            "style_choice": style_choice,
            "style_context": style_context,
            "draft": draft,
            "final_poem": final_poem,
            "corrections": corrections,
            "final_notes": final_notes,
            "initial_score": initial_score,
            "final_score": final_score,
            "lang_code": lang_code,
            "theme": theme,
            "analysis_data": analysis_data
        }
        st.session_state['history'].append({"style": style_choice, "text": final_poem, "timestamp": time.strftime("%H:%M:%S")})
        
        status.update(label=f"✅ Revisione Completata", state="complete", expanded=False)
        st.rerun()

# --- RENDERER (Persistent Stage) ---
if st.session_state.gen_results:
    res = st.session_state.gen_results
    # Only render if we're not in the middle of a new generation
    # Streamlit handles this naturally by control flow
    
    # We don't need to re-render everything here because Section 4 already did it
    # But if the page REFRESHES, Section 4 won't run unless the button is clicked.
    # So we show a clean mirror of Section 4.
    
    st.markdown("---")
    # 1. VALUTAZIONE INIZIALE (Audit della Bozza)
    st.markdown(f"#### 📊 Valutazione Iniziale: {res.get('initial_score', 5.0)}/10")
    if res.get('corrections'):
        st.info(res['corrections'])

    # 2. IL NUOVO TESTO (Revised Poem)
    st.markdown("#### 💎 Poesia Rivista")
    st.markdown(f"""<div style="background-color: #f0fff0; padding: 20px; border-radius: 8px; border: 1px solid #c3e6cb; font-family: 'serif'; font-size: 1.2rem; color: #155724; white-space: pre-wrap; margin-bottom: 20px;">{res['final_poem'].replace(chr(10), "<br>")}</div>""", unsafe_allow_html=True)
    
    # 3. VALUTAZIONE FINALE (Revisione Completata)
    st.markdown(f"#### 📊 Valutazione Finale: {res.get('final_score', 5.0)}/10")
    if res.get('final_notes'):
        st.success(res['final_notes'])
    
    st.download_button("💾 Scarica Poesia", res['final_poem'], "poesia.txt", key="dl_btn_persistent")
    
    # 4. INSIGHTS (Comparison, Sources, Metadata)
    st.divider()
    with st.expander("🔍 Approfondimenti (Insights)", expanded=False):
        tab_diff, tab_sources, tab_analysis = st.tabs(["🔄 Confronto Versioni", "📜 Fonti (RAG)", "📊 Dettagli Tecnici"])
        
        with tab_diff:
            st.markdown("### 🔄 Prima vs Dopo")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**BOZZA ORIGINALE (V1)**")
                st.code(res.get('draft', 'N/A'), language=None)
            with col2:
                st.markdown("**POESIA RIVISTA (V2)**")
                st.code(res.get('final_poem', 'N/A'), language=None)
        
        with tab_sources:
            st.markdown("### 📜 Contesto di Stile")
            st.info(res.get('style_context', 'N/A'))
            
        with tab_analysis:
            st.markdown("### 📊 Metadata Generazione")
            st.json(res.get('analysis_data', {}))

# Credits Footer (STRICT)
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: #888; font-size: 0.9rem; font-family: monospace;'>"
            "LangChain | ChromaDB | FreeLLM | HuggingFace Embeddings<br>"
            "<i>that's all folks!</i> 🐷"
            "</div>", unsafe_allow_html=True)
