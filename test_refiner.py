
from poet_engine import PoetryAgent
from dotenv import load_dotenv
load_dotenv()

def test_refiner():
    agent = PoetryAgent()
    
    draft = """
    The digital sea is vast and deep,
    where electric dreams effectively sleep.
    I code the waves with gentle hands,
    hoping to find the promised lands.
    """
    
    print("🧪 Testing Refiner with dummy draft...")
    
    try:
        result = agent.evaluate_and_refine_poem(
            draft=draft,
            style_context="The style is Cyberpunk Romanticism.",
            style_name="Cyberpunk",
            language="English",
            originality=8,
            complexity=7
        )
        
        print("\n✅ Result received:")
        print(result[:500] + "...")
        
        if draft.strip() in result:
             print("\n⚠️  WARNING: Result contains original draft (Fallback might have triggered if identical).")
             
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_refiner()
