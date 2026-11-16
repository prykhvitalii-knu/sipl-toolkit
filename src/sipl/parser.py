from __future__ import annotations

from functools import reduce
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal, cast

from lark import Lark, Token, Transformer, v_args
from lark.exceptions import LarkError, UnexpectedInput
from lark.tree import Meta

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


class SiplSyntaxError(Exception):
    def __init__(self, diagnostic: Diagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)


def _meta_to_span(meta: Meta) -> SourceSpan:
    return SourceSpan(
        start_line=meta.line,
        start_col=meta.column,
        end_line=meta.end_line,
        end_col=meta.end_column,
    )


def _token_to_span(tok: Token) -> SourceSpan:
    return SourceSpan(
        start_line=tok.line or 1,
        start_col=tok.column or 1,
        end_line=tok.end_line or tok.line or 1,
        end_col=tok.end_column or (tok.column or 1) + len(tok.value),
    )


def _merge_spans(first: SourceSpan, last: SourceSpan) -> SourceSpan:
    return SourceSpan(
        start_line=first.start_line,
        start_col=first.start_col,
        end_line=last.end_line,
        end_col=last.end_col,
    )


@v_args(meta=True)
class _AstBuilder(Transformer[Token, Stmt]):
    def seq_stmt(self, meta: Meta, children: list[Stmt]) -> Stmt:
        if len(children) == 1:
            return children[0]
        return SeqStmt(span=_meta_to_span(meta), statements=children)

    def skip_stmt(self, meta: Meta, _children: list[Any]) -> SkipStmt:
        return SkipStmt(span=_meta_to_span(meta))

    def assign_stmt(self, meta: Meta, children: list[Any]) -> AssignStmt:
        ident: Token = children[0]
        expr: AExpr = children[1]
        return AssignStmt(span=_meta_to_span(meta), target=str(ident), value=expr)

    def block_stmt(self, meta: Meta, children: list[Any]) -> BlockStmt:
        return BlockStmt(span=_meta_to_span(meta), body=children[0])

    def if_stmt(self, meta: Meta, children: list[Any]) -> IfStmt:
        return IfStmt(
            span=_meta_to_span(meta),
            condition=children[0],
            then_branch=children[1],
            else_branch=children[2],
        )

    def while_stmt(self, meta: Meta, children: list[Any]) -> WhileStmt:
        return WhileStmt(
            span=_meta_to_span(meta),
            condition=children[0],
            body=children[1],
        )

    def or_expr(self, _meta: Meta, children: list[BExpr]) -> BExpr:
        return reduce(
            lambda acc, item: BinBoolOp(
                span=_merge_spans(acc.span, item.span), op="or", left=acc, right=item
            ),
            children,
        )

    def and_expr(self, _meta: Meta, children: list[BExpr]) -> BExpr:
        return reduce(
            lambda acc, item: BinBoolOp(
                span=_merge_spans(acc.span, item.span), op="and", left=acc, right=item
            ),
            children,
        )

    def not_op(self, meta: Meta, children: list[Any]) -> NotOp:
        return NotOp(span=_meta_to_span(meta), operand=children[0])

    def comp_op(self, meta: Meta, children: list[Any]) -> CompOp:
        op_tok: Token = children[1]
        op = cast(Literal["=", "!=", "<", "<=", ">", ">="], str(op_tok))
        return CompOp(span=_meta_to_span(meta), op=op, left=children[0], right=children[2])

    def add_op(self, meta: Meta, children: list[Any]) -> BinArithOp:
        return BinArithOp(span=_meta_to_span(meta), op="+", left=children[0], right=children[1])

    def sub_op(self, meta: Meta, children: list[Any]) -> BinArithOp:
        return BinArithOp(span=_meta_to_span(meta), op="-", left=children[0], right=children[1])

    def mul_op(self, meta: Meta, children: list[Any]) -> BinArithOp:
        return BinArithOp(span=_meta_to_span(meta), op="*", left=children[0], right=children[1])

    def neg_op(self, meta: Meta, children: list[Any]) -> NegOp:
        return NegOp(span=_meta_to_span(meta), operand=children[0])

    def int_literal(self, _meta: Meta, children: list[Any]) -> IntLiteral:
        tok: Token = children[0]
        return IntLiteral(span=_token_to_span(tok), value=int(tok.value))

    def var_expr(self, _meta: Meta, children: list[Any]) -> VarExpr:
        tok: Token = children[0]
        return VarExpr(span=_token_to_span(tok), name=str(tok.value))


def _load_grammar() -> str:
    local_path = Path(__file__).resolve().parents[2] / "grammar" / "sipl.lark"
    if local_path.exists():
        return local_path.read_text(encoding="utf-8")
    return files("sipl.grammar").joinpath("sipl.lark").read_text(encoding="utf-8")


_PARSER = Lark(
    _load_grammar(),
    parser="lalr",
    propagate_positions=True,
    maybe_placeholders=False,
)


def parse_sipl(source: str) -> Stmt:
    if not source.strip():
        raise SiplSyntaxError(
            Diagnostic(
                code="E001",
                message="Empty SIPL program",
                span=SourceSpan(start_line=1, start_col=1, end_line=1, end_col=1),
            )
        )
    try:
        tree = _PARSER.parse(source)
        return _AstBuilder().transform(tree)
    except UnexpectedInput as exc:
        line = getattr(exc, "line", 1)
        col = getattr(exc, "column", 1)
        context = exc.get_context(source, span=40).strip()
        raise SiplSyntaxError(
            Diagnostic(
                code="E002",
                message=f"Syntax error at line {line}, column {col}:\n{context}",
                span=SourceSpan(
                    start_line=line,
                    start_col=col,
                    end_line=line,
                    end_col=col + 1,
                ),
            )
        ) from exc
    except LarkError as exc:
        raise SiplSyntaxError(Diagnostic(code="E003", message=f"Parse error: {exc}")) from exc
