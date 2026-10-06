"""AI Student Study & Placement Assistant - Flask backend.

Serves the web page from ./static and keeps the Gemini API key
on the server.

Run:
    python app.py
"""

import io
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pypdf import PdfReader
from google import genai
from google.genai import types


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


# ---------------------------------------------------------
# Gemini client
# ---------------------------------------------------------

_client = None


def get_client():
    global _client

    if _client is None:
        if not API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")

        _client = genai.Client(api_key=API_KEY)

    return _client


# ---------------------------------------------------------
# Flask application
# ---------------------------------------------------------

app = Flask(
    __name__,
    static_folder="static",
    static_url_path=""
)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB uploads


# ---------------------------------------------------------
# Gemini system prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are an AI Student Study and Placement Assistant for college students.

Your responsibilities include:

- Academic study helper
- Personalized learning helper
- Placement preparation helper
- Resume and job-description analyst
- Interview coach
- Quiz generator

Use the RETRIEVED CONTEXT in the user's message as the primary source.

Name the source document when you use information from it.

Never present unsupported facts as coming from the documents.

If the documents do not contain the answer, say so clearly and then optionally provide general information labeled "General information".

Never fabricate:
- citations
- page numbers
- sources
- statistics
- qualifications
- experience
- achievements

If evidence is incomplete or conflicting, say so.

Style:
- Simple
- Student-friendly
- Organized
- Encouraging
- Professional

Use headings, bullets, tables and step-by-step explanations where useful.

For study questions:
1. Give a direct answer
2. Give a simple explanation
3. Give an example if useful
4. Give key points for revision

For placement questions:
1. Identify the required skill or concept
2. Explain it
3. Give an example interview question
4. Suggest a preparation area

For quiz requests:
- Base questions mainly on the retrieved material.
- Do NOT give answers unless the student asks.

For resume questions:
- Do not invent qualifications, experience or achievements.
- Only use information supported by the resume.

For interview questions:
- Ask questions appropriate for a college student.
- Use the student's uploaded resume when available.

Privacy:
- Do not ask for unnecessary personal information.
- Do not expose confidential document content.
- Do not decide employment eligibility.
- Do not guarantee placement.
"""


# ---------------------------------------------------------
# Home page
# ---------------------------------------------------------

@app.get("/")
def index():
    return app.send_static_file("index.html")


# ---------------------------------------------------------
# API status
# ---------------------------------------------------------

@app.get("/api/status")
def status():
    return jsonify(
        ai=bool(API_KEY),
        provider="Google Gemini",
        model=MODEL
    )


# ---------------------------------------------------------
# Chat API
# ---------------------------------------------------------

@app.post("/api/chat")
def chat():

    # Check Gemini API key
    if not API_KEY:
        return jsonify(
            error="GEMINI_API_KEY is not set on the server."
        ), 503

    # Read request data
    data = request.get_json(silent=True) or {}

    messages = data.get("messages")

    if not isinstance(messages, list) or not messages:
        return jsonify(
            error="Send a non-empty 'messages' list."
        ), 400

    # -----------------------------------------------------
    # Clean messages
    # -----------------------------------------------------

    clean = []

    for m in messages[-8:]:

        if (
            not isinstance(m, dict)
            or m.get("role") not in ("user", "assistant")
            or not isinstance(m.get("content"), str)
        ):
            return jsonify(
                error="Each message needs a role and text content."
            ), 400

        clean.append(
            {
                "role": m["role"],
                "content": m["content"][:20000]
            }
        )

    # First message should be from user
    if clean and clean[0]["role"] != "user":
        clean = clean[1:]

    if not clean:
        return jsonify(
            error="No valid user message found."
        ), 400

    # Last message should be from user
    if clean[-1]["role"] != "user":
        return jsonify(
            error="The last message must be from the user."
        ), 400

    # -----------------------------------------------------
    # Convert conversation to Gemini prompt
    # -----------------------------------------------------

    conversation = "\n\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in clean
    )

    try:

        # Gemini generation
        response = get_client().models.generate_content(
            model=MODEL,
            contents=conversation,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=1500,
                temperature=0.4
            )
        )

        reply = response.text or "Sorry, I could not generate a response."

        return jsonify(
            reply=reply
        )

    except Exception as exc:

        app.logger.exception("Gemini request failed")

        return jsonify(
            error=f"AI request failed: {type(exc).__name__}"
        ), 502


# ---------------------------------------------------------
# PDF extraction API
# ---------------------------------------------------------

@app.post("/api/extract")
def extract():

    f = request.files.get("file")

    # Check uploaded file
    if not f:
        return jsonify(
            error="Please upload a PDF file."
        ), 400

    if not f.filename.lower().endswith(".pdf"):
        return jsonify(
            error="Upload a .pdf file."
        ), 400

    # Extract PDF text
    try:

        reader = PdfReader(
            io.BytesIO(f.read())
        )

        text = "\n\n".join(
            (page.extract_text() or "")
            for page in reader.pages
        )

    except Exception:

        return jsonify(
            error="Could not read this PDF."
        ), 400

    # Check extracted text
    if not text.strip():

        return jsonify(
            error="No selectable text found (scanned PDF?)."
        ), 400

    return jsonify(
        text=text
    )


# ---------------------------------------------------------
# Start Flask server
# ---------------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "5000")
    )

    app.run(
        host="127.0.0.1",
        port=port,
        debug=False
    )