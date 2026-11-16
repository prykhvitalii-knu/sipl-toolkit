import json
from pathlib import Path

from typer.testing import CliRunner

from sipl.cli import app

runner = CliRunner()


def test_cli_check_valid_and_invalid(tmp_path: Path) -> None:
    valid_file = tmp_path / "ok.sipl"
    valid_file.write_text("X := 10; Y := X + 5", encoding="utf-8")

    res_ok = runner.invoke(app, ["check", str(valid_file), "--json"])
    assert res_ok.exit_code == 0
    payload_ok = json.loads(res_ok.stdout)
    assert payload_ok["ok"] is True

    bad_file = tmp_path / "bad.sipl"
    bad_file.write_text("X = 10", encoding="utf-8")

    res_bad = runner.invoke(app, ["check", str(bad_file), "--json"])
    assert res_bad.exit_code == 1
    payload_bad = json.loads(res_bad.stdout)
    assert payload_bad["ok"] is False
    assert payload_bad["diagnostics"][0]["span"]["start_line"] == 1


def test_cli_parse_json(tmp_path: Path) -> None:
    src = tmp_path / "prog.sipl"
    src.write_text("X := 1", encoding="utf-8")

    res = runner.invoke(app, ["parse", str(src), "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["result"]["kind"] == "assign"
    assert data["result"]["target"] == "X"


def test_cli_run_with_vars_and_step_limit(tmp_path: Path) -> None:
    gcd = Path("examples/gcd.sipl")
    res = runner.invoke(app, ["run", str(gcd), "--var", "A=48", "--var", "B=18", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["result"]["state"]["A"] == 6

    inf_file = tmp_path / "inf.sipl"
    inf_file.write_text("while 1 = 1 do skip", encoding="utf-8")
    res_inf = runner.invoke(app, ["run", str(inf_file), "--max-steps", "20", "--json"])
    assert res_inf.exit_code == 2
    err_data = json.loads(res_inf.stdout)
    assert err_data["diagnostics"][0]["code"] == "R001"


def test_cli_missing_file_and_bad_var(tmp_path: Path) -> None:
    res_missing = runner.invoke(app, ["check", str(tmp_path / "none.sipl"), "--json"])
    assert res_missing.exit_code == 1

    valid_file = tmp_path / "ok.sipl"
    valid_file.write_text("skip", encoding="utf-8")
    res_bad_var = runner.invoke(app, ["run", str(valid_file), "--var", "BROKEN", "--json"])
    assert res_bad_var.exit_code == 1
