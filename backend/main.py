import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from fastapi import (BackgroundTasks, FastAPI, HTTPException, Query, Request,)
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from gdrive_setup.drive_sync import sync_folder
from gdrive_setup.drive_watch import (
    drive_status,
    setup_drive_watch,
    stop_drive_watch,
)
from gradio_app import create_gradio_app
from ingest import enqueue_file
from userQuery.user_query import ask

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(title="Selectiva RAG")


class FileRequest(BaseModel):
    file_path: str
    title: Optional[str] = None
    source_id: Optional[str] = None


class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process-file")
def process_file_endpoint(request: FileRequest):

    path = Path(request.file_path)

    result = enqueue_file(
            request.file_path,
            title=request.title,
            source_id=request.source_id,
        )

    return {
        "message": "File accepted",
        "result": result,
    }



@app.post("/ask")
def ask_question_endpoint(request: QuestionRequest):


    answer = ask(request.question)
    return {
        "question": request.question,
        "answer": answer
    }


@app.get("/admin/google-drive/status")
def admin_status():
    return drive_status()


@app.post("/admin/google-drive/sync-now")
def admin_sync_now(force: bool = Query(False)):
    try:
        return sync_folder(force=force)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/admin/google-drive/watch")
def admin_watch():
    try:
        return setup_drive_watch()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/admin/google-drive/stop")
def admin_stop():
    return stop_drive_watch()


@app.post("/webhooks/google-drive")
async def google_drive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    token: str | None = Query(None),
):
    resource_state = request.headers.get("X-Goog-Resource-State")
    channel_id = request.headers.get("X-Goog-Channel-ID")
    header_token = request.headers.get("X-Goog-Channel-Token")

    print(f"Drive webhook: state={resource_state} channel={channel_id}")

    expected = (os.getenv("GOOGLE_DRIVE_WEBHOOK_TOKEN") or "").strip()

    # Fail closed: an empty expected token must not match an empty supplied one
    if not expected:
        raise HTTPException(503, "Webhook token not configured")

    supplied = [value for value in (token, header_token) if value]
    if not supplied or any(value != expected for value in supplied):
        raise HTTPException(403, "Invalid webhook token")

    # Sent once right after registration — not a real change
    if resource_state == "sync":
        return {"status": "sync received"}

    # 202 immediately; Google's timeout is a few seconds and it retires
    # channels that keep timing out
    background_tasks.add_task(sync_folder)

    return JSONResponse({"status": "accepted"}, status_code=202)

@app.post("/google-drive/webhook")
async def google_drive_webhook(
    request: Request
):

    # Google sends metadata through headers

    channel_token = request.headers.get(
        "X-Goog-Channel-Token"
    )

    resource_state = request.headers.get(
        "X-Goog-Resource-State"
    )

    channel_id = request.headers.get(
        "X-Goog-Channel-ID"
    )

    print("\n==============================")
    print("GOOGLE DRIVE WEBHOOK")
    print("==============================")

    print(
        "Channel ID:",
        channel_id
    )

    print(
        "Resource State:",
        resource_state
    )

    # --------------------------------------
    # Security check
    # --------------------------------------

    if channel_token != GOOGLE_WEBHOOK_TOKEN:

        raise HTTPException(
            status_code=403,
            detail="Invalid webhook token"
        )

    # --------------------------------------
    # Initial sync event
    # --------------------------------------

    if resource_state == "sync":

        print(
            "Google Drive watch synchronized."
        )

        return {
            "status": "sync received"
        }

    # --------------------------------------
    # Actual Drive change
    # --------------------------------------

    process_drive_changes()

    return {
        "status": "Drive changes processed"   
    }



# ==========================================
# Gradio
# ==========================================

app = gr.mount_gradio_app(app, create_gradio_app(), path="/gradio")