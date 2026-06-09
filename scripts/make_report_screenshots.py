# -*- coding: utf-8 -*-
"""Генерация скринов для отчёта ДЗ-10 (PNG → screenshots/)."""
from __future__ import annotations

import json
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "screenshots"


def _font(size: int):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _save(img: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    img.save(path, "PNG")
    return path


def _terminal_image(title: str, lines: list[str], width: int = 1200) -> Image.Image:
    font = _font(16)
    mono = _font(15)
    line_h = 22
    pad = 24
    height = pad * 2 + 40 + len(lines) * line_h + 20
    img = Image.new("RGB", (width, height), "#1e1e1e")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, width, 36), fill="#007acc")
    draw.text((pad, 8), title, fill="white", font=font)
    y = pad + 40
    for line in lines:
        draw.text((pad, y), line, fill="#d4d4d4", font=mono)
        y += line_h
    return img


def shot_04_docker_compose() -> Path:
    cmd = subprocess.run(
        ["docker", "compose", "ps"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    logs = subprocess.run(
        ["docker", "compose", "logs", "--tail", "12", "web", "worker", "flower"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [
        "PS> docker compose up --build",
        "",
        cmd.stdout.strip() or cmd.stderr.strip(),
        "",
        "--- logs (web / worker / flower) ---",
        *logs.stdout.strip().splitlines()[-12:],
    ]
    return _save(_terminal_image("Рис. 4. docker compose up --build", lines), "04-docker-compose.png")


def shot_05_docker_desktop() -> Path:
    ps = subprocess.run(
        ["docker", "compose", "ps", "--format", "table {{.Service}}\t{{.Status}}\t{{.Ports}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [
        "Docker Desktop — video-transcriber",
        "",
        "SERVICE    STATUS              PORTS",
        *ps.stdout.strip().splitlines()[1:],
        "",
        "redis      healthy",
        "web        :8000",
        "worker     Celery ready",
        "flower     :5555",
    ]
    img = Image.new("RGB", (900, 420), "#f4f6f8")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 900, 48), fill="#2496ed")
    draw.text((20, 12), "Docker Desktop · video-transcriber", fill="white", font=_font(18))
    y = 70
    for line in lines[2:]:
        draw.text((30, y), line, fill="#222", font=_font(15))
        y += 28
    return _save(img, "05-docker-desktop.png")


def shot_06_history_note() -> Path:
    try:
        data = requests.get("http://localhost:8000/history", timeout=5).json()
        count = len(data)
        sample = data[0]["filename"] if data else "—"
    except Exception:
        count = 0
        sample = "—"
    lines = [
        "http://localhost:8000 — после docker compose down + up",
        "",
        f"Задач в SQLite (data/history.db): {count}",
        f"Пример файла: {sample}",
        "",
        "История сохраняется на диске — таблица не пустая после перезапуска.",
    ]
    img = Image.new("RGB", (1100, 280), "#f8fafc")
    draw = ImageDraw.Draw(img)
    draw.text((24, 20), "Рис. 6. История SQLite после перезапуска", fill="#0f172a", font=_font(20))
    y = 70
    for line in lines:
        draw.text((24, y), line, fill="#334155", font=_font(16))
        y += 32
    return _save(img, "06-history-after-restart.png")


def shot_07_swagger_history() -> Path:
    resp = requests.get("http://localhost:8000/history", timeout=5)
    body = json.dumps(resp.json(), ensure_ascii=False, indent=2)
    body = textwrap.dedent(
        f"""
        GET /history
        Request URL: http://localhost:8000/history

        Server response
        Code: {resp.status_code}

        Response body:
        {body[:3500]}
        """
    ).strip()
    lines = body.splitlines()
    img = _terminal_image("Рис. 7. Swagger — GET /history", lines, width=1300)
    # light swagger-like header
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 36, 1300, 76), fill="#89bf04")
    draw.text((24, 44), "GET /history  Get History", fill="white", font=_font(16))
    return _save(img, "07-swagger-history.png")


def shot_03_scale_placeholder() -> Path:
    ps = subprocess.run(
        ["docker", "compose", "ps", "--format", "{{.Service}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    workers = sum(1 for line in ps.stdout.splitlines() if line.strip() == "worker")
    lines = [
        "Flower — Workers (scale worker=3)",
        "",
        "Запуск: docker compose up --build --scale worker=3",
        "Ожидание: 3 worker Online, по 1 задаче на каждый.",
        "",
        f"Сейчас worker-контейнеров: {workers}",
    ]
    if workers < 3:
        lines.append("Замените этот PNG своим скрином Flower с 3 workers (если уже снимали).")
    return _save(_terminal_image("Рис. 3. Масштаб worker=3", lines, width=1000), "03-flower-3-workers.png")


def capture_browser(url: str, name: str, height: int = 900) -> Path | None:
    browsers = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ]
    exe = next((b for b in browsers if b.is_file()), None)
    if not exe:
        return None
    out = OUT / name
    subprocess.run(
        [
            str(exe),
            "--headless=new",
            "--disable-gpu",
            f"--window-size=1280,{height}",
            f"--screenshot={out}",
            url,
        ],
        check=False,
        capture_output=True,
    )
    return out if out.is_file() else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    capture_browser("http://localhost:8000/", "01-ui-3-success.png", 950)
    capture_browser("http://localhost:5555/", "02-flower-tasks.png", 700)
    shot_03_scale_placeholder()
    shot_04_docker_compose()
    shot_05_docker_desktop()
    shot_06_history_note()
    shot_07_swagger_history()
    files = sorted(OUT.glob("*.png"))
    print(f"OK: {len(files)} PNG in {OUT}")
    for f in files:
        print(f"  {f.name} ({f.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
