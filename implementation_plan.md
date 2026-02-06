# Implementation Plan - The AI Poetry Studio 🎭

## Goal

Create a sophisticated, multi-agent AI system capable of crafting high-value poetry.
To ensure quality and depth (not just generic rhymes), we will use **RAG (Retrieval Augmented Generation)**.
The AI won't just "guess" a style; it will study real examples first.

## Why RAG? (The Value Add)

If you ask an AI to write like "Dante Alighieri", it mimics the stereotype.
With RAG, we can feed it specific cantos or analyses of Dante's metric structure. The AI will "read" them before writing, ensuring the output respects the true prosody and tone.

## Architecture: The "Writer's Room"

1. **📚 The Researcher (RAG Agent)**:
    * Searches the local knowledge base (txt/pdf of famous poems) for style references matching the user's request.
2. **✍️ The Poet (Drafting Agent)**:
    * Writes the first draft using the inspiration found by the Researcher.
3. **🧐 The Critic (Review Agent)**:
    * Analyzes the draft against specific metrics (rhyme scheme, meter, emotional impact).
4. **🎨 The Artist (Visual Agent)**:
    * Generates a cover image for the poem using the `generate_image` tool.

## Proposed Changes

### Folder Structure

* `06_Poetry_Agent/`
  * `app.py` (Streamlit Interface)
  * `knowledge_base/` (Files with poems/styles to "study")
  * `poet_engine.py` (The logic class)
  * `requirements.txt`

### Key Features

* **Style Injection**: User selects "Cyberpunk" -> RAG retrieves "Neuromancer" snippets or Cyberpunk poetry examples.
* **Iterative Refinement**: Showing the user the "Critic's feedback" before the final version.

## Next Steps

1. Create the environment.
2. Set up the RAG system (VectorStore).
3. Build the Multi-Agent Loop.

## RAG Knowledge Base Expansion 📚

We will populate `06_Poetry_Agent/knowledge_base/` with structured definitions for 10 distinct styles:

1. Shakespearean Sonnet
2. Cyberpunk Free Verse
3. Romanticism
4. Beat Generation
5. Surrealism
6. Futurism
7. Symbolism
8. Slam Poetry
9. Hermeticism
10. Neo-Avantgarde

Each file will contain the *Patterns*, *Techniques*, and *Key Authors* provided by the user to ground the RAG agent.

## Palimpsest UI Implementation Plan 🎨

### 1. Header & Branding

* **Title**: "PALIMPSEST" (Centered/Spaced letterspacing)

* **Subtitle/Quote**: *"These fragments I have shored against my ruins" — Eliot*
* **Layout**: Clean, minimal, using `st.columns` for centering.

### 2. Advanced Controls (New Input Params) 🎚️

* **Sliders**:
  * `Adherence` (Strictness of RAG context usage)
  * `Originality` (LLM Temperature or "Surprise" prompt instruction)
  * `Complexity` (Vocabulary/Syntax instruction)

* **Backend Update**: `PoetryAgent` methods must accept these new parameters.

### 3. Process Visualization (The "Engine Room") ⚙️

* **Layout**: 4 Columns:
  1. **Researcher**: Shows sources found.
  2. **Poet**: Shows the raw draft.
  3. **Critic**: Shows metrics/feedback.
  4. **Interpreter (New)**: Explains the poem's meaning or choices.

* **Refiner Loop**: A distinct visual block showing the iteration before "Final Work".

### 4. Footer & Actions

* **Tabs**: `[📊 Analysis] [📚 Sources] [🔄 Versions] [📤 Export]`

* **Content**:
  * Analysis: The Interpreter's output.
  * Sources: RAG snippets.
  * Export: The Download button.
