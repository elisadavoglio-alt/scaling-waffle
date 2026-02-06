# 🚀 Deployment Guide: Palimpsest AI

## 1. Prepare for GitHub

You are about to push your code. We have already created a `.gitignore` to exclude your API keys (`.env`) and the heavy database (`chroma_db`). The database will rebuild itself automatically on the cloud.

### Step 1: Push to GitHub

If you haven't initialized a repository yet:

```bash
cd 06_Poetry_Agent
git init
git add .
git commit -m "Initial commit of Palimpsest AI"
# Link to your new GitHub repo
git remote add origin https://github.com/YOUR_USERNAME/palimpsest-ai.git
git push -u origin main
```

## 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click **New App**.
3. Select your GitHub repository (`palimpsest-ai`).
4. Set **Main file path** to: `app.py` (or `06_Poetry_Agent/app.py` if in a subfolder).
5. **IMPORTANT**: Before clicking Deploy, click **Advanced Settings** (or "Secrets").

### Step 3: Configure Secrets

Streamlit Cloud needs your API keys. Copy the content of your local `.env` file into the Secrets area:

```toml
GROQ_API_KEY = "gsk_..."
TAVILY_API_KEY = "tvly-..."
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_API_KEY = "lsv2_..."
LANGCHAIN_PROJECT = "Poetry_Agent"
```

1. Click **Deploy**! 🎈

## What happens next?

- The app will spin up.
- It will see that `chroma_db` is missing.
- It will automatically read the `knowledge_base/` folder and rebuild the vectors (this takes about 30-60 seconds on the first run).
- Palimpsest is then live for the world!
