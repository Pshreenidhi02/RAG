
import io
import json
import os
import re
import threading
from pathlib import Path
 
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
 
 
# backend/gdrive_setup/google_drive.py -> parents[2] is the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
 
# Read-only: this key can list and download, never modify or delete.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
 
DOWNLOAD_DIR = PROJECT_ROOT / "data" / "downloads"
 
# Only these are ingestible today. The value is the extension used when a
# Drive filename has none.
DRIVE_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument"
    ".wordprocessingml.document": ".docx",
}
 
# md5Checksum and modifiedTime are needed for dedupe; parents for folder
# filtering. Drive omits all of them unless explicitly requested.
FILE_FIELDS = (
    "id, name, mimeType, md5Checksum, modifiedTime, size, trashed, parents"
)
 
_service = None
_lock = threading.Lock()
 
 
def service_account_path():
    """Where the JSON key lives. Absolute paths are used as given."""
    raw = (os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE") or "").strip()
    raw = raw or "service_account.json"
 
    path = Path(raw)
    return path if path.is_absolute() else PROJECT_ROOT / path
 
 
def credentials_available():
    return service_account_path().exists()
 
 
def service_account_email():
    """The address the Drive folder must be shared with."""
    try:
        with open(service_account_path(), encoding="utf-8") as handle:
            return json.load(handle).get("client_email")
    except Exception:
        return None
 
 
def folder_id():
    value = (os.getenv("GOOGLE_DRIVE_FOLDER_ID") or "").strip()
 
    if not value:
        raise RuntimeError("GOOGLE_DRIVE_FOLDER_ID is not set in .env")
 
    return value
 
 
def get_drive_service():
    """One cached Drive client per process."""
    global _service
 
    if _service is None:
        with _lock:
            if _service is None:
                key_path = service_account_path()
 
                if not key_path.exists():
                    raise RuntimeError(
                        f"Service account key not found at {key_path}. "
                        "Set GOOGLE_SERVICE_ACCOUNT_FILE in .env."
                    )
 
                credentials = (
                    service_account.Credentials.from_service_account_file(
                        str(key_path), scopes=SCOPES
                    )
                )
 
                print(f"Drive service account -> {service_account_email()}")
 
                _service = build(
                    "drive",
                    "v3",
                    credentials=credentials,
                    cache_discovery=False,
                )
 
    return _service
 
 
def list_folder_files(target_folder_id=None):
    """Every supported, non-trashed file directly inside the folder."""
    target_folder_id = target_folder_id or folder_id()
 
    service = get_drive_service()
 
    mime_clause = " or ".join(
        f"mimeType='{mime}'" for mime in DRIVE_MIME_TYPES
    )
 
    query = (
        f"'{target_folder_id}' in parents "
        f"and trashed=false and ({mime_clause})"
    )
 
    files = []
    page_token = None
 
    while True:
        response = (
            service.files()
            .list(
                q=query,
                fields=f"nextPageToken, files({FILE_FIELDS})",
                pageSize=100,
                pageToken=page_token,
                # Required if the folder lives in a Shared Drive; without
                # these the folder looks empty.
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
 
        files.extend(response.get("files", []))
 
        page_token = response.get("nextPageToken")
 
        # Drive pages at 100 items. Without this loop a folder of 150 files
        # silently gives you 100.
        if not page_token:
            break
 
    return files
 
 
def safe_local_name(file_id, file_name, mime_type=""):
    """A filesystem-safe name that cannot escape DOWNLOAD_DIR."""
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", file_name or "file").strip("_")
 
    if not Path(name).suffix:
        name += DRIVE_MIME_TYPES.get(mime_type, "")
 
    # file_id prefix: two Drive files may share a name.
    return f"{file_id}_{name}"[:150]
 
 
def download_drive_file(file_id, file_name, mime_type=""):
    """Download to data/downloads and return the absolute path."""
    service = get_drive_service()
 
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
 
    file_path = DOWNLOAD_DIR / safe_local_name(file_id, file_name, mime_type)
 
    request = service.files().get_media(
        fileId=file_id, supportsAllDrives=True
    )
 
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request, chunksize=1024 * 1024)
 
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"Download {file_name}: {int(status.progress() * 100)}%")
 
    # Write once, so an interrupted download leaves no half-file for the
    # parser to choke on.
    file_path.write_bytes(buffer.getvalue())
 
    print("Downloaded:", file_path)
 
    return str(file_path)