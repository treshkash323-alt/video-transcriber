import os
from typing import Any

from app.celery_app import celery_app
from app.history import save_task_result

# Alias for: celery -A app.tasks worker
app = celery_app

_whisper_model = None


def _get_local_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        size = os.getenv('WHISPER_MODEL_SIZE', 'base')
        _whisper_model = WhisperModel(size, device='cpu', compute_type='int8')
    return _whisper_model


def _transcribe_openai(file_path: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    with open(file_path, 'rb') as f:
        response = client.audio.transcriptions.create(model='whisper-1', file=f)
    return response.text


def _transcribe_local(file_path: str) -> str:
    model = _get_local_model()
    segments, _info = model.transcribe(file_path)
    return ' '.join(segment.text.strip() for segment in segments)


@celery_app.task(bind=True, name='transcribe_video')
def transcribe_video(self, file_path: str, original_filename: str) -> dict[str, Any]:
    try:
        backend = os.getenv('TRANSCRIPTION_BACKEND', 'openai').lower()
        if backend == 'local':
            transcript = _transcribe_local(file_path)
        else:
            transcript = _transcribe_openai(file_path)

        result = {
            'filename': original_filename,
            'transcript': transcript,
            'status': 'done',
        }
        save_task_result(self.request.id, original_filename, 'SUCCESS', result)
        return result
    except Exception as e:
        result = {
            'filename': original_filename,
            'status': 'error',
            'error': str(e),
        }
        save_task_result(self.request.id, original_filename, 'SUCCESS', result)
        return result
