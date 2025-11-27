from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
import docx
from PyPDF2 import PdfReader
import os
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print("API Key being used:", GROQ_API_KEY[:8] + "..." if GROQ_API_KEY else "NOT SET")

# 3 FIXED QUESTIONS THAT WILL COME ON THE FRONTEND EVERYTIME USER CLICKS ON NEW CHAT
questions = [
    "What are you learning today?",
    "How much depth are you planning to learn?",
    "How much time do you have to achieve this?"
]


# ---- Extract video ID from YouTube URL ----
def get_video_id(url: str) -> str:
    try:
        ind = url.index("v=") + 2
        video_id = url[ind:ind+11]  # YouTube video IDs are 11 chars
        return video_id
    except ValueError:
        return None


# ---- Get transcript text from YouTube ----
def get_youtube_transcript(video_id: str) -> str:
    try:
        # Create API object
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        data = fetched_transcript.to_raw_data()
        content = []
        for item in data:
            content.append(item["text"])

        content = " ".join(content)
        return content 

    except TranscriptsDisabled:
        print("⚠️ Transcripts are disabled for this video.")
        return None
    except NoTranscriptFound:
        print("⚠️ No transcript found for this video.")
        return None
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None
    

# ---- Split content into chunks ----
def get_chunks(content: str, chunk_size=500):
    return [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

@app.get("/questions")
def ask_questions():
    return {"question": questions}

@app.post("/analyze")
async def analysis(file: Optional[UploadFile] = File(None),  # <-- Optional here
    message: str = Form(...),
    link: Optional[str] = Form(None)):

    if link and file == "":
        if not GROQ_API_KEY:
            return {"error": "Groq API Key not set!"}

        video_id = get_video_id(link)
        if not video_id:
            return {"error": "Invalid YouTube link"}

        transcript = get_youtube_transcript(video_id)
        if not transcript:
            return {"error": "No transcript available for this video"}

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
        }

        c = get_chunks(transcript)
        last_chunk = c[-1]

        combined_responses = []

        for chunk in c:
            if (chunk==last_chunk):
                prompt = (f"Analyze and summarize the following video transcript chunk and give the combined response:\n\n{chunk}"
                          f"The user answers: {message}\n\n"
                          f"Prepare a syllabus based on the answers and make a comparison table with the provided combined chunks\n\n"
                          f"Show which topics are missing and why they are important."
                )
                
            else:
                prompt = f"Analyze and summarize the following video transcript chunk and give the combined response:\n\n{chunk}"
            
            payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
            }
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            try:
                answer = result["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                answer = "[Error processing this chunk]"
            combined_responses.append(answer)

        final_answer = "\n\n".join(combined_responses)
        return {"video_id": video_id, "analysis": final_answer[:2000]}  # truncate

    
    elif file:
        content = None
        filename = file.filename.lower()

        if filename.endswith(".txt"):
            content = (await file.read()).decode("utf-8")

        elif filename.endswith(".docx"):
            word_doc = docx.Document(file.file)
            content = "\n".join([para.text for para in word_doc.paragraphs])

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

        # ---- Build prompt ----
        if content:
            prompt = (
                f"Imagine you have asked these questions:\n{questions}\n\n"
                f"The user answers: {message}\n\n"
                f"Prepare a syllabus based on the answers and make a comparison table with the provided material:\n\n{content}\n\n"
                f"Show which topics are missing and why they are important."
            )
        else:
            prompt = (
                f"Imagine you have asked these questions:\n{questions}\n\n"
                f"The user answers: {message}\n\n"
                f"Prepare a syllabus in accordance with the user's answers."
            )

        # ---- API Key check ----
        if not GROQ_API_KEY:
            return {"error": "Groq API Key not set!"}

        # ---- Call Groq API ----
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(url, headers=headers, json=payload)
        groq_reply = response.json()
        
        try:
            llm_answer = groq_reply["choices"][0]["message"]["content"]
        except KeyError:
            return {"error": "Invalid response from Groq API", "raw": groq_reply}

        # ---- Return clean response ----
        return {
            "user_answers": message,
            "file_included": True,
            "llm_response": llm_answer
        }
    
    

    