# Video Transcriber → развитие (TODO)

**Статус:** ДЗ-10 выполнено локально  
**Каркас:** FastAPI + Celery + Redis + Flower + Docker

---

## Фаза 0 — ДЗ-10 ✅

- [x] 4 сервиса в docker-compose
- [x] OpenAI + local Whisper
- [x] Flower (тот же образ, что worker) — :5555 отвечает HTTP 200
- [x] Проверка 25 МБ
- [ ] GitHub + отчёт Word
- [ ] Скрины: :8000, Flower, scale worker=3

---

## Фаза 1 — EDU (AIKIVAVIORA)

| TODO | Описание |
|------|----------|
| [ ] Транскрипт лекции → урок | POST /transcribe из админки EDU |
| [ ] Связь с dzen-rag | текст → индекс для чата по курсу |
| [ ] Supabase | хранить task_id, transcript, user_id |
| [ ] RLS | студент видит только свои транскрипты |

**Переиспользовать:** `designstudio-crm` auth + этот Celery-стек.

---

## Фаза 2 — CRM + Tilda

| TODO | Описание |
|------|----------|
| [ ] Webhook Tilda | видео-отзыв → очередь transcribe |
| [ ] Лид + транскрипт | в `leads.notes` или отдельная таблица |

---

## Фаза 3 — Prod

- [ ] Deploy: Railway / VPS + managed Redis
- [ ] S3 для uploads вместо локальной папки
- [ ] FFmpeg-сжатие перед Whisper (>25 МБ)
- [ ] CI: docker build + pytest

---

## Фаза 4 — UX

- [ ] Прогресс-бар (Celery PROGRESS)
- [ ] Скачать .txt
- [ ] Telegram-бот «пришли голосовое → текст»

---

*Обновлять по мере решений.*
