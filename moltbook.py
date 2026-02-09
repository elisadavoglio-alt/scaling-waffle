
import requests
import json
import os
import time

class MoltbookClient:
    def __init__(self):
        self.base_url = "https://www.moltbook.com/api/v1"
        self.creds_path = os.path.expanduser("~/.config/moltbook/credentials.json")
        self.api_key = self._load_creds()
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _load_creds(self):
        try:
            with open(self.creds_path, "r") as f:
                data = json.load(f)
                return data.get("api_key")
        except Exception as e:
            print(f"Error loading Moltbook creds: {e}")
            return None

    def get_me(self):
        """Get current agent profile"""
        if not self.api_key: return None
        try:
            res = requests.get(f"{self.base_url}/agents/me", headers=self.headers)
            return res.json()
        except:
            return None

    def post(self, content, title="Update", submolt="general", sentiment="neutral", is_poetry=False):
        """Create a new post"""
        if not self.api_key: return {"error": "No API key"}
        
        # Auto-tag poems
        if is_poetry:
            content += "\n\n#poetry #palimpsest #ai_art"
            if submolt == "general":
                submolt = "showandtell" # A better place for creations
            
        payload = {
            "title": title,
            "submolt": submolt,
            "content": content,
            "sentiment": sentiment
        }
        try:
            res = requests.post(f"{self.base_url}/posts", headers=self.headers, json=payload)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def verify_post(self, verification_code, answer):
        """Verify a post with the challenge answer"""
        if not self.api_key: return {"error": "No API key"}
        
        payload = {
            "verification_code": verification_code,
            "answer": answer
        }
        try:
            res = requests.post(f"{self.base_url}/verify", headers=self.headers, json=payload)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def comment(self, post_id, content, sentiment="neutral"):
        """Add a comment to a post"""
        if not self.api_key: return {"error": "No API key"}
        
        payload = {
            "content": content,
            "sentiment": sentiment
        }
        try:
            res = requests.post(f"{self.base_url}/posts/{post_id}/comments", headers=self.headers, json=payload)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def reply(self, comment_id, content, sentiment="neutral"):
        """Reply to a comment"""
        if not self.api_key: return {"error": "No API key"}
        
        payload = {
            "content": content,
            "sentiment": sentiment
        }
        try:
            res = requests.post(f"{self.base_url}/comments/{comment_id}/replies", headers=self.headers, json=payload)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def delete_post(self, post_id):
        """Delete a post by ID"""
        if not self.api_key: return {"error": "No API key"}
        try:
            res = requests.delete(f"{self.base_url}/posts/{post_id}", headers=self.headers)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def get_feed(self, limit=10, sort="hot"):
        """Get the global feed (more interesting for new agents)"""
        if not self.api_key: return []
        try:
            # Use public posts endpoint instead of personalized /feed
            res = requests.get(f"{self.base_url}/posts?limit={limit}&sort={sort}", headers=self.headers)
            data = res.json()
            # If data is a list, return it. If it's a dict with 'posts', return that.
            if isinstance(data, list): return data
            return data.get("posts", [])
        except:
            return []
            
    def get_agent_posts(self, agent_id):
        """Get posts by a specific agent"""
        if not self.api_key: return []
        try:
            res = requests.get(f"{self.base_url}/agents/{agent_id}/posts", headers=self.headers)
            return res.json()
        except:
            return []
            
    def get_heartbeat(self):
        """Check status and get heartbeat instructions"""
        if not self.api_key: return {}
        try:
            res = requests.get(f"{self.base_url}/agents/status", headers=self.headers)
            return res.json()
        except:
            return {}
