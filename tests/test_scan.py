# -*- coding: utf-8 -*-
"""M5 · scan — read-only CI gate with baseline accounting (K9)."""

import io
import json
import os
import time

import pytest

from mojibake_forensics import cli
from mojibake_forensics import report
from mojibake_forensics import scan as scan_cmd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCAN_FIXTURE = os.path.join(ROOT, "data", "fixtures", "scan")
BASELINE = os.path.join(SCAN_FIXTURE, "clean-corpus.json")


def _run_json(argv, capsys):
    code = cli.main(argv)
    out = capsys.readouterr().out
    return code, json.loads(out)


def _snapshot(root):
    """mtime + content of every file under ``root`` (read-only assertion)."""
    snapshot = {}
    for base, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(base, name)
            with io.open(path, "rb") as handle:
                snapshot[path] = (os.path.getmtime(path), handle.read())
    return snapshot


def test_clean_corpus_zero_new_zero_changes(capsys):
    """K9 gate: clean corpus → 0 new hits, exit 0, files untouched."""
    clean_dir = os.path.join(SCAN_FIXTURE, "clean")
    snapshot = _snapshot(clean_dir)
    code, payload = _run_json(
        ["scan", "--dir", clean_dir, "--baseline", BASELINE, "--json"], capsys
    )
    after = _snapshot(clean_dir)
    assert snapshot == after  # zero changes (mtime + content)
    assert code == report.EXIT_OK
    assert payload["status"] == "ok"
    assert payload["command"] == "scan"
    assert payload["new"] == []
    assert payload["files_scanned"] == 10
    assert "milestone" not in payload


def test_polluted_corpus_exit_1_and_locatable(capsys):
    """Polluted corpus → exit 1, hits locate path + line + candidate set."""
    polluted = os.path.join(SCAN_FIXTURE, "polluted")
    code, payload = _run_json(
        ["scan", "--dir", polluted, "--baseline", BASELINE, "--json"], capsys
    )
    assert code == report.EXIT_ATTENTION
    assert payload["status"] == "attention"
    assert payload["notes"] == ["new_hits_require_attention"]
    by_path = dict((hit["path"], hit) for hit in payload["new"])
    assert set(by_path) == {"ja.md", "zh.md"}
    zh = by_path["zh.md"]
    assert zh["line"] == 1
    candidates = "".join(c["result"] for c in zh["candidates"])
    assert "中文測試" in candidates
    ja = by_path["ja.md"]
    candidates = "".join(c["result"] for c in ja["candidates"])
    assert "日本語" in candidates


def test_stale_entries_do_not_affect_exit_code(tmp_path, capsys):
    """Baseline entries pointing at missing files → stale, exit code unchanged."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "clean.txt").write_bytes("Clean ASCII baseline line.\n".encode("utf-8"))
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "schema": "mojibake-forensics/clean-corpus/1",
                "expected_new": [],
                "files": [
                    {"path": "clean.txt", "allowed_hits": []},
                    {"path": "clean/missing.md", "allowed_hits": []},
                ],
            }
        ),
        encoding="utf-8",
    )
    code, payload = _run_json(
        ["scan", "--dir", str(corpus), "--baseline", str(baseline), "--json"], capsys
    )
    assert code == report.EXIT_OK
    assert payload["stale"] == ["clean/missing.md"]
    assert payload["new"] == []


def test_baselined_hit_is_not_new(tmp_path, capsys):
    """A hit on a baseline-covered file goes to ``baselined``, not ``new``."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    # One mojibake line (utf-8 bytes misread as latin-1) that the baseline covers.
    (corpus / "known.md").write_bytes("中文測試\n".encode("utf-8").decode("latin-1").encode("utf-8"))
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "schema": "mojibake-forensics/clean-corpus/1",
                "expected_new": [],
                "files": [{"path": "known.md", "allowed_hits": ["mojibake"]}],
            }
        ),
        encoding="utf-8",
    )
    code, payload = _run_json(
        ["scan", "--dir", str(corpus), "--baseline", str(baseline), "--json"], capsys
    )
    assert code == report.EXIT_OK
    assert payload["new"] == []
    assert len(payload["baselined"]) == 1
    assert payload["baselined"][0]["path"] == "known.md"
    assert payload["baselined"][0]["line"] == 1


def test_bad_baseline_is_exit_2_and_writes_nothing(tmp_path, capsys):
    """Baseline JSON syntax error → exit 2, no output file is produced."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    out_file = tmp_path / "report.json"
    code = cli.main(
        [
            "scan", "--dir", str(tmp_path), "--baseline", str(bad),
            "--format", "json",
        ]
    )
    assert code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert not out_file.exists()


def test_double_run_json_byte_identical(capsys):
    argv = ["scan", "--dir", os.path.join(SCAN_FIXTURE, "polluted"), "--baseline", BASELINE, "--json"]
    _run_json(argv, capsys)
    first = capsys.readouterr().out
    _run_json(argv, capsys)
    second = capsys.readouterr().out
    assert first == second


def test_json_keys_sorted_no_host_facts(capsys):
    code = cli.main(
        ["scan", "--dir", os.path.join(SCAN_FIXTURE, "polluted"), "--baseline", BASELINE, "--json"]
    )
    out = capsys.readouterr().out
    assert code == report.EXIT_ATTENTION
    text = json.dumps(json.loads(out), sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    assert text == out  # canonical serialization (K4)
    assert str(SCAN_FIXTURE) not in out
    assert ":\\" not in out


def test_scan_directory_function_buckets(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "clean.txt").write_bytes("Clean ASCII baseline line.\n".encode("utf-8"))
    baseline = {"files": [{"path": "clean.txt", "allowed_hits": []}], "expected_new": []}
    buckets = scan_cmd.scan_directory(str(corpus), baseline)
    assert buckets["new"] == []
    assert buckets["baselined"] == []
    assert buckets["exit_code"] == report.EXIT_OK
    assert buckets["files_scanned"] == 1
    assert buckets["stale"] == []


def test_render_human_output(capsys):
    code = cli.main(
        ["scan", "--dir", os.path.join(SCAN_FIXTURE, "polluted"), "--baseline", BASELINE,
         "--format", "human"]
    )
    out = capsys.readouterr().out
    assert code == report.EXIT_ATTENTION
    assert out.startswith("scan: ")
    assert "ja.md:1" in out
    assert "zh.md:1" in out


def test_line_hit_k9_thresholds():
    assert scan_cmd.line_hit("") is None
    assert scan_cmd.line_hit("Clean ASCII baseline line.") is None
    hit = scan_cmd.line_hit(
        "中文測試\n".encode("utf-8").decode("latin-1")
    )
    assert hit is not None
    assert hit["input_readability"] < 0.5
    results = "".join(c["result"] for c in hit["candidates"])
    assert "中文測試" in results
