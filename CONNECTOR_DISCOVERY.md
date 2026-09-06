# PostHog Connector — Connector Discovery

**Vendor API Baseline:** https://posthog.com

## Архитектура API
- **Базовый адрес:** `https://app.posthog.com/api`
- **Протокол:** REST / HTTPS (JSON)
- **Аутентификация:** Personal API Key (Authorization: Bearer <key>)
- **Ключевые эндпоинты:**
  - проекты (/projects)
  - события (/events)
  - когорты (/cohorts)
  - инсайты (/insights)
  - записи сессий (/session_recordings)
- **Тестовая точка проверки подключения:** `GET /api/projects/@current`.
