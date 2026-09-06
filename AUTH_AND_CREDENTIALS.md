# PostHog Connector — Auth & Credentials Standard

**Compliance:** AUTH_AND_CREDENTIALS_STANDARD.md (B1–B10)

## Схема аутентификации
- **Метод:** Personal API Key (Authorization: Bearer <key>)
- **Хранение:** Секреты сохраняются изолированно в хранилище секретов платформы Imperal.
- **Валидация:** При сохранении ключа выполняется тестовый запрос `GET /api/projects/@current`.
- **Отключение:** Удаление локальных ключей без воздействия на аккаунт вендора.
