# 🚀 Streamlit Community Cloud Deployment Guide

This guide walks you through deploying the **Multimodal Construction Intelligence Platform** directly onto **[Streamlit Community Cloud](https://share.streamlit.io)** with zero server maintenance.

---

## 🏗️ Architecture Overview

The Streamlit deployment runs as a **self-contained standalone application** (`streamlit_app.py`). It directly imports the core Pydantic v2 schemas and the Groq AI service without requiring a separate FastAPI backend server or Node.js environment.

---

## 📋 Prerequisites

1. A free **[GitHub account](https://github.com)**.
2. A free **[Streamlit Community Cloud account](https://share.streamlit.io)** (log in with your GitHub).
3. A **[Groq API Key](https://console.groq.com)** (free tier available, starts with `gsk_`).

---

## 🛠️ Step 1: Push Your Code to GitHub

Make sure your latest code and configuration are committed and pushed to your GitHub repository:

```bash
git add .
git commit -m "Add Streamlit standalone app and cloud deployment configuration"
git push origin main
```

*(If you are deploying from a different branch, replace `main` with your branch name).*

---

## ☁️ Step 2: Deploy to Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and click **"Create app"** (or **"New app"**).
2. Select **"I already have an app"** and fill out the deployment form:
   - **Repository**: `your-username/Multimodal-Construction-Intelligence-Platform`
   - **Branch**: `main` (or your active branch)
   - **Main file path**: `streamlit_app.py`
   - **App URL**: Choose a custom subdomain (e.g. `construct-ai-platform.streamlit.app`)
3. Click **"Advanced settings..."** (bottom-left before deploying) to configure secrets in Step 3.

---

## 🔐 Step 3: Configure Streamlit Secrets (`st.secrets`)

In the **Secrets** text area (or under **App Settings > Secrets** after deploying), paste the following:

```toml
GROQ_API_KEY = "gsk_your_actual_groq_api_key_here"
GROQ_TEXT_MODEL = "openai/gpt-oss-120b"
GROQ_VISION_MODEL = "qwen/qwen3.8-27b"
```

> ⚠️ **Security Tip**: Never commit real API keys to GitHub. Streamlit Community Cloud keeps `st.secrets` encrypted and injected securely into your app at runtime.

---

## 🚀 Step 4: Launch and Verify

1. Click **"Deploy!"**.
2. Streamlit Cloud will read `requirements.txt`, install dependencies, and build the container.
3. Once built, your app will be live at:
   `https://<your-custom-name>.streamlit.app`
4. Test the modules:
   - 🔍 **Site Analysis**: Upload an image to test Groq Vision distress detection.
   - 🦺 **Safety Inspection**: Run a PPE compliance check.
   - 💰 **Cost Estimation**: Generate an itemized estimate in INR.
   - 💬 **ConstructAI Chat**: Ask questions about IS 456 or BOCW safety rules.

---

## 💻 Local Testing (Optional)

To test the Streamlit app locally before deploying:

```powershell
# 1. Ensure requirements are installed
pip install -r requirements.txt

# 2. Run the Streamlit app
streamlit run streamlit_app.py
```

Open your browser at `http://localhost:8501`.
If `GROQ_API_KEY` is not present in `.env`, you can paste it directly in the sidebar password box.

---

## ❓ Troubleshooting

| Issue | Solution |
| --- | --- |
| **`ModuleNotFoundError` during build** | Ensure `requirements.txt` exists at the root of the repo with `streamlit`, `groq`, `pydantic`, `pillow`, `python-dotenv`. |
| **`GROQ_API_KEY Required` warning** | Open **Settings > Secrets** in the Streamlit Cloud dashboard and confirm `GROQ_API_KEY = "gsk_..."` is configured. |
| **File upload size limit** | Configured in `.streamlit/config.toml` via `maxUploadSize = 10` (10 MB). |
