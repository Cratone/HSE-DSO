# Recipe Box API

[![CI](https://github.com/Cratone/HSE-DSO/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Cratone/HSE-DSO/actions/workflows/ci.yml)

Менеджер рецептов с ингредиентами и безопасными контролями.

## Требования окружения
- Python >= 3.11
- Poetry/pip + virtualenv (рекомендуется)
- Установленный `uvicorn` для локального запуска

## Установка
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # PowerShell / Windows
pip install -r requirements.txt -r requirements-dev.txt
```

## Конфигурация
- Бэкенд сессий по умолчанию — in-memory. Для продакшена используйте Redis: `SESSION_BACKEND=redis`, `REDIS_URL=redis://<host>:6379/0`, `SESSION_TTL_SECONDS`.
- Зарегистрируйте пользователя через `POST /auth/register`, затем выполните `POST /auth/login` и сохраните `access_token`.
- Все защищённые эндпоинты ожидают заголовок `Authorization: Bearer <access_token>`.

## Контейнеризация
```bash
docker build -t recipe-box:local .
docker run --rm -p 8000:8000 \
	-e SESSION_BACKEND=redis -e REDIS_URL=redis://host.docker.internal:6379/0 \
	recipe-box:local
```

### Локальный стек через Docker Compose
```bash
docker compose up --build
```

- `compose.yaml` поднимает API и Redis, включает healthchecks и автоматический рестарт.
- Контейнер приложения запускается под non-root (UID 10001), rootfs read-only, `tmpfs` смонтирован только для `/tmp`, все Linux capabilities сброшены, `no-new-privileges` включён.

### Профили безопасности

- **Seccomp:** по умолчанию контейнер получает профиль `docker/security/seccomp/recipe-box-default.json`, который запрещает `clone3`, `bpf`, `io_uring_*`, операции монтирования и другие опсные syscalls. Можно указать альтернативный путь: `export APP_SECCOMP_PROFILE=/full/path/to/profile.json` (Linux/macOS) или `set APP_SECCOMP_PROFILE=unconfined` (cmd) / `$env:APP_SECCOMP_PROFILE="unconfined"` (PowerShell).
- **AppArmor:** Docker Desktop/WSL автоматически применяет `docker-default`. Для усиленного режима загрузите профиль `docker/security/apparmor/recipe-box.profile` на Linux-хосте: `sudo apparmor_parser -r docker/security/apparmor/recipe-box.profile`, затем `export APP_APPARMOR_PROFILE=recipe-box`. Если AppArmor недоступен, нужно установить `APP_APPARMOR_PROFILE=unconfined` или `$env:APP_APPARMOR_PROFILE="unconfined"`.

## Запуск
```bash
uvicorn app.main:app --reload
```

Проверка работоспособности: `GET /health` → `{ "status": "ok" }`.

## API
- `POST /auth/register` — регистрация пользователя (валидация email + пароль ≥8 символов, буквы и цифры).
- `POST /auth/login` — выдача bearer-токена.
- `GET /auth/me` — информация о текущем пользователе.
- `POST /ingredients` — создать ингредиент (имя 1..100 символов, уникальность без учёта регистра).
- `GET /ingredients` / `GET /ingredients/{id}` — чтение справочника.
- `POST /recipes` — создать рецепт с шагами и до 100 ингредиентов.
- `GET /recipes?ingredient=name` — список рецептов владельца, фильтрация по названию ингредиента (case-insensitive).
- `PATCH /recipes/{id}` — частичное обновление (нельзя отправлять пустое тело).
- `DELETE /recipes/{id}` — удаление. CRUD открыт только владельцу (owner-id определяется по токену).

Ответы об ошибках стандартизированы в формате RFC 7807 (см. `app/errors.py`).

## Swagger UI
- Откройте `http://localhost:8000/docs`, зарегистрируйте пользователя и выполните `POST /auth/login` прямо из UI.
- Скопируйте `access_token`, нажмите **Authorize** (HTTP Bearer) и вставьте токен (без префикса `Bearer`).
- После авторизации Swagger автоматически добавит заголовок `Authorization` ко всем вызовам.

## Тесты и качество
```bash
ruff check --fix . && black . && isort .
pytest -q
pre-commit run --all-files
```

Негативные тесты покрывают отсутствие заголовков авторизации, попытки Path/IDOR, а также валидацию доменных ограничений (см. `tests/test_api_security.py`, `tests/test_recipes_api.py`).

## Безопасность
- Строгие Pydantic-модели (Decimal для количеств, `extra='forbid'`, очистка строк).
- RFC 7807 ответы с `correlation_id` и маскировкой внутренних ошибок.
- Секреты берутся только из окружения, API-ключ не логируется/не хардкодится.
- Вся бизнес-логика привязана к владельцу, определяемому по bearer-токену, что предотвращает IDOR.
- Сессионные токены могут храниться в Redis с TTL, что позволяет горизонтально масштабировать API и быстро инвалидавать токены.

## Лицензия
MIT
