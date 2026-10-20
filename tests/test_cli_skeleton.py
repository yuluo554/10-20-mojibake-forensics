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


def test_attr_not_ready_json(capsys):
    code = cli.main(["attr", "--text", "é›…", "--json"])
    assert code == report.EXIT_NOT_READY
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "not_ready"
    assert payload["command"] == "attr"
    assert payload["milestone"] == "M2"
    assert payload["schema"] == "mojibake-forensics/1"
    assert payload["criteria"]["max_depth"] == 3
    assert payload["notes"] == ["not_implemented_in_skeleton"]


def test_recover_not_ready_human(capsys):
    code = cli.main(["recover", "--text", "x", "--pick", "1"])
    assert code == report.EXIT_NOT_READY
    out = capsys.readouterr().out
    assert "not implemented yet" in out
    assert "M4" in out


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
