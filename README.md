# AI Student Study & Placement Assistant

A small web app that helps college students study from their own notes and prepare for placements.

## Features
- **Documents:** upload `.txt`, `.md`, `.csv` or `.pdf`, or paste text. The app finds the most relevant passages and shows which document they came from.
- **Ask & Study:** summaries, MCQs (answers only on request), important questions, interview questions and personalized prep plans. The assistant rules live in `SYSTEM_PROMPT` in `app.py`: use documents first, label general knowledge, never invent facts or qualifications, never judge eligibility or promise placement.
- **Resume & job match:** compares skills in a resume with a job description. Runs in the browser, no AI needed.

**No API key needed to try it.** Without a key, a built-in engine (`static/offline.js`) builds summaries, fill-in-the-blank MCQs (type "show answers" for the answers), important questions, interview questions and a 4-week plan directly from your documents, and shows matching passages for other questions. With a key, you get fuller AI-written answers.

## Project structure
```
app.py              Flask server (chat + PDF text extraction)
requirements.txt    Python dependencies
.env.example        Settings template
.gitignore
static/             index.html, style.css, app.js, offline.js
```

## Run it
1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Add your key (optional but needed for full answers):
   ```
   cp .env.example .env             # Windows: copy .env.example .env
   ```
   Open `.env` and set `ANTHROPIC_API_KEY`.
5. Start the server:
   ```
   python app.py
   ```
6. Open http://127.0.0.1:5000

## Deploy
Use a production server such as gunicorn: `gunicorn app:app`. Set `ANTHROPIC_API_KEY` as an environment variable on your host. Do not commit `.env`.

## Privacy notes
- Documents stay in the browser session. Only the passages relevant to a question are sent to the server and on to the AI service.
- PDFs are read in memory and are not saved.
- The API key stays on the server and is never sent to the browser.
