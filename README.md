# 📄 AI Resume Analyzer

An AI-powered web app that compares your resume against a job description and gives you an instant match score, skill gap breakdown, and concrete suggestions to improve your resume — powered by Groq's free LLM API.

## Features

- Upload your resume as PDF, DOCX, or TXT
- Paste in any job description
- Get an AI-generated match score (0–100)
- See matched skills vs. missing skills
- Get a breakdown of your strengths and gaps
- Receive concrete, actionable suggestions to improve your resume for that specific role

## Tech Stack

- **Frontend/UI:** Streamlit
- **Text extraction:** pdfplumber (PDF), python-docx (DOCX)
- **AI analysis:** Groq API running `openai/gpt-oss-120b`
- **Language:** Python

## How It Works

1. The app extracts raw text from your uploaded resume file
2. That text, along with the job description, is sent to an LLM via the Groq API with a structured prompt
3. The model returns a JSON response containing the match score, matched/missing skills, strengths, gaps, and improvement suggestions
4. Streamlit renders the results in a clean, readable layout

## Getting a Free Groq API Key

Sign up at [console.groq.com/keys](https://console.groq.com/keys) — no credit card required. The free tier is sufficient for personal projects and demos.

---

## Option 1: Run Locally

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ai-resume-analyzer.git
cd ai-resume-analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key as an environment variable

```bash
export GROQ_API_KEY="your-key-here"   # macOS/Linux
set GROQ_API_KEY="your-key-here"      # Windows (cmd)
```

### 4. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Option 2: Run in Google Colab (via ngrok)

A ready-to-use notebook (`AI_Resume_Analyzer_ngrok_Colab.ipynb`) is included that runs the same app inside Google Colab and exposes it via a public URL — no local installation required.

1. Open the notebook in Colab
2. Run the install cell
3. Enter your Groq API key when prompted (kept private via `getpass`)
4. Enter a free [ngrok authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) when prompted
5. Run the launch cell — it prints a public `https://....ngrok-free.app` link
6. Open the link and use the app

---

## Option 3: Deploy on Streamlit Community Cloud (permanent link)

For a stable, shareable link (great for a resume/portfolio):

1. Push this repo to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud) and connect your repo
3. Add `GROQ_API_KEY` as a secret in the app's settings
4. Deploy — you'll get a permanent `https://yourapp.streamlit.app` URL

---

## Usage

1. Upload your resume (PDF, DOCX, or TXT)
2. Paste the job description into the text box
3. Click **Analyze Match**
4. Review your match score, skill gaps, and suggestions

## Notes

- Your API key is never hardcoded or stored — it's read from an environment variable at runtime.
- Model used: `openai/gpt-oss-120b` (Groq's recommended model, replacing the deprecated Llama 3.3 70B).

## Possible Extensions

- Support uploading multiple resumes and rank them against one job description
- Cache analysis results to avoid repeated API calls
- Add a classic NLP fallback (spaCy + embeddings) for offline/no-API-cost matching

## Demo 
<img width="943" height="500" alt="Screenshot 2026-11-16 041411" src="https://github.com/user-attachments/assets/e5025f55-7662-4245-b99b-93cb0f78fcfb" />
Streamlit link - https://elixir-composite-waviness.ngrok-free.dev/

