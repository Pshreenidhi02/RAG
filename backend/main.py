import os
import gradio as gr

from gradio_app import create_gradio_app

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from dataprocessing.dataprocess import process_file
from userQuery import user_query
#from drive_changes import process_drive_changes
#from google_drive import download_drive_file

load_dotenv()
app = FastAPI()


class FileRequest(BaseModel):
    file_path: str


class QuestionRequest(BaseModel):
    question: str

class DriveFileRequest(BaseModel):
    file_id: str
    file_name: str




@app.post("/process-file")
def process_file_endpoint(request: FileRequest):

    result = process_file(request.file_path)

    return {
        "message": "File processed successfully",
        "result": result
    }


@app.post("/ask")
def ask_question_endpoint(request: QuestionRequest):

    answer = user_query(request.question)

    return {
        "question": request.question,
        "answer": answer
    }
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

gradio_app = create_gradio_app()

app = gr.mount_gradio_app(
    app,
    gradio_app,
    path="/gradio"
)