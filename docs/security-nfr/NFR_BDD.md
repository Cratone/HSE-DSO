# BDD приемка — Security NFR

Feature: Хранение паролей Argon2id
  Scenario: Пароли хэшируются только с Argon2id с параметрами
    Given сервис развернут в тестовом окружении
    When создается новый пользователь с паролем "Secret123!"
    Then пароль в базе отсутствует в открытом виде
    And алгоритм хэширования равен "argon2id"
    And параметры соответствуют: t=3, m=256MB, p=1

Feature: Owner-only доступ к рецептам
  Scenario: Пользователь не может читать чужой рецепт
    Given существуют пользователи Alice (id=1) и Bob (id=2) и рецепт R1, принадлежащий Alice
    And Bob аутентифицирован и имеет валидный JWT
    When Bob запрашивает GET /recipes/{R1.id}
    Then ответ имеет статус 404 или 403
    And тело содержит error.code in ["not_found", "forbidden"]

  Scenario: Пользователь может обновлять только свои рецепты
    Given Alice аутентифицирована и имеет рецепт R2, принадлежащий Alice
    When Alice отправляет PATCH /recipes/{R2.id} c валидными полями
    Then ответ 200 и изменения применены

Feature: Валидация единиц измерения
  Scenario: Создание ингредиента с недопустимой единицей отклоняется
    Given список разрешенных units: g, kg, ml, l, tsp, tbsp, pcs
    When выполняется POST /recipes/{id}/ingredients с unit="pound"
    Then ответ 422
    And body.error.code == "validation_error"

Feature: Производительность поиска по ингредиенту
  Scenario: p95 ответа на поиск держится под порогом на stage
    Given сервис развернут на stage и фоновые данные (≥1000 рецептов)
    And генерируется нагрузка 30 RPS на GET /recipes?ingredient=tomato в течение 5 минут
    When завершается прогон нагрузочного теста
    Then p95 времени ответа ≤ 200 миллисекунд

Feature: Ограничение скорости на мутации
  Scenario: Превышение лимита ведет к 429
    Given лимит 100 запросов в минуту на пользователя/IP для POST/PATCH/DELETE
    When один клиент отправляет 150 POST /ingredients за 60 секунд
    Then не менее 50 ответов имеют статус 429
    And тело ошибки содержит error.code == "rate_limited"
