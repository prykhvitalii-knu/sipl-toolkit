import pytest

from sipl.ast import AssignStmt, SeqStmt, SourceSpan, WhileStmt
from sipl.parser import SiplSyntaxError, parse_sipl

VALID_PROGRAMS = [
    # 1. Простий skip
    "skip",
    # 2. Присвоювання константи
    "X := 42",
    # 3. Арифметика з пріоритетом операцій
    "R := 1 + 2 * 3 - 4",
    # 4. Унарний мінус та дужки
    "Z := -(X + Y) * 2",
    # 5. Послідовність операторів
    "X := 1; Y := 2; Z := X + Y",
    # 6. Блок begin/end
    "begin X := 10; Y := 20 end",
    # 7. Умовний оператор if-then-else
    "if X > 0 then Y := 1 else Y := 0",
    # 8. Складна булева умова (and, or, not)
    "if not (X = 0) and (Y >= 1 or Z != 5) then skip else X := 0",
    # 9. Класичний приклад множення з методички
    """
    begin
        R := 1;
        while Y > 0 do
        begin
            R := R * X;
            Y := Y - 1
        end
    end
    """,
    # 10. Коментарі різних стилів
    """
    // Ініціалізація змінних
    A := 5; # коментар у рядку
    B := A * 2
    """,
]

INVALID_PROGRAMS = [
    # 1. Порожній файл
    "",
    # 2. Лише пробіли та коментарі
    "   // just comment\n  ",
    # 3. Знак = замість := у присвоюванні
    "X = 10",
    # 4. Зайва крапка з комою перед end
    "begin X := 1; end",
    # 5. Незакритий блок begin
    "begin X := 1; Y := 2",
    # 6. Відсутня гілка else (за БНФ SIPL if має повну форму)
    "if X > 0 then X := 1",
    # 7. Цикл while без ключового слова do
    "while X > 0 X := X - 1",
    # 8. Некоректне ім'я змінної (починається з цифри)
    "1var := 10",
    # 9. Незакрита дужка у виразі
    "X := (1 + 2 * 3",
    # 10. Пропущений операнд
    "X := 5 + * 2",
]


@pytest.mark.parametrize("code", VALID_PROGRAMS)
def test_valid_sipl_programs(code: str) -> None:
    ast = parse_sipl(code)
    assert ast.span.start_line >= 1
    assert ast.span.start_col >= 1


@pytest.mark.parametrize("code", INVALID_PROGRAMS)
def test_invalid_sipl_programs(code: str) -> None:
    with pytest.raises(SiplSyntaxError) as exc_info:
        parse_sipl(code)
    assert exc_info.value.diagnostic.severity == "error"
    assert exc_info.value.diagnostic.span is not None


def test_ast_structure_and_spans() -> None:
    code = "X := 10;\nwhile X > 0 do X := X - 1"
    ast = parse_sipl(code)
    assert isinstance(ast, SeqStmt)
    assert len(ast.statements) == 2

    first, second = ast.statements
    assert isinstance(first, AssignStmt)
    assert first.target == "X"
    assert first.span == SourceSpan(start_line=1, start_col=1, end_line=1, end_col=8)

    assert isinstance(second, WhileStmt)
    assert second.span.start_line == 2