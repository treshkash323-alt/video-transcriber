# -*- coding: utf-8
"""Сборка DZ-10 docx. Скрины: папка screenshots/ — см. screenshots/README.md."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
GITHUB = "https://github.com/treshkash323-alt/video-transcriber"

FIGURES = [
    (
        "01-ui-3-success.png",
        "Рис. 1. Транскрибация — :8000, три задачи SUCCESS с текстом",
    ),
    (
        "02-flower-tasks.png",
        "Рис. 2. Flower — мониторинг, Succeeded: 3",
    ),
    (
        "03-flower-3-workers.png",
        "Рис. 3. Масштаб — три worker Online (docker compose --scale worker=3)",
    ),
    (
        "04-docker-compose.png",
        "Рис. 4. Запуск — docker compose up --build в терминале",
    ),
    (
        "05-docker-desktop.png",
        "Рис. 5. Docker Desktop — сервисы video-transcriber",
    ),
    (
        "06-history-after-restart.png",
        "Рис. 6. История SQLite — :8000 после docker compose down и повторного up",
    ),
    (
        "07-swagger-history.png",
        "Рис. 7. Swagger — GET /history возвращает список задач",
    ),
]


def setup_doc(title: str) -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(2)
    sec.bottom_margin = Cm(2)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2)
    h = doc.add_heading(title, level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return doc


def meta(doc: Document, rows: list[tuple[str, str]]) -> None:
    for a, b in rows:
        p = doc.add_paragraph()
        p.add_run(a + " ").bold = True
        p.add_run(b)
    doc.add_paragraph()


def table(doc: Document, headers: list[str], rows: list[tuple]) -> None:
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        t.rows[0].cells[i].text = h
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            t.rows[ri + 1].cells[ci].text = str(val)
    doc.add_paragraph()


def add_figure(doc: Document, filename: str, caption: str) -> str:
    """Вставить PNG или placeholder. Возвращает статус для таблицы."""
    path = SCREENSHOTS / filename
    doc.add_paragraph(caption).runs[0].bold = True
    if path.is_file():
        doc.add_picture(str(path), width=Cm(15.5))
        status = "✅"
    else:
        p = doc.add_paragraph()
        run = p.add_run(f"[Вставить скрин: screenshots/{filename}]")
        run.italic = True
        status = "☐"
    doc.add_paragraph()
    return status


def build_report() -> Path:
    doc = setup_doc("ДЗ-10 — отчёт для сдачи (Lite)")
    meta(
        doc,
        [
            ("Студент:", "Игорь Кашинцев"),
            ("Курс:", "VibeCoder, Тема 10 — Celery, FastAPI"),
            ("Проект:", "video-transcriber"),
            ("GitHub:", GITHUB),
            ("Папка:", "Projects/ДЗ-10/video-transcriber/"),
            ("Запуск:", "localhost:8000 · Flower :5555"),
            ("Дата:", "2026 · готово к сдаче"),
        ],
    )

    doc.add_heading("1. Цель", level=1)
    doc.add_paragraph(
        "AI-транскрибатор: FastAPI принимает файлы, Celery + Whisper обрабатывает в фоне, "
        "Redis — очередь, Flower — мониторинг. Статусы PENDING → STARTED → SUCCESS. "
        "Масштаб: --scale worker=3. История задач — SQLite (data/history.db)."
    )

    doc.add_heading("2. Стек", level=1)
    doc.add_paragraph(
        "Docker Compose · FastAPI · Celery · Redis · Flower · OpenAI Whisper · "
        "SQLite (история) · FFmpeg"
    )

    doc.add_heading("3. Безопасность", level=1)
    table(
        doc,
        ["Проверка", "Результат"],
        [
            (".env в git", "Нет"),
            ("API key в коде", "Нет"),
            ("Лимит 25 МБ", "Да (UI + сервер)"),
            ("Redis наружу", "Нет"),
        ],
    )

    doc.add_heading("4. Скриншоты", level=1)
    doc.add_paragraph(
        "PNG положите в папку screenshots/ (имена — в screenshots/README.md), "
        "затем: python build_docx_dz10.py"
    )

    figure_status: list[tuple[str, str, str]] = []
    for filename, caption in FIGURES:
        short = caption.split("—", 1)[0].strip()
        status = add_figure(doc, filename, caption)
        figure_status.append((filename.replace(".png", ""), short, status))

    doc.add_heading("5. Чеклист скринов", level=1)
    table(
        doc,
        ["Файл", "Описание", "Статус"],
        [(a, b, c) for a, b, c in figure_status],
    )

    doc.add_heading("6. Результат", level=1)
    table(
        doc,
        ["Пункт", "Статус"],
        [
            ("docker compose up — 4 сервиса", "✅"),
            ("3 файла транскрибированы", "✅"),
            ("Flower работает", "✅"),
            ("scale worker=3", "✅"),
            ("История SQLite", "✅"),
            ("GitHub без секретов", "✅"),
            ("Скрины в Word", "☐" if any(s == "☐" for *_, s in figure_status) else "✅"),
        ],
    )

    doc.add_heading("7. Комментарий для преподавателя", level=1)
    doc.add_paragraph(
        "Lite: FastAPI + Celery + Redis + Docker. Whisper через OpenAI API. "
        "Лимит 25 МБ учтён. Flower на том же образе, что worker. "
        "История задач в SQLite переживает docker compose down. "
        "План развития: EDU + CRM — TODO_ROADMAP.md."
    )

    out = ROOT / "DZ-10_отчёт_для_сдачи.docx"
    doc.save(out)
    return out


if __name__ == "__main__":
    path = build_report()
    found = sum(1 for f, _ in FIGURES if (SCREENSHOTS / f).is_file())
    print(f"OK: {path}")
    print(f"Скринов вставлено: {found}/{len(FIGURES)}")
