from __future__ import annotations

from pydantic import BaseModel, Field

from sipl.ast import (
    AExpr,
    AssignStmt,
    BExpr,
    BinArithOp,
    BinBoolOp,
    BlockStmt,
    CompOp,
    Diagnostic,
    IfStmt,
    IntLiteral,
    NegOp,
    NotOp,
    SeqStmt,
    SkipStmt,
    SourceSpan,
    Stmt,
    VarExpr,
    WhileStmt,
)


class StepLimitExceededError(Exception):
    def __init__(self, max_steps: int, span: SourceSpan) -> None:
        self.diagnostic = Diagnostic(
            code="R001",
            message=f"Execution step limit exceeded ({max_steps} steps)",
            span=span,
        )
        super().__init__(self.diagnostic.message)


class ExecutionResult(BaseModel):
    state: dict[str, int] = Field(default_factory=dict)
    steps: int = 0


class Interpreter:
    def __init__(self, max_steps: int = 10_000) -> None:
        self.max_steps = max_steps
        self._steps = 0
        self._state: dict[str, int] = {}

    def run(self, stmt: Stmt, initial_state: dict[str, int] | None = None) -> ExecutionResult:
        self._steps = 0
        self._state = dict(initial_state) if initial_state else {}
        self._exec_stmt(stmt)
        return ExecutionResult(state=dict(self._state), steps=self._steps)

    def _tick(self, span: SourceSpan) -> None:
        self._steps += 1
        if self._steps > self.max_steps:
            raise StepLimitExceededError(self.max_steps, span)

    def _exec_stmt(self, stmt: Stmt) -> None:
        self._tick(stmt.span)

        match stmt:
            case SkipStmt():
                return
            case AssignStmt(target=target, value=value):
                self._state[target] = self._eval_aexpr(value)
            case SeqStmt(statements=statements):
                for sub_stmt in statements:
                    self._exec_stmt(sub_stmt)
            case BlockStmt(body=body):
                self._exec_stmt(body)
            case IfStmt(condition=cond, then_branch=then_b, else_branch=else_b):
                if self._eval_bexpr(cond):
                    self._exec_stmt(then_b)
                else:
                    self._exec_stmt(else_b)
            case WhileStmt(condition=cond, body=body):
                while self._eval_bexpr(cond):
                    self._exec_stmt(body)
                    self._tick(stmt.span)

    def _eval_aexpr(self, expr: AExpr) -> int:
        match expr:
            case IntLiteral(value=value):
                return value
            case VarExpr(name=name):
                return self._state.get(name, 0)
            case NegOp(operand=operand):
                return -self._eval_aexpr(operand)
            case BinArithOp(op=op, left=left, right=right):
                lv = self._eval_aexpr(left)
                rv = self._eval_aexpr(right)
                if op == "+":
                    return lv + rv
                if op == "-":
                    return lv - rv
                return lv * rv

    def _eval_bexpr(self, expr: BExpr) -> bool:
        match expr:
            case CompOp(op=op, left=left, right=right):
                lv = self._eval_aexpr(left)
                rv = self._eval_aexpr(right)
                if op == "=":
                    return lv == rv
                if op == "!=":
                    return lv != rv
                if op == "<":
                    return lv < rv
                if op == "<=":
                    return lv <= rv
                if op == ">":
                    return lv > rv
                return lv >= rv
            case NotOp(operand=operand):
                return not self._eval_bexpr(operand)
            case BinBoolOp(op=op, left=left, right=right):
                if op == "and":
                    return self._eval_bexpr(left) and self._eval_bexpr(right)
                return self._eval_bexpr(left) or self._eval_bexpr(right)
