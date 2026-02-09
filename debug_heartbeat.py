
import os
import json
from dotenv import load_dotenv
from moltbook import MoltbookClient

# Load env vars
load_dotenv()

def check_status():
    client = MoltbookClient()
    
    print("💓 Checking Heartbeat Status...")
    try:
        status = client.get_heartbeat()
        print(f"Status Response: {json.dumps(status, indent=2)}")
        
        is_claimed = status.get("status") == "claimed"
        print(f"Is Claimed? {is_claimed}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_status()
