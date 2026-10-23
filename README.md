# 📖 VocabCraft — AI Vocabulary Builder

> An intelligent, interactive vocabulary-learning companion powered by **Python**, **Streamlit**, and the **Google Gemini API** (`google-genai` SDK).

![VocabCraft Banner](https://img.shields.io/badge/Streamlit-1.49-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
---

## ✨ Features

- 🔍 **Instant Vocabulary Exploration**: Enter any English word to generate:
  - **Simple Definition**: Plain-English, beginner-friendly explanation.
  - **Part of Speech & Phonetics**: Grammatical classification and IPA pronunciation guide.
  - **3 Synonyms & 3 Antonyms**: Curated semantic opposites and parallels presented in color-coded pills.
  - **2 Real-World Example Sentences**: Natural contexts demonstrating practical usage.
  - **Memory Hook / Mnemonic**: Catchy mental associations and retention tips to remember words long-term.
- 🎯 **Interactive 3-Question Mastery Quiz**:
  - Automatically generated multiple-choice quiz covering word definition, synonyms/antonyms, and contextual usage.
  - Instant scoring with percentage badge and motivational feedback.
  - Complete post-quiz review displaying your answer, the correct answer, and pedagogical explanations.
- 🟢 **Dual Operation Mode**:
  - **Live AI Mode**: Generates fresh, custom vocabulary breakdowns for *any* English word using Google's modern `gemini-2.5-flash` model.
  - **Curated Demo Mode**: Runs offline without an API key using 8 rich sample words (*Serendipity*, *Resilient*, *Ephemeral*, *Eloquent*, *Pragmatic*, *Luminous*, *Tenacious*, *Ubiquitous*).
- 🔒 **Secure API Key Handling**:
  - Zero hardcoding of credentials.
  - Reads keys securely from Streamlit secrets, environment variables, or a masked sidebar input.
- 🎨 **Modern, Responsive UI**:
  - Sleek dark theme with modern typography (Outfit & Inter), cards, badges, and responsive columns.

---

## 🛠️ Tech Stack

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **LLM SDK**: Official [google-genai](https://github.com/googleapis/python-genai) SDK (`from google import genai`)
- **Model**: `gemini-2.5-flash` (with `gemini-1.5-flash` option)
- **Data Validation & Typing**: [Pydantic v2](https://docs.pydantic.dev/)

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/VocabCraft.git
cd VocabCraft
```

### 2. Create and Activate a Virtual Environment
**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Configure Gemini API Key
You can run the app immediately in **Demo Mode** without an API key!

To enable **Live AI Mode**, obtain a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey) and configure it using any of these 3 methods:

#### Method A: Streamlit Secrets (Recommended for local dev)
Create a `.streamlit/secrets.toml` file (copied from `.streamlit/secrets.toml.example`):
```toml
GEMINI_API_KEY = "your-actual-gemini-api-key"
```

#### Method B: Environment Variable
```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="your-actual-gemini-api-key"

# Linux / macOS
export GEMINI_API_KEY="your-actual-gemini-api-key"
```

#### Method C: Sidebar Input
You can paste your API key directly into the password-masked field in the app's sidebar.

### 5. Launch the Application
```bash
python -m streamlit run app.py
# or: streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ Deployment to Streamlit Community Cloud

Deploying VocabCraft is 100% free and takes under 2 minutes:

1. **Push your code to GitHub** (see instructions below).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New app"** (or **"Create app"**).
4. Select your **Repository** (`YOUR_USERNAME/VocabCraft`), **Branch** (`main`), and set **Main file path** to `app.py`.
5. Under **"Advanced settings"** -> **"Secrets"**, add your Gemini API key:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   ```
6. Click **"Deploy!"**. Your app will be live with a public URL!

---

## 📦 Pushing to a New GitHub Repository

Run these exact commands in your terminal from the `VocabCraft` directory:

```bash
# 1. Initialize Git repository (if not already done)
git init

# 2. Stage all project files (safe .gitignore prevents committing secrets)
git add .

# 3. Commit the initial release
git commit -m "Initial commit: VocabCraft AI Vocabulary Builder"

# 4. Rename default branch to main
git branch -M main

# 5. Link to your new GitHub repository (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/VocabCraft.git

# 6. Push to GitHub
git push -u origin main
```

---

## 📂 Project Structure

```text
VocabCraft/
├── .streamlit/
│   └── secrets.toml.example    # Safe secrets template
├── app.py                      # Main Streamlit application & logic
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── .gitignore                  # Git ignore rules (secrets, venv, cache)
```

---

## 🛡️ Error Handling & Reliability

- **Input Sanitization**: Protects against non-alphabetical characters, oversized inputs, and sentences.
- **Quota & API Errors**: Catches rate-limits (HTTP 429) and invalid API keys (HTTP 401/403) with clear user feedback.
- **Strict Schema Enforcement**: Uses Pydantic schemas with `google-genai` structured outputs (`response_mime_type="application/json"`).
- **Graceful Fallback**: If offline or unauthenticated, clearly signals Demo Mode with 8 rich offline words without spoofing AI generation.

---
