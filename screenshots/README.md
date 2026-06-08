# Скрины для `DZ-10_отчёт_для_сдачи.docx`

Сохраните PNG в эту папку **с такими именами** — скрипт `build_docx_dz10.py` вставит их автоматически.

| Файл | Что снять | Подпись в Word |
|------|-----------|----------------|
| `01-ui-3-success.png` | :8000 — 3 SUCCESS + текст | Рис. 1. Транскрибация |
| `02-flower-tasks.png` | Flower — Succeeded: 3 | Рис. 2. Flower |
| `03-flower-3-workers.png` | Flower — 3 workers (scale) | Рис. 3. Масштаб worker=3 |
| `04-docker-compose.png` | Терминал `docker compose up --build` | Рис. 4. Запуск |
| `05-docker-desktop.png` | Docker Desktop — 4+ контейнера | Рис. 5. Docker |
| `06-history-after-restart.png` | :8000 после down/up — история SQLite | Рис. 6. История (опц.) |
| `07-swagger-history.png` | Swagger GET /history — не пустой | Рис. 7. API (опц.) |

Пересборка Word:

```powershell
python build_docx_dz10.py
```

Скрины **не коммитятся** в git (см. `.gitignore`) — только для локального отчёта.
