from celery_app import celery_app

from dataprocessing.dataprocess import process_file


@celery_app.task(
    name="rag.process_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_document_task(file_path, title=None, source_id=None):
    print("Celery processing:", file_path)

    return process_file(
        file_path,
        title=title,
        source_id=source_id,
    )