from fastapi import FastAPI, Form
import re
import os
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

#EXTRACTING THE VIDEO ID

def get_video_id(url: str) -> str:
    store_url = url
    ind = store_url.index('v') + 2
    video_id = store_url[ind:]
    return video_id

#GETTING THE ENTIRE TRANSCRIPT

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

#MAKING CHUNKS OF CONTENT TO AVOID MAXIMUM TOKEN LIMIT

def get_chunk(content, chunk_size = 500):
    chunk_list = []
    for chunk in range(0, len(content), chunk_size):
        chunk_list.append(content[chunk:chunk+chunk_size])
    return chunk_list


@app.post("/analyze-link")

async def analyze_link(link: str = Form(...)):
    if not GROQ_API_KEY:
        return {"error": "Groq API Key not set!"}
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

    combined_responses = []

    for chunk in chunk_list(transcript, chunk_size=500):
        prompt = f"Analyze the following video transcript chunk and answer the question: {user_question}\n\nChunk:\n{chunk}"
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        # Extract content safely
        try:
            answer = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            answer = "[Error processing this chunk]"
        combined_responses.append(answer)

    final_answer = "\n\n".join(combined_responses)
    return {"video_id": video_id, "analysis": final_answer[:2000]}  # truncate to first 2000 chars