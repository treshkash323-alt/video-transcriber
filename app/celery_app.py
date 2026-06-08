from celery import Celery

celery_app = Celery(
    'video_transcriber',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
    task_track_started=True,
)
