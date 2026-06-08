# Video Transcriber — ДЗ-10

FastAPI + Celery + Redis + Flower · AI-транscрибатор.

**Полная инструкция:** [`СТАРТ.md`](СТАРТ.md)

```powershell
copy .env.example .env
docker compose up --build
```

| URL | Назначение |
|-----|------------|
| http://localhost:8000 | Загрузка + статусы |
| http://localhost:5555 | Flower |
| http://localhost:8000/docs | Swagger |

**Масштаб:** `docker compose up --build --scale worker=3`

---

Документация: `СТАРТ.md` (быстро) · `DZ-10_РУКОВОДСТВО_И_ПЗ.md` (полное ПЗ)  
Связь с проектами: ДЗ-9 CRM · EDU · Tilda — `TODO_ROADMAP.md`
