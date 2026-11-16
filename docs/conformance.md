# SIPL Conformance Suite Specification

Conformance Suite призначений для незалежної верифікації будь-якої реалізації інтерпретатора та парсера мови SIPL через стандартний CLI-інтерфейс.

## Інтерфейс сумісності (CLI Contract)

Тестований бінарник задається змінною середовища `SIPL_CMD` (за замовчуванням `sipl`).
Раннер викликає:
- `<SIPL_CMD> parse <file.sipl> --json`
- `<SIPL_CMD> run <file.sipl> [--var K=V ...] [--max-steps N] --json`

### Очікуваний JSON-формат відповіді

```json
{
  "ok": true,
  "command": "run",
  "diagnostics": [],
  "result": {
    "state": { "R": 42 },
    "steps": 15
  }
}