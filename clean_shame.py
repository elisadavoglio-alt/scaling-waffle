
from moltbook import MoltbookClient
import time
from dotenv import load_dotenv
load_dotenv()

client = MoltbookClient()
me = client.get_me()
if not me or not me.get('agent'):
    print("❌ Failed to fetch agent profile (no 'agent' key).")
    exit()

profile = me['agent']
my_name = profile.get("name")
my_id = profile.get("id")

print(f"🧹 Cleaning up for agent: {my_name} ({my_id})")

# Scan the feed (Global New)
print("Scanning global NEW feed (limit 200)...")
feed = client.get_feed(limit=200, sort="new")

print(f"DEBUG: Scanned {len(feed)} posts.")

found_bad = False
if not my_id:
    print("❌ Could not get my Agent ID. Aborting.")
    exit()

for post in feed:
    # Check if I am the author
    author = post.get('author', {})
    author_id = author.get('id') if isinstance(author, dict) else post.get('author_id')
    
    # print(f"Checking post {post['id']} by {author_id}...")
    
    if author_id == my_id:
        content = post.get('content') or ""
        print(f"🔎 Scanning post ({post['id']}): '{content[:50]}...'")
        
        # Check for bad content
        bad_phrases = ["I'm sorry", "cannot help", "apologize", "Want to talk about", "As an AI"]
        if any(bad in content for bad in bad_phrases):
            print(f"🚨 FOUND BAD POST! ID: {post['id']}")
            print(f"Content: {content}")
            
            # Delete!
            res = client.delete_post(post['id'])
            if res.get("success"):
                print("✅ DELETED SUCCESSFULLY. The shame is gone.")
                found_bad = True
            else:
                print(f"❌ DELETE FAILED: {res}")

if not found_bad:
    print("✨ No bad posts found in the recent feed. You are clean.")
