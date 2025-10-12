## Диаграмма
```mermaid
flowchart LR
  subgraph Client[Trust Boundary: Client]
    U[User/Browser]
  end
  subgraph Edge[Trust Boundary: Edge]
    API[FastAPI Service]
  end
  subgraph Core[Trust Boundary: Core]
    AUTH[Auth Subsystem]
    REC[Recipes Module]
  end
  subgraph Data[Trust Boundary: Data]
    DB[(PostgreSQL: users, recipes, ingredients, recipe_ingredients)]
    SECRET[["Secret Store (JWT secret)"]]
  end

  U -->|F1: HTTPS login creds| API
  API -->|F2: verify password| AUTH
  AUTH -->|F3: argon2id verify| DB
  AUTH -->|F4: read JWT secret| SECRET
  API -->|F5: issue JWT| U
  U -->|"F6: HTTPS CRUD recipes/ingredients (JWT)"| API
  API -->|F7: owner-only checks + queries| REC
  REC -->|F8: read/write| DB
```

## Список потоков
| ID | Откуда → Куда | Канал/Протокол | Данные/PII | Комментарий |
|----|---------------|-----------------|------------|-------------|
| F1 | User → API    | HTTPS           | Логин/пароль | Аутентификация пользователя |
| F2 | API → AUTH    | In-Proc/Call    | userId/hash | Вызов подсистемы аутентификации |
| F3 | AUTH → DB     | TCP             | хэш пароля  | Проверка hash (argon2id) |
| F4 | AUTH → SECRET | Local/SDK       | секрет JWT  | Чтение секрета из Secret Store |
| F5 | API → User    | HTTPS           | JWT         | Выдача токена |
| F6 | User → API    | HTTPS           | JWT + payload | CRUD /recipes, /ingredients, /recipes?ingredient= |
| F7 | API → REC     | In-Proc/Call    | userId, recipeId | Owner-only проверка/бизнес-логика |
| F8 | REC → DB      | TCP             | данные рецептов | Запросы/модификации данных |
