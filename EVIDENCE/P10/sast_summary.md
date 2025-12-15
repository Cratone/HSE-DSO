# Итоги P10 — SAST & Secrets

## Semgrep
- Профиль: `p/ci` + проектные правила из `security/semgrep/rules.yml`.
- Команда: `semgrep ci --config p/ci --config security/semgrep/rules.yml --sarif --output EVIDENCE/P10/semgrep.sarif --metrics=off`.
- Результат: 0 предупреждений после фикса.
- Принятые меры: правило `recipebox-avoid-traceback-print` подсветило прямой вызов `traceback.print_exc()` в `app/main.py`. Исправлено заменой на структурированное логирование через `logging`, чтобы не утащить стек-трейсы в stdout.

## Gitleaks
- Команда: `gitleaks detect --no-banner --config=security/.gitleaks.toml --source=. --report-format=json --report-path=EVIDENCE/P10/gitleaks.json`.
- Результат: 0 инцидентов.
- Allowlist: шаблон `Str0ngPass123` + прочие тестовые пароли вынесены в `security/.gitleaks.toml`, потому что дефолтные правила воспринимают их как секреты, хотя это фикстуры из `tests/test_auth.py`.

## Дальнейшие шаги
- Поддерживать правило по количеству итераций PBKDF2 (`recipebox-pbkdf2-iteration-policy`) при изменении криптополитики.
- Использовать артефакты `EVIDENCE/P10/*.sarif|json` в GitHub Actions и в дальнейшем отчёте по безопасности.
