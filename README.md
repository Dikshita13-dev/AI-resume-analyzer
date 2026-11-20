# ResumeIQ — AI Resume Analyzer (Streamlit)

Upload a resume (PDF/DOCX), paste a job description, and get an AI match score with matched/missing skills, strengths, gaps and resume suggestions. Each visitor gets **10 free analyses**.

**Stack:** Streamlit · Groq API (free tier, `openai/gpt-oss-120b`) · pdfplumber · python-docx. **No database.**

## Deploy on Streamlit Community Cloud

1. Create a GitHub repo and upload everything in this folder (keep the structure):
   ```
   app.py
   analyzer.py
   limiter.py
   requirements.txt
   README.md
   .gitignore
   .streamlit/config.toml
   .streamlit/secrets.toml.example
   ```
   **Never upload `.streamlit/secrets.toml` or a `.env` file** (they're in `.gitignore`).
2. Go to https://share.streamlit.io → **Create app** → pick the repo, branch `main`, main file `app.py`.
3. Open **Advanced settings → Secrets** and paste:
   ```toml
   GROQ_API_KEY = "your_key_from_console.groq.com"
   ```
4. Deploy. Get a free key at https://console.groq.com/keys.

## Run locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # add your key
streamlit run app.py
```

## How the 10-use limit works (no DB)

Streamlit can't set cookies, so visitors are identified by IP (`X-Forwarded-For`, which Streamlit Cloud provides) and counted in an in-memory limiter shared by all sessions.

- Refreshing the page does **not** reset the count.
- Counts reset when the app restarts/sleeps (free apps sleep when idle).
- Visitors behind the same IP (office/campus Wi-Fi) share the 10; a VPN gets a fresh 10.
- Failed analyses are refunded, not counted.

For a hard guarantee you'd add login + a database (e.g. Supabase/SQLite) — a good "next steps" answer in interviews. Change the limit with the `MAX_ANALYSES` secret.

## Security notes

- Server-side validation: extension + magic bytes, 5 MB cap, 10-page PDF cap, text length caps.
- Files are processed in memory, never written to disk.
- Prompt-injection hardening: resume/JD wrapped in tags and treated as data; model output is validated and clamped.
- All model/user text is HTML-escaped before display.
- API key lives only in Streamlit Secrets.

## Interview talking points

- **Pipeline:** upload → extract text → prompt LLM for strict JSON → validate/normalize → render.
- **Structure:** `analyzer.py` (pure logic) and `limiter.py` are framework-free and unit-testable; `app.py` is only UI.
- **JSON mode + fallback:** structured output is requested, but the parser tolerates fences/preamble and retries without optional params.
- **Reasoning-model budget:** `gpt-oss` spends tokens thinking, so `max_tokens=4000`, `reasoning_effort=low`.
- **Trade-offs:** IP-based in-memory limiter vs. accounts + DB.
- **Extensions:** ATS keyword density, bullet-by-bullet rewrites, OCR for scanned PDFs, caching by file hash.
