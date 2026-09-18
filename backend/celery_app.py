import os

from celery import Celery
from dotenv import load_dotenv


load_dotenv()


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0"
)


celery_app = Celery(
    "rag_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)


celery_app.conf.update(
    task_track_started=True,
    result_expires=3600
)

