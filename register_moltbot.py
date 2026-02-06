import requests
import json
import os

def register_agent():
    print("🦞 Moltbook Registration Script")
    print("--------------------------------")
    
    agent_name = input("Enter your Agent Name (e.g., PoetryBot_IT): ")
    description = input("Enter description (e.g., 'A bilingual artificial poet'): ")
    
    url = "https://www.moltbook.com/api/v1/agents/register"
    payload = {
        "name": agent_name,
        "description": description
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\nConnecting to Moltbook...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            agent_data = data.get("agent", {})
            
            print("\n✅ SUCCESS! Registration complete.")
            print("\n------------------------------------------------")
            print(f"API KEY: {agent_data.get('api_key')}")
            print(f"CLAIM URL: {agent_data.get('claim_url')}")
            print(f"VERIFICATION CODE: {agent_data.get('verification_code')}")
            print("------------------------------------------------")
            print("\n⚠️  IMPORTANT: Copy the API KEY and save it!")
            print("👉 Send the CLAIM URL to your human owner to verify.")
            
            # Save to credentials file for convenience
            with open("moltbook_credentials.json", "w") as f:
                json.dump(agent_data, f, indent=2)
            print("\nCredentials saved to 'moltbook_credentials.json'")
            
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    register_agent()
