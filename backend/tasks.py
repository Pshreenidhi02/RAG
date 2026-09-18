from celery_app import celery_app

from dataprocessing.dataprocess import (
    process_file
)


@celery_app.task
def process_document_task(
    file_path
):

    print(
        "Celery processing:",
        file_path
    )

    result = process_file(
        file_path
    )

    return result