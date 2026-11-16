import pytest

from sipl.interpreter import Interpreter, StepLimitExceededError
from sipl.parser import parse_sipl


def test_multiplication_program() -> None:
    code = """
    begin
        R := 0;
        while Y > 0 do
        begin
            R := R + X;
            Y := Y - 1
        end
    end
    """
    ast = parse_sipl(code)
    res = Interpreter().run(ast, initial_state={"X": 6, "Y": 7})
    assert res.state["R"] == 42
    assert res.state["Y"] == 0


def test_factorial_program() -> None:
    code = """
    begin
        RES := 1;
        while N > 1 do
        begin
            RES := RES * N;
            N := N - 1
        end
    end
    """
    res = Interpreter().run(parse_sipl(code), initial_state={"N": 5})
    assert res.state["RES"] == 120


def test_boolean_and_arithmetic_operators() -> None:
    code = """
    A := -5 + 10 * 2;
    if (A >= 15 and not (A = 0)) or (A < 0) then
        OK := 1
    else
        OK := 0;
    if A <= 10 or A != 15 then
        FLAG := 1
    else
        skip
    """
    res = Interpreter().run(parse_sipl(code))
    assert res.state["A"] == 15
    assert res.state["OK"] == 1
    assert res.state.get("FLAG", 0) == 0


def test_infinite_loop_protection() -> None:
    code = "while 1 > 0 do skip"
    ast = parse_sipl(code)
    with pytest.raises(StepLimitExceededError) as exc_info:
        Interpreter(max_steps=50).run(ast)
    assert exc_info.value.diagnostic.code == "R001"
