# Video Transcriber — безопасность

**Проект:** ДЗ-10 · FastAPI + Celery + Redis  
**Не production** — учебный локальный стек.

---

## Чеклист

### Сдача ДЗ-10

- [x] `.env` в `.gitignore`
- [x] `OPENAI_API_KEY` только в `.env`, не в коде
- [x] Проверка размера файла (25 МБ) на клиенте и сервере
- [ ] Скрины в `DZ-10_отчёт_для_сдачи.docx`
- [ ] На скринах нет API-ключа

### Перед prod / EDU

- [ ] HTTPS, не открывать Redis наружу
- [ ] Rate limit на `/transcribe`
- [ ] Auth (JWT / Supabase) — переиспользовать паттерн ДЗ-9
- [ ] Очистка `uploads/` по TTL
- [ ] Secret scan в CI

---

## Секреты

| Переменная | Где |
|------------|-----|
| `OPENAI_API_KEY` | `.env` only |
| Redis | внутри Docker-сети, порт 6379 не наружу |

---

*ДЗ-10 · video-transcriber*
