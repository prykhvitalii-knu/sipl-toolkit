from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

CONFORMANCE_DIR = Path(__file__).resolve().parents[1] / "conformance"


def _load_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for yaml_file in sorted(CONFORMANCE_DIR.glob("*.yaml")):
        loaded = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            cases.extend(loaded)
    return cases


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: str(c["id"]))
def test_conformance_case(case: dict[str, Any], tmp_path: Path) -> None:
    sipl_cmd = shlex.split(os.environ.get("SIPL_CMD", "uv run sipl"))
    src_file = tmp_path / f"{case['id']}.sipl"
    src_file.write_text(case["source"], encoding="utf-8")

    cmd = [*sipl_cmd, case["command"], str(src_file), "--json"]

    for k, v in case.get("vars", {}).items():
        cmd.extend(["--var", f"{k}={v}"])

    if "max_steps" in case:
        cmd.extend(["--max-steps", str(case["max_steps"])])

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert proc.returncode == case["expected_exit_code"], (
        f"Unexpected exit code {proc.returncode}. stderr: {proc.stderr}"
    )

    payload = json.loads(proc.stdout)

    if case["expected_exit_code"] == 0:
        assert payload["ok"] is True
        if case["command"] == "parse" and "expected_ast_kind" in case:
            assert payload["result"]["kind"] == case["expected_ast_kind"]
        if case["command"] == "run" and "expected_state" in case:
            assert payload["result"]["state"] == case["expected_state"]
    else:
        assert payload["ok"] is False
        if "expected_error_code" in case:
            codes = [d["code"] for d in payload["diagnostics"]]
            assert case["expected_error_code"] in codes