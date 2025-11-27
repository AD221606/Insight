from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form

app = FastAPI()

@app.post("/submit/")
async def submit(
    message: str = Form(...),
    youtube_link: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)  # expects UploadFile or None
):
    return {
        "message": message,
        "youtube_link": youtube_link,
        "file": file.filename if file else None
    }
