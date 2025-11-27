from fastapi import FastAPI, UploadFile, File
import docx
from PyPDF2 import PdfReader
import os
import requests
from dotenv import load_dotenv

# Load .env file (if exists)
load_dotenv()

app = FastAPI()

# Get Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print("API Key being used:", GROQ_API_KEY[:8] + "..." if GROQ_API_KEY else "NOT SET")


@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...)):

    filename = file.filename.lower()

    if filename.endswith(".txt"):
        content = (await file.read()).decode("utf-8")    

    elif filename.endswith(".docx"):
        word_doc = docx.Document(file.file)
        cont = [para.text for para in word_doc.paragraphs]
        content = "\n".join(cont)

    elif filename.endswith(".pdf"):
        pdf_doc = PdfReader(file.file)
        cont = []
        for page in pdf_doc.pages:
            text = page.extract_text()
            if text:
                cont.append(text)
        content = "\n".join(cont)

    else:
        return {"error": "Unsupported file type"}

      # --- Step 2: Send to Groq API ---
    if not GROQ_API_KEY:
        return {"error": "Groq API Key not set!"}

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
            {"role": "user", "content": f"Summarize this document:\n\n{content[:2000]}"}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    print("Groq API status:", response.status_code)
    print("Groq API response text:", response.text)

    if response.status_code == 200:
        groq_output = response.json()["choices"][0]["message"]["content"]
    else:
        groq_output = f"Error: {response.text}"

    # --- Step 3: Return preview + Groq result ---
    return {
        "filename": file.filename,
        "content_preview": content[:500],
        "groq_summary": groq_output
    }