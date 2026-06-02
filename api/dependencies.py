from fastapi import UploadFile, HTTPException
import os
import uuid
from neuromarketing.config import UPLOAD_DIR


ALLOWED_VIDEO = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
ALLOWED_AUDIO = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
ALLOWED_TEXT = {".txt", ".md", ".html"}


async def save_upload(upload: UploadFile) -> str:
    ext = os.path.splitext(upload.filename)[1].lower()
    if ext not in ALLOWED_VIDEO | ALLOWED_AUDIO | ALLOWED_TEXT:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, safe_name)

    content = await upload.read()
    with open(path, "wb") as f:
        f.write(content)

    return path
