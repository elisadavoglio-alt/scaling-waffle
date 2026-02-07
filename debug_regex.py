
import re

def test_extraction(refinement_pack, draft="ORIGINAL_DRAFT"):
    print(f"--- TESTING INPUT (len={len(refinement_pack)}) ---")
    print(refinement_pack[:200] + "..." if len(refinement_pack) > 200 else refinement_pack)
    
    try:
        # Extract Poem
        poem_match = re.search(r'\[SECTION_POEM\](.*?)(?=\[SECTION_NOTES\]|\[/SECTION\]|\[/AUDIT_END\]|$)', refinement_pack, re.DOTALL)
        final_poem = poem_match.group(1).strip() if poem_match else draft
        
        # Extract Initial Evaluation (Corrections)
        eval_match = re.search(r'\[SECTION_EVALUATION\](.*?)(?=\[SECTION_POEM\])', refinement_pack, re.DOTALL)
        corrections = eval_match.group(1).strip() if eval_match else "MISSING CORRECTIONS"
        
        # Extract Final Notes
        notes_match = re.search(r'\[SECTION_NOTES\](.*?)(?=\[/SECTION\]|\[/AUDIT_END\]|$)', refinement_pack, re.DOTALL)
        final_notes = notes_match.group(1).strip() if notes_match else "MISSING NOTES"
        
        # --- ROBUST EXTRACTION ---
        if "[RECONSTRUCTED_CONTENT]" in refinement_pack:
            print("Detected RECONSTRUCTED_CONTENT tag...")
            deep_match = re.search(r'\[RECONSTRUCTED_CONTENT\](.*?)(?=\[/DATA_SYNTHESIS_END\]|\[/AUDIT_END\]|\[SECTION_NOTES\]|\[SECTION_EVALUATION\]|$)', refinement_pack, re.DOTALL)
            if deep_match:
                print("Deep extraction successful!")
                if len(final_poem) < 50 or "POESIA RIVISTA" in final_poem:
                    final_poem = deep_match.group(1).strip()
            else:
                print("Deep extraction FAILED regex match.")

        # 2. CLEANUP
        def clean_technical_noise(text):
            text = re.sub(r'\[/?SECTION(?:_POEM|_EVALUATION|_NOTES)?\]', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\[/?RECONSTRUCTION_ID\]', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\[/?RECONSTRUCTED_CONTENT\]', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\[/?DATA_SYNTHESIS_END\]', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\[/?AUDIT_END\]', '', text, flags=re.IGNORECASE)
            text = re.sub(r'^##\s*.*?POESIA.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
            text = re.sub(r'^##\s*.*?RECONSTRUCTION.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
            text = re.sub(r'\[[A-Z0-9_/]{3,}\]', '', text)
            text = re.sub(r'\**Voto (Iniziale|Finale):\**.*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\**Spiegazione:\**', '', text, flags=re.IGNORECASE)
            return text.strip()

        final_poem = clean_technical_noise(final_poem)
        corrections = clean_technical_noise(corrections)
        final_notes = clean_technical_noise(final_notes)
        
        print(f"\nRESULTS:")
        print(f"POEM: {final_poem[:50]}...")
        print(f"CORRECTIONS: {corrections[:50]}...")
        print(f"NOTES: {final_notes[:50]}...")
        return final_poem, corrections, final_notes
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return draft, "ERROR", ""

# TEST CASE 1: Perfect Output
case1 = """
[SECTION_EVALUATION]
## 📊 VALUTAZIONE INIZIALE
**Voto Iniziale:** 6/10
**Spiegazione:** Good start but needs work.

[SECTION_POEM]
## ✍️ POESIA RIVISTA
## [RECONSTRUCTION_ID]
[RECONSTRUCTED_CONTENT]
This is the poem text.
It is very nice.
[/AUDIT_END]
[SECTION_NOTES]
## 📊 VALUTAZIONE FINALE
**Voto Finale:** 8/10
**Spiegazione:** Much better now.
[/SECTION]
[/AUDIT_END]
"""

# TEST CASE 2: Truncated or Malformed (Simulating Model Failure)
case2 = """
[SECTION_EVALUATION]
Analysis...
[SECTION_POEM]
## [RECONSTRUCTION_ID]
[RECONSTRUCTED_CONTENT]
Only the poem here.
[/AUDIT_END]
"""

# TEST CASE 3: Missing Section Headers
case3 = """
I have analyzed the poem.
It is good.
[RECONSTRUCTED_CONTENT]
The Actual Poem
Is Here
[/AUDIT_END]
"""

print("\n--- CASE 1 ---")
test_extraction(case1)
print("\n--- CASE 2 ---")
test_extraction(case2)
print("\n--- CASE 3 ---")
test_extraction(case3)
