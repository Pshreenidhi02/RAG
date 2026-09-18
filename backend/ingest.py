"""Single entry point for queueing ingestion work."""

import os


INGEST_MODE = (os.getenv("INGEST_MODE") or "celery").strip().lower()


def enqueue_file(file_path, title=None, source_id=None):
    """Queue a file for ingestion; fall back to inline if the broker is down."""
    if INGEST_MODE != "inline":
        try:
            from tasks import process_document_task

            async_result = process_document_task.delay(
                file_path=str(file_path),
                title=title,
                source_id=source_id,
            )

            return {
                "mode": "celery",
                "status": "queued",
                "task_id": async_result.id,
                "title": title,
            }

        except Exception as error:
            print(f"Celery unavailable ({error}); processing inline.")

    from dataprocessing.dataprocess import process_file

    result = process_file(file_path, title=title, source_id=source_id)
    result["mode"] = "inline"
    return result