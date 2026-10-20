# -*- coding: utf-8 -*-
import json

import pytest

from mojibake_forensics import __version__
from mojibake_forensics import cli
from mojibake_forensics import report


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


@pytest.mark.parametrize("command", ["attr", "explain", "recover", "file", "scan"])
def test_subcommand_help(command, capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main([command, "--help"])
    assert excinfo.value.code == 0
    assert "usage:" in capsys.readouterr().out.lower()


def test_attr_is_no_longer_not_ready(capsys):
    """M2 retires exit code 4 for attr; the envelope is a real candidate list."""
    code = cli.main(["attr", "--text", "é›…", "--json"])
    assert code == report.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "candidates"
    assert payload["command"] == "attr"
    assert "milestone" not in payload
    assert payload["schema"] == "mojibake-forensics/1"
    assert payload["criteria"]["max_depth"] == 3
    assert isinstance(payload["candidates"], list)


def test_recover_is_no_longer_not_ready(capsys):
    """M4 retires exit code 4 for recover; the envelope is a real verdict."""
    code = cli.main(["recover", "--text", "é›…", "--pick", "1", "--json"])
    assert code == report.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "recovered"
    assert payload["command"] == "recover"
    assert "milestone" not in payload
    assert payload["schema"] == "mojibake-forensics/1"
    assert payload["recovered"] == "雅"
    assert payload["verify"] is True


def test_explain_is_no_longer_not_ready(capsys):
    """M3 retires exit code 4 for explain; the envelope carries a real proof."""
    code = cli.main(["explain", "--text", "é›…", "--pick", "1", "--json"])
    assert code == report.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["command"] == "explain"
    assert "milestone" not in payload
    assert payload["schema"] == "mojibake-forensics/1"
    assert payload["proofs"][0]["verify"] is True


@pytest.mark.parametrize(
    "argv",
    [
        ["file", "--path", "x.bin", "--json"],
        ["scan", "--dir", ".", "--baseline", "baseline.json", "--json"],
    ],
)
def test_remaining_commands_still_not_ready(argv, capsys):
    assert cli.main(argv) == report.EXIT_NOT_READY
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "not_ready"
    assert payload["notes"] == ["not_implemented_in_skeleton"]


def test_attr_requires_text_or_file():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["attr"])
    assert excinfo.value.code == 2


def test_attr_rejects_top_zero():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["attr", "--text", "x", "--top", "0"])
    assert excinfo.value.code == 2


def test_explain_requires_pick_or_all():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["explain", "--text", "x"])
    assert excinfo.value.code == 2


def test_recover_rejects_pick_zero():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["recover", "--text", "x", "--pick", "0"])
    assert excinfo.value.code == 2


def test_scan_default_format_is_json(capsys):
    code = cli.main(["scan", "--dir", ".", "--baseline", "baseline.json"])
    assert code == report.EXIT_NOT_READY
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "not_ready"
    assert payload["command"] == "scan"
