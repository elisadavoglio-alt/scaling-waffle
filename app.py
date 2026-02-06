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

    # History
    st.divider()
    with st.expander("📜 History"):
        if 'history' in st.session_state and st.session_state['history']:
            for i, item in enumerate(reversed(st.session_state['history'])):
                st.text(f"{item['timestamp']} - {item['style']}")
        else:
            st.caption("No poetry generated yet.")

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
        st.success("Style context retrieved!")
        status.update(label="✅ Research Complete", state="complete", expanded=False)
    
    # 3. THE WRITER'S ROOM (4 Columns)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("#### 📚 Sources")
        st.caption("RAG Context")
        # FIX: Replaced st.code with styled div for text wrapping
        st.markdown(f"""
        <div style='background-color: #2b2b2b; padding: 15px; border-radius: 8px; border: 1px solid #444; color: #ccc; font-family: "Space Mono", monospace; font-size: 0.85em;'>
            <p><strong>🏛️ ARCHIVE ACCESSED</strong></p>
            <p>Retrieved structural blueprints for: <span style='color: #4CAF50;'>{style_choice}</span>.</p>
            <hr style='border: 0; border-top: 1px dashed #555; margin: 10px 0;'>
            <p style='font-style: italic;'>Metric rules, vocabulary, and rhetorical strategies have been injected into the Generator's active context.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🔍 View Raw Analysis (Debug)"):
             st.text(style_context)

    # --- STEP 2: DRAFT ---
    with col2:
        st.markdown("#### ✍️ Poet")
        with st.status("✍️ Drafting Verses...", expanded=True) as status:
            draft = agent.write_draft(topic, style_context, style_choice, lang_code, adherence, originality, complexity)
            # Use styled div instead of st.code to allow wrapping
            # FIX: replace newlines with <br> and add scroll
            st.markdown(f"""
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ddd; font-family: 'Roboto Mono', monospace; font-size: 0.9rem; white-space: pre-wrap; color: #333; max-height: 500px; min-height: 200px; overflow-y: auto;">
                {draft.replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)
            status.update(label="Draft Written", state="complete", expanded=True)

    # --- STEP 3: CRITIQUE ---
    with col3:
        st.markdown("#### 🎭 Critic")
        with st.status("🧐 Analyzing Metrics...", expanded=True) as status:
            critique = agent.critique_poem(draft, style_context, lang_code)
            st.markdown(f"""
             <div style="max-height: 500px; min-height: 200px; overflow-y: auto; font-size: 0.9rem;">
                <b>Feedback:</b><br>{critique.replace(chr(10), "<br>")}
             </div>
             """, unsafe_allow_html=True)
            status.update(label="Critique Recorded", state="complete", expanded=True)

    with col4:
        st.markdown("#### 🔮 Interpreter")
        with st.status("🔮 Analyzing (Pre-Refinement)...", expanded=True) as status:
            draft_analysis = agent.interpret_poem(draft, lang_code)
            st.markdown(f"""
            <div style="font-size: 0.8rem; height: 300px; overflow-y: auto; background-color: {theme['card_bg']}; padding: 10px; border-radius: 5px;">
                {draft_analysis.replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)
            status.update(label="Analysis Ready", state="complete", expanded=False)

    # 4. REFINER (Skip divider edit to keep context simple)
    # ...
    
    # 5. INTERPRETER Update
    # ...
    # We update the container height in the later block too, but replacing file content here focuses on the main columns.


    # 4. REFINEMENT LOOP (The Crucible)
    st.divider()
    st.markdown("### 🔄 Refinement Loop")
    
    current_poem = draft
    current_critique = critique
    iteration = 0
    max_iterations = 3
    final_score = 0.0

    # Parse initial score
    final_score = agent.parse_critic_score(current_critique)
    
    col_ref_1, col_ref_2 = st.columns([1, 3])
    with col_ref_1:
        st.caption("Initial Critique Score")
        st.metric(label="Score", value=f"{final_score}/10")
        
    with col_ref_2:
        loop_container = st.container()
        
        while final_score < 9.0 and iteration < max_iterations:
             iteration += 1
             with loop_container.expander(f"🔄 Iteration {iteration} (Score: {final_score}/10)", expanded=True):
                 st.write(f"**Attempting improvement...** (The Critic is asking for > 9.0)")
                 
                 # A. INTERPRET (Deep Analysis)
                 with st.spinner("🔮 Interpreter analyzing deep structure..."):
                      interpretation = agent.interpret_poem(current_poem, lang_code)
                 
                 # B. REFINE (Fixing specific issues)
                 with st.spinner("🛠️ Refiner applying fixes..."):
                      revised_poem_pack = agent.refine_poem(current_poem, current_critique, interpretation, style_context, lang_code)
                      
                      # Extract just the poem text from the complex output? 
                      # The Refiner outputs: [TITLE]\n[POEM]\n\nMETRIC TABLE...
                      # We need to render the whole pack for the user to see the Changelog, 
                      # BUT pass only the text to the Critic?
                      # For simplicity, let's treat the whole output as the "current_poem" for display,
                      # but we might need to be careful if the Critic gets confused by the table.
                      # Let's assume the Critic is smart enough or we leave it as is.
                      current_poem = revised_poem_pack # Contains Table + Changelog
                 
                 # C. CRITIQUE (Re-Evaluation)
                 with st.spinner("🧐 Critiquing revision..."):
                      current_critique = agent.critique_poem(current_poem, style_context, lang_code)
                      final_score = agent.parse_critic_score(current_critique)
                 
                 st.markdown(f"**New Score:** {final_score}/10")
                 st.markdown(f"**Critique:** {current_critique}")
        
        if final_score >= 8.0:
            st.success(f"✨ Excellence Achieved! High Score: {final_score}/10")
        else:
            st.warning(f"⚠️ Max iterations reached. Best Score: {final_score}/10")

        final_poem = current_poem # Setup (table included)
    
    # 5. INTERPRETER (Post-Generation Analysis)

    # 5. INTERPRETER (Post-Generation Analysis)
    # 5. INTERPRETER (Post-Generation Analysis)
    # 5. INTERPRETER (Post-Generation Analysis)
    with col4:
         st.divider()
         st.markdown("#### 🏁 Final Analysis")
         
         # Upgrade: Use st.status instead of spinner for persistent visibility
         with st.status("🔮 Analyzing Final Result...", expanded=True) as status:
            interpretation = agent.interpret_poem(final_poem, lang_code)
            status.update(label="✅ Analysis Complete", state="complete", expanded=True)
         
         # Show snippet in the column
         with st.container(height=200):
            st.caption(interpretation[:150] + "...")

    # 6. FINAL WORK
    st.markdown("---") 
    st.markdown("## 💎 The Final Work")
    
    # Styled Card with Scrollbar fix
    st.markdown(f"""
    <div class="poem-card" style="max-height: 600px; min-height: 200px; overflow-y: auto;">
        {final_poem.replace(chr(10), "<br>")}
    </div>
    """, unsafe_allow_html=True)

    # 7. PARSING ANALYSIS DATA
    # Helper to parse the pseudo-JSON from Interpreter
    def parse_analysis(text):
        data = {}
        for line in text.split('\n'):
            if ": " in line:
                key, val = line.split(": ", 1)
                data[key.strip()] = val.strip()
        return data

    analysis_data = parse_analysis(interpretation)
    
    # 8. FOOTER ACTIONS (Enhanced Tabs)
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis", "📚 Sources", "🔄 Versions", "📤 Export"])
    
    with tab1:
        # --- 📊 ANALISI TECNICA ---
        col_metrics, col_scores = st.columns([2, 1])
        
        with col_metrics:
            st.markdown("#### 📏 Metrica & Struttura")
            # Default values to avoid errors if parsing fails
            scheme = analysis_data.get("SCHEME", "Libero")
            metrics_val = analysis_data.get("METRICS", "Variabile")
            devices = analysis_data.get("DEVICES", "N/A")
            
            st.code(f"""
Schema:  {scheme}
Sillabe: {metrics_val}
Figure:  {devices}
            """, language="yaml")
            
        with col_scores:
            st.markdown("#### 🎯 Performance")
            
            # Adherence Bar
            try:
                adh_score = int(analysis_data.get("RATING_ADHERENCE", "80").replace("%", ""))
            except: adh_score = 80
            st.caption(f"Aderenza Stile ({adh_score}%)")
            st.progress(adh_score / 100)
            
            # Originality Bar
            try:
                orig_score = int(analysis_data.get("RATING_ORIGINALITY", "70").replace("%", ""))
            except: orig_score = 70
            st.caption(f"Originalità ({orig_score}%)")
            st.progress(orig_score / 100, )

        st.info(f"**Interpretazione:** {analysis_data.get('INTERPRETATION', interpretation)}")

    with tab2:
        # --- 📚 FONTI ---
        st.markdown("#### Risonanze & Ispirazioni")
        st.write("Il sistema RAG ha attinto dalle seguenti definizioni stilistiche:")
        with st.expander(f"📖 Corpus: {style_choice}", expanded=True):
            st.caption(style_context[:1000] + " [...]")
            
    with tab3:
        # --- 🔄 PALLINSESTO (VERSIONI) ---
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("**v1 (Bozza Poeta)**")
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; height: 300px; overflow-y: auto; font-size: 0.9rem; white-space: pre-wrap;">
                {draft.replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)
            
        with col_v2:
            st.markdown("**v3 (Finale Refiner)**")
            st.markdown(f"""
            <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; height: 300px; overflow-y: auto; font-size: 0.9rem; white-space: pre-wrap;">
                {final_poem.replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("##### 📝 Note del Critico")
        st.warning(critique)

    with tab4:
        # --- 📤 EXPORT & HISTORY ---
        st.download_button(
            label="💾 Download Text",
            data=f"{final_poem}\n\n---\n{analysis_data.get('INTERPRETATION', '')}\n\nGenerated by Palimpsest AI",
            file_name=f"palimpsest_{style_choice.replace(' ', '_').lower()}.txt",
            mime="text/plain"
        )
        
        # Save to history logic
        # Save to gen_results for persistence
        st.session_state.gen_results = {
            "style_choice": style_choice,
            "style_context": style_context,
            "draft": draft,
            "critique": critique,
            "final_poem": final_poem,
            "interpretation": interpretation,
            "lang_code": lang_code,
            "theme": theme,
            "analysis_data": analysis_data
        }

        # Save to history logic
        st.session_state['history'].append({
            "style": style_choice,
            "text": final_poem,
            "timestamp": time.strftime("%H:%M:%S")
        })
        
        st.success("Salvataggio in Cronologia completato.")

# --- RENDERER (Persistent Stage) ---
if st.session_state.gen_results:
    res = st.session_state.gen_results
    
    # Extract variables for easier use
    style_choice = res['style_choice']
    style_context = res['style_context']
    draft = res['draft']
    critique = res['critique']
    final_poem = res['final_poem']
    interpretation = res['interpretation']
    lang_code = res['lang_code']
    theme = res['theme']
    analysis_data = res['analysis_data']

    # Redraw standard workflow columns (Static indicators)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### 📚 Sources")
        st.markdown(f"""
        <div style='background-color: #2b2b2b; padding: 15px; border-radius: 8px; border: 1px solid #444; color: #ccc; font-family: "Space Mono", monospace; font-size: 0.85em;'>
            <p><strong>🏛️ ARCHIVE ACCESSED</strong></p>
            <p>Retrieved structural blueprints for: <span style='color: #4CAF50;'>{style_choice}</span>.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("#### ✍️ Poet")
        st.success("Draft Persisted")
    with col3:
        st.markdown("#### 🎭 Critic")
        st.success("Evaluation Saved")
    with col4:
        st.markdown("#### 🔮 Interpreter")
        st.success("Analysis Ready")

    st.markdown("---") 
    st.markdown("## 💎 The Final Work")
    
    # Styled Card with Scrollbar fix
    st.markdown(f"""
    <div class="poem-card" style="max-height: 600px; min-height: 200px; overflow-y: auto;">
        {final_poem.replace(chr(10), "<br>")}
    </div>
    """, unsafe_allow_html=True)
    
    # 8. FOOTER ACTIONS (Enhanced Tabs)
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis", "📚 Sources", "🔄 Versions", "📤 Export"])
    
    with tab1:
        col_metrics, col_scores = st.columns([2, 1])
        with col_metrics:
            st.markdown("#### 📏 Metrica & Struttura")
            st.code(f"Schema:  {analysis_data.get('SCHEME', 'Libero')}\nSillabe: {analysis_data.get('METRICS', 'Variabile')}\nFigure:  {analysis_data.get('DEVICES', 'N/A')}", language="yaml")
        with col_scores:
            st.markdown("#### 🎯 Performance")
            try: adh_score = int(analysis_data.get("RATING_ADHERENCE", "80").replace("%", ""))
            except: adh_score = 80
            st.progress(adh_score / 100, text=f"Aderenza ({adh_score}%)")
        st.info(f"**Interpretazione:** {analysis_data.get('INTERPRETATION', interpretation)}")

    with tab2:
        st.markdown("#### Risonanze & Ispirazioni")
        st.write("Il sistema RAG ha attinto dalle seguenti definizioni stilistiche:")
        with st.expander(f"📖 Corpus: {style_choice}", expanded=True):
            st.caption(style_context[:1000] + " [...]")
            
    with tab3:
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("**v1 (Bozza Poeta)**")
            st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; height: 300px; overflow-y: auto; font-size: 0.9rem; white-space: pre-wrap; color: #333;">{draft.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        with col_v2:
            st.markdown("**v3 (Finale Refiner)**")
            st.markdown(f'<div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; height: 300px; overflow-y: auto; font-size: 0.9rem; white-space: pre-wrap; color: #333;">{final_poem.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        st.markdown("##### 📝 Note del Critico")
        st.warning(critique)

    with tab4:
        st.download_button(label="💾 Download Text", data=f"{final_poem}\n\n---\n{analysis_data.get('INTERPRETATION', '')}", file_name="poetry.txt")

    # 9. CREDITS FOOTER
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            Developed by <b>E.D.</b><br>
            Powered by <b>LangChain</b> (RAG) & <b>Llama 3</b> (Groq)
        </div>
        <div style="text-align: center; margin-top: 20px; font-family: 'Brush Script MT', cursive; font-size: 1.2rem; color: #888; opacity: 0.8;">
            🐷 That's all folks!
        </div>
        """, 
        unsafe_allow_html=True
    )


