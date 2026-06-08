"""SQLite — история задач на диске (переживает docker compose down)."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

DB_PATH = os.getenv('HISTORY_DB_PATH', 'data/history.db')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _display_status(celery_status: str, result: dict[str, Any] | None) -> str:
    if celery_status == 'SUCCESS' and result and result.get('status') == 'error':
        return 'ERROR'
    return celery_status


def _row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    result = json.loads(row['result']) if row['result'] else None
    return {
        'task_id': row['task_id'],
        'filename': row['filename'],
        'status': row['status'],
        'result': result,
        'created_at': row['created_at'],
    }


def create_task(task_id: str, filename: str) -> None:
    init_db()
    now = _now()
    with _conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO tasks
                (task_id, filename, status, result, created_at, updated_at)
            VALUES (?, ?, 'PENDING', NULL, ?, ?)
            """,
            (task_id, filename, now, now),
        )


def save_task_result(
    task_id: str,
    filename: str,
    celery_status: str,
    result: dict[str, Any] | None,
) -> None:
    init_db()
    status = _display_status(celery_status, result)
    now = _now()
    result_json = json.dumps(result, ensure_ascii=False) if result is not None else None
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO tasks
                (task_id, filename, status, result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                filename = excluded.filename,
                status = excluded.status,
                result = excluded.result,
                updated_at = excluded.updated_at
            """,
            (task_id, filename, status, result_json, now, now),
        )


def update_status(
    task_id: str,
    filename: str,
    celery_status: str,
    result: dict[str, Any] | None = None,
) -> None:
    init_db()
    status = _display_status(celery_status, result)
    now = _now()
    result_json = json.dumps(result, ensure_ascii=False) if result is not None else None
    with _conn() as conn:
        if result is not None:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, result = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (status, result_json, now, task_id),
            )
        else:
            conn.execute(
                """
                UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?
                """,
                (status, now, task_id),
            )
        if conn.total_changes == 0:
            conn.execute(
                """
                INSERT INTO tasks
                    (task_id, filename, status, result, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (task_id, filename, status, result_json, now, now),
            )


def get_task(task_id: str) -> dict[str, Any] | None:
    init_db()
    with _conn() as conn:
        row = conn.execute(
            'SELECT * FROM tasks WHERE task_id = ?',
            (task_id,),
        ).fetchone()
    return _row_to_payload(row) if row else None


def list_tasks(limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            'SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?',
            (limit,),
        ).fetchall()
    return [_row_to_payload(row) for row in rows]
