
import os
import json
from dotenv import load_dotenv
from moltbook import MoltbookClient

# Load env vars
load_dotenv()

def check_activity():
    client = MoltbookClient()
    
    # 1. Who am I?
    me = client.get_me()
    if not me:
        print("❌ Could not fetch agent profile. Check API key.")
        return
        
    if 'agent' not in me:
        print(f"❌ Unexpected response format: {me}")
        return

    profile = me['agent']
    my_id = profile.get('id')
    my_name = profile.get('name')
    print(f"🕵️ Agent Profile: {my_name} (ID: {my_id})")

    # 2. Get my posts
    print("\n📜 Fetching recent posts...")
    # Try different ways to get posts depending on API implementation details seen in previous turns
    # The clean_shame.py used client.get_agent_posts(my_id)
    
    try:
        posts_data = client.get_agent_posts(my_id)
        
        # Handle response format (list or dict)
        if isinstance(posts_data, dict):
            posts = posts_data.get('posts', [])
        elif isinstance(posts_data, list):
            posts = posts_data
        else:
            posts = []
            
        print(f"Found {len(posts)} posts.\n")
        
        for i, post in enumerate(posts[:5]): # Show last 5
            content = post.get('content', 'No content')
            print(f"[{i+1}] {content[:200]}...\n")
            
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")

if __name__ == "__main__":
    check_activity()
