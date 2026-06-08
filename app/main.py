import os
import uuid
from contextlib import asynccontextmanager
from typing import List

import aiofiles
from celery.result import AsyncResult
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from app.celery_app import celery_app
from app import history
from app.tasks import transcribe_video


@asynccontextmanager
async def lifespan(_app: FastAPI):
    history.init_db()
    yield


app = FastAPI(title='AI Транскрибатор видео', lifespan=lifespan)
UPLOAD_DIR = 'uploads'
# OpenAI Whisper API limit
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_FILES = 3

INDEX_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Транскрибатор · ДЗ-10</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; max-width: 960px; margin: 0 auto; padding: 2rem; background: #f8fafc; color: #0f172a; }
    h1 { margin-top: 0; }
    .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
    button { background: #4f46e5; color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; cursor: pointer; font-size: 1rem; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { border: 1px solid #e2e8f0; padding: 0.6rem; text-align: left; vertical-align: top; }
    th { background: #f1f5f9; }
    .status-PENDING { color: #64748b; }
    .status-STARTED { color: #d97706; }
    .status-SUCCESS { color: #059669; font-weight: 600; }
    .status-FAILURE { color: #dc2626; font-weight: 600; }
    .status-ERROR { color: #dc2626; font-weight: 600; }
    .file-list { font-size: 0.85rem; color: #475569; margin-top: 0.5rem; }
    .file-list .bad { color: #dc2626; }
    .transcript { white-space: pre-wrap; max-width: 400px; font-size: 0.85rem; color: #334155; }
    .hint { font-size: 0.85rem; color: #64748b; margin-top: 0.5rem; }
    .persist { font-size: 0.85rem; color: #059669; margin: 0.5rem 0 0; }
    .links a { margin-right: 1rem; }
  </style>
</head>
<body>
  <h1>AI Транскрибатор видео</h1>
  <p class="links">
    <a href="/docs">Swagger</a>
    <a href="http://localhost:5555" target="_blank">Flower</a>
  </p>

  <div class="card">
    <form id="upload-form">
      <p><strong>Загрузите 1–3 файла</strong> (30–60 сек, до 25 МБ каждый)</p>
      <input type="file" id="files" name="files" multiple accept="video/*,audio/*,.mp4,.mov,.mp3,.wav,.m4a" required />
      <p class="hint">MP4, MOV, MP3, WAV · Ctrl+клик — несколько файлов · PENDING → STARTED → SUCCESS</p>
      <p id="file-list" class="file-list"></p>
      <p style="margin-top: 1rem;"><button type="submit" id="submit-btn">Транскрибировать</button></p>
    </form>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Задачи</h2>
    <p class="persist">История сохраняется в SQLite (<code>data/history.db</code>) — переживёт <code>docker compose down</code></p>
    <table>
      <thead>
        <tr>
          <th>Файл</th>
          <th>Task ID</th>
          <th>Статус</th>
          <th>Результат</th>
        </tr>
      </thead>
      <tbody id="tasks-body"></tbody>
    </table>
  </div>

  <script>
    const MAX_BYTES = 25 * 1024 * 1024;
    const MAX_FILES = 3;
    const tasks = new Map();
    let pollTimer = null;

    function fmtMb(bytes) {
      return (bytes / (1024 * 1024)).toFixed(1) + ' МБ';
    }

    document.getElementById('files').addEventListener('change', (e) => {
      const list = document.getElementById('file-list');
      const files = e.target.files;
      if (!files.length) { list.textContent = ''; return; }
      if (files.length > MAX_FILES) {
        list.innerHTML = '<span class="bad">Выберите не больше ' + MAX_FILES + ' файлов</span>';
        return;
      }
      list.innerHTML = Array.from(files).map(f => {
        const bad = f.size > MAX_BYTES;
        return '<span class="' + (bad ? 'bad' : '') + '">' + f.name + ' — ' + fmtMb(f.size) + (bad ? ' (слишком большой!)' : '') + '</span>';
      }).join('<br>');
    });

    function statusClass(s) {
      return 'status-' + (s || 'PENDING');
    }

    function renderRow(taskId, data, prepend) {
      let row = document.getElementById('row-' + taskId);
      const tbody = document.getElementById('tasks-body');
      if (!row) {
        row = document.createElement('tr');
        row.id = 'row-' + taskId;
        row.innerHTML =
          '<td class="file-cell"></td>' +
          '<td class="id-cell" style="font-size:0.75rem;word-break:break-all"></td>' +
          '<td class="status-cell status-PENDING">PENDING</td>' +
          '<td class="result-cell">…</td>';
        if (prepend) tbody.prepend(row);
        else tbody.appendChild(row);
      }
      row.querySelector('.file-cell').textContent = data.filename || '—';
      row.querySelector('.id-cell').textContent = taskId;
      const statusEl = row.querySelector('.status-cell');
      const resultEl = row.querySelector('.result-cell');

      let displayStatus = data.status;
      if (data.status === 'SUCCESS' && data.result && data.result.status === 'error') {
        displayStatus = 'ERROR';
      }
      statusEl.textContent = displayStatus;
      statusEl.className = 'status-cell ' + statusClass(displayStatus === 'ERROR' ? 'ERROR' : data.status);

      if (data.status === 'SUCCESS' && data.result) {
        if (data.result.status === 'error') {
          resultEl.textContent = data.result.error || 'unknown';
        } else {
          resultEl.innerHTML = '<div class="transcript">' + (data.result.transcript || '') + '</div>';
        }
      } else if (data.status === 'ERROR' && data.result) {
        resultEl.textContent = data.result.error || 'unknown';
      } else if (data.status === 'FAILURE') {
        resultEl.textContent = 'FAILURE';
      } else if (data.status === 'PENDING' || data.status === 'STARTED') {
        resultEl.textContent = '…';
      } else {
        resultEl.textContent = '…';
      }
    }

    async function pollTask(taskId) {
      try {
        const res = await fetch('/status/' + taskId);
        const data = await res.json();
        renderRow(taskId, data);
        if (data.status === 'SUCCESS' || data.status === 'FAILURE' || data.status === 'ERROR') {
          tasks.delete(taskId);
        }
      } catch (e) {
        console.error(e);
      }
    }

    function startPolling() {
      if (pollTimer) return;
      pollTimer = setInterval(() => {
        for (const taskId of tasks.keys()) {
          pollTask(taskId);
        }
        if (tasks.size === 0) {
          clearInterval(pollTimer);
          pollTimer = null;
        }
      }, 3000);
    }

    function addTask(taskId, filename) {
      renderRow(taskId, { filename: filename, status: 'PENDING', result: null }, true);
      tasks.set(taskId, filename);
      pollTask(taskId);
      startPolling();
    }

    async function loadHistory() {
      try {
        const res = await fetch('/history');
        const items = await res.json();
        const tbody = document.getElementById('tasks-body');
        tbody.innerHTML = '';
        for (const item of items) {
          renderRow(item.task_id, item);
          if (item.status === 'PENDING' || item.status === 'STARTED') {
            tasks.set(item.task_id, item.filename);
          }
        }
        if (tasks.size > 0) startPolling();
      } catch (e) {
        console.error(e);
      }
    }

    loadHistory();

    document.getElementById('upload-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const input = document.getElementById('files');
      const btn = document.getElementById('submit-btn');
      if (!input.files.length) return;
      if (input.files.length > MAX_FILES) {
        alert('Максимум ' + MAX_FILES + ' файла за раз');
        return;
      }
      for (const file of input.files) {
        if (file.size > MAX_BYTES) {
          alert(file.name + ' больше 25 МБ. Сожмите файл или используйте TRANSCRIPTION_BACKEND=local');
          return;
        }
      }

      const formData = new FormData();
      for (const file of input.files) {
        formData.append('files', file);
      }

      btn.disabled = true;
      try {
        const res = await fetch('/transcribe', { method: 'POST', body: formData });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        for (const t of data.tasks) {
          addTask(t.task_id, t.filename);
        }
        input.value = '';
        document.getElementById('file-list').textContent = '';
      } catch (err) {
        alert('Ошибка загрузки: ' + err.message);
      } finally {
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


@app.get('/', response_class=HTMLResponse)
async def index():
    return INDEX_HTML


@app.post('/transcribe')
async def transcribe(files: List[UploadFile] = File(...)):
    if len(files) > MAX_FILES:
        raise HTTPException(400, f'Максимум {MAX_FILES} файла за запрос')

    task_ids = []
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    for file in files:
        content = await file.read()
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(
                413,
                f'{file.filename}: больше 25 МБ (лимит OpenAI Whisper API)',
            )

        ext = file.filename.split('.')[-1] if file.filename and '.' in file.filename else 'bin'
        unique_name = f'{uuid.uuid4()}.{ext}'
        path = os.path.join(UPLOAD_DIR, unique_name)

        async with aiofiles.open(path, 'wb') as f:
            await f.write(content)

        task = transcribe_video.delay(path, file.filename or unique_name)
        history.create_task(task.id, file.filename or unique_name)
        task_ids.append({'task_id': task.id, 'filename': file.filename or unique_name})

    return {'tasks': task_ids}


@app.get('/status/{task_id}')
def get_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    celery_status = result.status
    celery_result = result.result if result.ready() else None

    stored = history.get_task(task_id)
    filename = stored['filename'] if stored else '—'

    if celery_status in ('PENDING',) and stored and stored['status'] in (
        'SUCCESS',
        'ERROR',
        'FAILURE',
    ):
        return stored

    if celery_status in ('STARTED', 'SUCCESS', 'FAILURE'):
        history.update_status(task_id, filename, celery_status, celery_result)

    return {
        'task_id': task_id,
        'filename': filename,
        'status': celery_status,
        'result': celery_result,
    }


@app.get('/history')
def get_history():
    return history.list_tasks()
