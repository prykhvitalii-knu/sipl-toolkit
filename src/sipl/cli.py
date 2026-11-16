from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import BaseModel, Field

from sipl.ast import Diagnostic
from sipl.interpreter import Interpreter, StepLimitExceededError
from sipl.parser import SiplSyntaxError, parse_sipl

app = typer.Typer(
    name="sipl",
    help="SIPL Language Toolkit CLI: parse, check, and execute SIPL programs.",
    add_completion=False,
)


class CliResponse(BaseModel):
    ok: bool
    command: str
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    result: Any = None


def _emit(response: CliResponse, as_json: bool, exit_code: int) -> None:
    if as_json:
        typer.echo(response.model_dump_json(indent=2))
    else:
        if response.ok:
            typer.echo(f"[OK] {response.command}: {response.result}")
        else:
            for diag in response.diagnostics:
                loc = (
                    f" (line {diag.span.start_line}, col {diag.span.start_col})"
                    if diag.span
                    else ""
                )
                typer.secho(f"[{diag.code}]{loc}: {diag.message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=exit_code)


def _read_source(file: Path, command: str, as_json: bool) -> str:
    if not file.exists() or not file.is_file():
        _emit(
            CliResponse(
                ok=False,
                command=command,
                diagnostics=[Diagnostic(code="IO01", message=f"File not found: {file}")],
            ),
            as_json=as_json,
            exit_code=1,
        )
    return file.read_text(encoding="utf-8")


def _parse_vars(vars_list: list[str], command: str, as_json: bool) -> dict[str, int]:
    state: dict[str, int] = {}
    for item in vars_list:
        if "=" not in item:
            _emit(
                CliResponse(
                    ok=False,
                    command=command,
                    diagnostics=[
                        Diagnostic(
                            code="CLI01", message=f"Invalid --var format '{item}', expected KEY=INT"
                        )
                    ],
                ),
                as_json=as_json,
                exit_code=1,
            )
        key, raw_val = item.split("=", 1)
        try:
            state[key.strip()] = int(raw_val.strip())
        except ValueError:
            _emit(
                CliResponse(
                    ok=False,
                    command=command,
                    diagnostics=[
                        Diagnostic(code="CLI02", message=f"Variable '{key}' must be an integer")
                    ],
                ),
                as_json=as_json,
                exit_code=1,
            )
    return state


@app.command()
def check(
    file: Annotated[Path, typer.Argument(help="Path to .sipl source file")],
    as_json: Annotated[bool, typer.Option("--json", help="Output structured JSON")] = False,
) -> None:
    """Validate syntax of a SIPL program."""
    source = _read_source(file, "check", as_json)
    try:
        parse_sipl(source)
    except SiplSyntaxError as exc:
        _emit(
            CliResponse(ok=False, command="check", diagnostics=[exc.diagnostic]),
            as_json=as_json,
            exit_code=1,
        )
    _emit(
        CliResponse(ok=True, command="check", result={"valid": True}), as_json=as_json, exit_code=0
    )


@app.command()
def parse(
    file: Annotated[Path, typer.Argument(help="Path to .sipl source file")],
    as_json: Annotated[bool, typer.Option("--json", help="Output structured JSON")] = False,
) -> None:
    """Parse a SIPL program and output its typed AST."""
    source = _read_source(file, "parse", as_json)
    try:
        ast = parse_sipl(source)
    except SiplSyntaxError as exc:
        _emit(
            CliResponse(ok=False, command="parse", diagnostics=[exc.diagnostic]),
            as_json=as_json,
            exit_code=1,
        )
    _emit(
        CliResponse(ok=True, command="parse", result=ast.model_dump()),
        as_json=as_json,
        exit_code=0,
    )


@app.command()
def run(
    file: Annotated[Path, typer.Argument(help="Path to .sipl source file")],
    var: Annotated[
        list[str] | None,
        typer.Option("--var", "-v", help="Initial variable value in KEY=INT format"),
    ] = None,
    max_steps: Annotated[
        int, typer.Option("--max-steps", help="Maximum execution steps before aborting")
    ] = 10_000,
    as_json: Annotated[bool, typer.Option("--json", help="Output structured JSON")] = False,
) -> None:
    """Execute a SIPL program and output final variable state."""
    source = _read_source(file, "run", as_json)
    initial_state = _parse_vars(var or [], "run", as_json)

    try:
        ast = parse_sipl(source)
    except SiplSyntaxError as exc:
        _emit(
            CliResponse(ok=False, command="run", diagnostics=[exc.diagnostic]),
            as_json=as_json,
            exit_code=1,
        )

    interpreter = Interpreter(max_steps=max_steps)
    try:
        exec_res = interpreter.run(ast, initial_state=initial_state)
    except StepLimitExceededError as exc:
        _emit(
            CliResponse(ok=False, command="run", diagnostics=[exc.diagnostic]),
            as_json=as_json,
            exit_code=2,
        )

    _emit(
        CliResponse(ok=True, command="run", result=exec_res.model_dump()),
        as_json=as_json,
        exit_code=0,
    )
