# -*- coding: utf-8 -*-
"""M5 · file — raw-byte pipeline diagnostics (read-only)."""

import io
import json
import os

import pytest

from mojibake_forensics import cli
from mojibake_forensics import file as file_cmd
from mojibake_forensics import report

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURES = os.path.join(ROOT, "data", "fixtures", "file")


def _fixture(name):
    directory = os.path.join(FIXTURES, name)
    with io.open(os.path.join(directory, "expect.json"), "r", encoding="utf-8") as handle:
        expect = json.load(handle)
    path = os.path.join(directory, expect["input"]["path"])
    return path, expect


def _run_json(path, capsys, preset=None):
    argv = ["file", "--path", path, "--json"]
    if preset is not None:
        argv.append("--preset")
        argv.append(preset)
    code = cli.main(argv)
    out = capsys.readouterr().out
    return code, json.loads(out)


def test_bom_conflict_fixture(capsys):
    """BOM conflict fixture: golden fields match, byte for byte."""
    path, expect = _fixture("bom-conflict")
    with io.open(path, "rb") as handle:
        before = handle.read()
    code, payload = _run_json(path, capsys)
    expected = expect["expected"]
    assert code == report.EXIT_OK
    assert payload["status"] == "ok"
    assert payload["command"] == "file"
    assert payload["bom"] == expected["bom"]
    assert payload["bom_conflict"] is True
    assert payload["content"] == expected["content"]
    assert payload["mutates_input"] is False
    with io.open(path, "rb") as handle:
        assert handle.read() == before  # read-only


def test_utf16_misalignment_fixture(capsys):
    """Odd byte count + shift-by-one evidence, no auto-fix."""
    path, expect = _fixture("utf16-misalignment")
    with io.open(path, "rb") as handle:
        before = handle.read()
    code, payload = _run_json(path, capsys)
    expected = expect["expected"]
    assert code == report.EXIT_OK
    assert payload["utf16_misalignment"] == expected["utf16_misalignment"]
    assert payload["mutates_input"] is False
    with io.open(path, "rb") as handle:
        assert handle.read() == before


@pytest.mark.parametrize("name", ["zip-cjk-utf8", "zip-cjk-cp437"])
def test_zip_name_fixture(name, capsys):
    """Both zip fixtures: flag decides the interpretation, both are listed."""
    path, expect = _fixture(name)
    with io.open(path, "rb") as handle:
        before = handle.read()
    code, payload = _run_json(path, capsys)
    expected = expect["expected"]
    assert code == report.EXIT_OK
    assert payload["zip_names"] == expected["zip_names"]
    assert payload["zipfile_view"] == expected["zipfile_view"]
    assert payload["archive_sha256"] == expected["archive_sha256"]
    assert payload["mutates_input"] is False
    with io.open(path, "rb") as handle:
        assert handle.read() == before


def test_missing_file_is_exit_code_2(capsys):
    code = cli.main(["file", "--path", "definitely-missing.bin", "--json"])
    assert code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["command"] == "file"


def test_report_has_no_absolute_path(tmp_path, capsys):
    """K7: the report never carries the host's absolute paths."""
    target = tmp_path / "sample.bin"
    target.write_bytes(b"\xef\xbb\xbf" + b"abc")
    code, payload = _run_json(str(target), capsys)
    assert code == report.EXIT_OK
    assert payload["path"] == "sample.bin"
    text = json.dumps(payload)
    assert str(tmp_path) not in text
    assert ":\\" not in text


def test_double_run_is_byte_identical(tmp_path, capsys):
    target = tmp_path / "sample.bin"
    target.write_bytes(b"\xef\xbb\xbf" + "中文".encode("gbk"))
    _run_json(str(target), capsys)
    first = capsys.readouterr().out
    _run_json(str(target), capsys)
    second = capsys.readouterr().out
    assert first == second


def test_csv_preset_reports_candidates(tmp_path, capsys):
    target = tmp_path / "table.csv"
    target.write_bytes("名前,種類\n".encode("shift_jis"))
    code, payload = _run_json(str(target), capsys, preset="csv-excel-win")
    assert code == report.EXIT_OK
    section = payload["csv_candidates"]
    codecs_seen = dict((item["codec"], item["decodable"]) for item in section["candidates"])
    assert codecs_seen["shift_jis"] is True
    assert codecs_seen["cp1252"] is True  # latin-1-ish always decodes
    assert section["delimiter"] == ","


def test_zip_preset_suppresses_other_sections(capsys):
    path, _ = _fixture("zip-cjk-utf8")
    code, payload = _run_json(path, capsys, preset="zip-names")
    assert code == report.EXIT_OK
    assert "zip_names" in payload
    assert "utf16_misalignment" not in payload
    assert "csv_candidates" not in payload


def test_codec_unavailable_is_exit_code_3(tmp_path, capsys, monkeypatch):
    import codecs as codecs_module

    target = tmp_path / "table.csv"
    target.write_bytes(b"a,b\n")
    original_lookup = codecs_module.lookup

    def broken_lookup(name):
        if name.lower() in ("cp1252", "gbk", "shift_jis", "utf-8", "gb18030"):
            raise LookupError(name)
        return original_lookup(name)

    monkeypatch.setattr(codecs_module, "lookup", broken_lookup)
    argv = ["file", "--path", str(target), "--preset", "csv-excel-win", "--json"]
    code = cli.main(argv)
    assert code == report.EXIT_ENV
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"


def test_render_is_stable_and_readonly(tmp_path, capsys):
    target = tmp_path / "sample.zip"
    import shutil

    shutil.copyfile(_fixture("zip-cjk-utf8")[0], str(target))
    code = cli.main(["file", "--path", str(target)])
    assert code == report.EXIT_OK
    human = capsys.readouterr().out
    assert human.startswith("file: sample.zip (read-only)")
    assert "zip name" in human
