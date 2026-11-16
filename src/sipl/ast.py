from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SourceSpan(BaseModel):
    start_line: int
    start_col: int
    end_line: int
    end_col: int


class Diagnostic(BaseModel):
    severity: Literal["error", "warning"] = "error"
    code: str
    message: str
    span: SourceSpan | None = None


class ASTNode(BaseModel):
    span: SourceSpan


# --- Арифметичні вирази ---


class IntLiteral(ASTNode):
    kind: Literal["int"] = "int"
    value: int


class VarExpr(ASTNode):
    kind: Literal["var"] = "var"
    name: str


class NegOp(ASTNode):
    kind: Literal["neg"] = "neg"
    operand: AExpr


class BinArithOp(ASTNode):
    kind: Literal["arith_op"] = "arith_op"
    op: Literal["+", "-", "*"]
    left: AExpr
    right: AExpr


AExpr = IntLiteral | VarExpr | NegOp | BinArithOp


# --- Булеві вирази ---


class CompOp(ASTNode):
    kind: Literal["comp_op"] = "comp_op"
    op: Literal["=", "!=", "<", "<=", ">", ">="]
    left: AExpr
    right: AExpr


class NotOp(ASTNode):
    kind: Literal["not"] = "not"
    operand: BExpr


class BinBoolOp(ASTNode):
    kind: Literal["bool_op"] = "bool_op"
    op: Literal["and", "or"]
    left: BExpr
    right: BExpr


BExpr = CompOp | NotOp | BinBoolOp


# --- Оператори ---


class SkipStmt(ASTNode):
    kind: Literal["skip"] = "skip"


class AssignStmt(ASTNode):
    kind: Literal["assign"] = "assign"
    target: str
    value: AExpr


class SeqStmt(ASTNode):
    kind: Literal["seq"] = "seq"
    statements: list[Stmt] = Field(min_length=2)


class BlockStmt(ASTNode):
    kind: Literal["block"] = "block"
    body: Stmt


class IfStmt(ASTNode):
    kind: Literal["if"] = "if"
    condition: BExpr
    then_branch: Stmt
    else_branch: Stmt


class WhileStmt(ASTNode):
    kind: Literal["while"] = "while"
    condition: BExpr
    body: Stmt


Stmt = SkipStmt | AssignStmt | SeqStmt | BlockStmt | IfStmt | WhileStmt
