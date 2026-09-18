
 
from gdrive_setup import drive_state
from gdrive_setup.google_drive import (
    DRIVE_MIME_TYPES,
    download_drive_file,
    folder_id,
    list_folder_files,
)
from ingest import enqueue_file
 
 
MAX_BYTES = 50 * 1024 * 1024
 
 
def ingest_drive_file(drive_file):
    """Download one Drive file and queue it for ingestion."""
    file_id = drive_file["id"]
    file_name = drive_file.get("name", file_id)
 
    size = int(drive_file.get("size") or 0)
 
    if size and size > MAX_BYTES:
        return {
            "file_id": file_id,
            "name": file_name,
            "status": "skipped",
            "reason": f"larger than {MAX_BYTES // (1024 * 1024)} MB",
        }
 
    file_path = download_drive_file(
        file_id, file_name, drive_file.get("mimeType", "")
    )
 
    queued = enqueue_file(
        file_path=file_path,
        title=file_name,
        # The Drive file id is stable across renames; the filename is not.
        # Using it means editing a file in Drive REPLACES its chunks
        # instead of creating a second copy.
        source_id=f"gdrive:{file_id}",
    )
 
    drive_state.mark_processed(drive_file)
 
    return {
        "file_id": file_id,
        "name": file_name,
        "status": "queued",
        "detail": queued,
    }
 
 
def sync_folder(force=False):
    """List the folder, ingest what is new. force=True re-ingests everything."""
    target = folder_id()
 
    files = list_folder_files(target)
 
    print(f"Folder {target}: {len(files)} supported files")
 
    processed = []
    skipped = []
 
    for drive_file in files:
        if drive_file.get("mimeType") not in DRIVE_MIME_TYPES:
            skipped.append({
                "name": drive_file.get("name"),
                "status": "skipped",
                "reason": "unsupported type",
            })
            continue
 
        if not force and not drive_state.is_new_or_updated(drive_file):
            skipped.append({
                "name": drive_file.get("name"),
                "status": "unchanged",
            })
            continue
 
        try:
            processed.append(ingest_drive_file(drive_file))
        except Exception as error:
            # One bad file must not abort the rest of the folder.
            print(f"Failed on {drive_file.get('name')}: {error}")
            skipped.append({
                "name": drive_file.get("name"),
                "status": "error",
                "reason": str(error),
            })
 
    queued_count = len(
        [item for item in processed if item.get("status") == "queued"]
    )
 
    return {
        "status": "success",
        "folder_id": target,
        "files_seen": len(files),
        "processed_files": queued_count,
        "processed": processed,
        "skipped": skipped,
    }