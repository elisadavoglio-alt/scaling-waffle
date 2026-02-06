# 🚀 Deployment Guide: Poetry Agent Studio

## 1. GitHub Setup

We have already initialized Git and made the first commit locally. Now you just need to connect it to your GitHub account.

1. **Create a Repo**: Go to GitHub and create a new repository named `poetry-agent-studio` (Public or Private).
2. **Link and Push**: Open your terminal in the project folder and run:

   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/poetry-agent-studio.git
   git branch -M main
   git push -u origin main
   ```

## 2. Streamlit Cloud Deployment

1. **Connect**: Go to [share.streamlit.io](https://share.streamlit.io/) and click **"Create app"**.
2. **Select Repo**: Choose your `poetry-agent-studio` repository.
3. **Settings**:
   - **Main file path**: `app.py`
4. **Secrets (CRITICAL)**: Click on **"Advanced settings..."** before deploying. Copy and paste the following into the **Secrets** box:

```toml
FREELLM_API_KEY = "YOUR_FREE_LLM_KEY"
GROQ_API_KEY = "YOUR_GROQ_KEY"
TAVILY_API_KEY = "YOUR_TAVILY_KEY"
LANGCHAIN_API_KEY = "YOUR_LANGCHAIN_KEY"
LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_PROJECT = "Poetry_Studio"
```

1. Click **Deploy**! 🎈

## What happens next?

- The app will spin up.
- It will see that `chroma_db` is missing.
- It will automatically read the `knowledge_base/` folder and rebuild the vectors (this takes about 30-60 seconds on the first run).
- Palimpsest is then live for the world!
