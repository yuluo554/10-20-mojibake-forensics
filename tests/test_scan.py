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


def _reverse_chain(chain):
    """Turn a corruption chain into the repair chain the report prints.

    ``encode:utf-8>decode:cp437`` (how the file got broken) is undone by
    ``encode:cp437>decode:utf-8`` (what ``scan`` reports as ``path_string``):
    reverse the step order and swap encode/decode in every step.
    """
    swap = {"encode": "decode", "decode": "encode"}
    steps = chain.split(">")
    return ">".join("%s:%s" % (swap[op], codec) for op, codec in
                    (step.split(":", 1) for step in reversed(steps)))


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
    """Polluted corpus → exit 1, hits locate path + line + candidate set.

    Reported paths are relative to the **baseline file's directory**
    (``data/README.md`` §4.6), so the polluted subtree keeps its ``polluted/``
    prefix — the same shape ``expect.json`` records.
    """
    polluted = os.path.join(SCAN_FIXTURE, "polluted")
    code, payload = _run_json(
        ["scan", "--dir", polluted, "--baseline", BASELINE, "--json"], capsys
    )
    assert code == report.EXIT_ATTENTION
    assert payload["status"] == "attention"
    assert payload["notes"] == ["new_hits_require_attention"]
    by_path = dict((hit["path"], hit) for hit in payload["new"])
    assert set(by_path) == {"polluted/ja.md", "polluted/zh.md"}
    zh = by_path["polluted/zh.md"]
    assert zh["line"] == 1
    candidates = "".join(c["result"] for c in zh["candidates"])
    assert "中文測試" in candidates
    ja = by_path["polluted/ja.md"]
    candidates = "".join(c["result"] for c in ja["candidates"])
    assert "日本語" in candidates


def test_stale_entries_do_not_affect_exit_code(tmp_path, capsys):
    """Baseline entries pointing at missing files → stale, exit code unchanged.

    The baseline lives beside the corpus root, so its paths carry the ``corpus/``
    prefix (§4.6 anchor rule).
    """
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
                    {"path": "corpus/clean.txt", "allowed_hits": []},
                    {"path": "corpus/missing.md", "allowed_hits": []},
                ],
            }
        ),
        encoding="utf-8",
    )
    code, payload = _run_json(
        ["scan", "--dir", str(corpus), "--baseline", str(baseline), "--json"], capsys
    )
    assert code == report.EXIT_OK
    assert payload["stale"] == ["corpus/missing.md"]
    assert payload["new"] == []


def test_baselined_hit_is_not_new(tmp_path, capsys):
    """A hit on a baseline-covered file goes to ``baselined``, not ``new``.

    Baseline paths are relative to the baseline file's directory (§4.6), hence
    the ``corpus/`` prefix.
    """
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
                "files": [{"path": "corpus/known.md", "allowed_hits": ["mojibake"]}],
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
    assert payload["baselined"][0]["path"] == "corpus/known.md"
    assert payload["baselined"][0]["line"] == 1


def test_missing_directory_is_exit_2_and_writes_nothing(tmp_path, capsys):
    """D3: a mistyped ``--dir`` is a usage error, never a silent green scan.

    Before this check the walk was skipped when ``os.path.isdir()`` was false and
    the command reported ``status="ok"`` with ``files_scanned: 0``; one typo in
    the CI command made the gate vacuously green.
    """
    out_file = tmp_path / "report.json"
    code = cli.main(
        [
            "scan", "--dir", str(tmp_path / "cleen"), "--baseline", BASELINE,
            "--format", "json",
        ]
    )
    assert code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["code"] == "scan_directory_missing"
    assert "scan" not in payload.get("notes", [])
    assert not out_file.exists()


def test_directory_pointing_at_a_file_is_exit_2_and_writes_nothing(tmp_path, capsys):
    """D3: ``--dir`` aimed at a regular file is a usage error, not an empty scan."""
    target = tmp_path / "not-a-dir.md"
    target.write_bytes("Clean ASCII baseline line.\n".encode("utf-8"))
    out_file = tmp_path / "report.json"
    code = cli.main(
        [
            "scan", "--dir", str(target), "--baseline", BASELINE,
            "--format", "json",
        ]
    )
    assert code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["code"] == "scan_directory_not_a_directory"
    assert not out_file.exists()


def test_expect_json_matches_reality(capsys):
    """D4/D5: ``expect.json`` is live evidence, not decoration.

    Everything the fixture declares about the two documented invocations is
    asserted cell by cell — including ``stale``, which no test used to read. The
    baseline anchor rule (§4.6) is what makes both invocations pass at once.
    """
    with io.open(os.path.join(SCAN_FIXTURE, "expect.json"), "r", encoding="utf-8") as handle:
        expect = json.load(handle)

    expected = expect["expected"]
    # The declared input shape must be the one the tests actually use.
    assert expect["input"]["baseline"] == os.path.basename(BASELINE)

    for name in ("clean", "polluted"):
        code, payload = _run_json(
            ["scan", "--dir", os.path.join(SCAN_FIXTURE, name),
             "--baseline", BASELINE, "--json"],
            capsys,
        )
        want = expected[name]

        # exit_code is on the envelope's status, not in the JSON body.
        assert code == want["exit_code"], "%s: exit code" % name
        assert payload["status"] == ("ok" if want["exit_code"] == 0 else "attention")

        got_new = [hit["path"] for hit in payload["new"]]
        if name == "clean":
            assert got_new == want["new"], "%s: new" % name
        else:
            assert got_new == [item["path"] for item in want["new"]], "%s: new paths" % name
            # Every declared hit detail must be locatable in the live report.
            by_path = dict((hit["path"], hit) for hit in payload["new"])
            for item in want["new"]:
                hit = by_path[item["path"]]
                assert hit["line"] == 1
                assert item["category"] == "mojibake"  # declared category for both hits
                assert item["candidate_contains"] in "".join(
                    c["result"] for c in hit["candidates"]
                ), "%s: candidate for %s" % (name, item["path"])
                # ``corruption_chain`` describes how the bytes were broken; the
                # report's ``path_string`` is the repair chain — the exact
                # reversal of it. Asserting the reversal keeps both readings
                # honest instead of weakening the check.
                repair_chain = _reverse_chain(item["corruption_chain"])
                assert repair_chain in [
                    c["path_string"] for c in hit["candidates"]
                ], "%s: chain for %s" % (name, item["path"])
                # ``truth_bytes_hex`` are the UTF-8 bytes of the pre-corruption
                # text: decoding them must give back the declared candidate.
                raw_bytes = bytes(
                    int(b, 16) for b in item["truth_bytes_hex"].split()
                )
                assert raw_bytes.decode("utf-8") == item["candidate_contains"]

        assert [hit["path"] for hit in payload["baselined"]] == [
            hit["path"] for hit in want.get("baselined", [])
        ], "%s: baselined" % name
        # A fixture block that declares no ``stale`` list declares no stale
        # entries; asserting the empty bucket is still a real check.
        assert payload["stale"] == want.get("stale", []), "%s: stale" % name

        # ``files_scanned`` is declared for clean and derivable for both: it must
        # equal the number of files actually on disk under ``--dir``.
        on_disk = sum(len(files) for _b, _d, files in os.walk(os.path.join(SCAN_FIXTURE, name)))
        assert payload["files_scanned"] == on_disk, "%s: files on disk" % name
        if "files_scanned" in want:
            assert payload["files_scanned"] == want["files_scanned"], "%s: files" % name


def test_expect_json_stale_probe(tmp_path, capsys):
    """The ``stale`` bucket the fixture declares: reported, never affecting exit."""
    with io.open(os.path.join(SCAN_FIXTURE, "expect.json"), "r", encoding="utf-8") as handle:
        probe = json.load(handle)["expected"]["stale_probe"]
    assert probe["bucket"] == "stale"
    assert probe["exit_code_effect"] == "none"

    # Copy the clean subtree beside the baseline so the fixture's declared
    # ``clean/<name>`` layout is reproduced under one anchor (and so the walk and
    # the baseline share a drive; relpath is not defined across mounts).
    corpus = tmp_path / "clean"
    corpus.mkdir()
    for name in sorted(os.listdir(os.path.join(SCAN_FIXTURE, "clean"))):
        with io.open(os.path.join(SCAN_FIXTURE, "clean", name), "rb") as handle:
            (corpus / name).write_bytes(handle.read())

    baseline = {
        "schema": "mojibake-forensics/clean-corpus/1",
        "expected_new": [],
        "files": [
            {"path": "clean/en-01.md", "allowed_hits": []},
            {"path": "clean/%s" % os.path.basename(probe["virtual_missing_path"]),
             "allowed_hits": []},
        ],
    }
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    code, payload = _run_json(
        ["scan", "--dir", str(corpus), "--baseline", str(baseline_path), "--json"], capsys
    )
    assert code == report.EXIT_OK  # stale never changes the exit code
    assert payload["stale"] == [probe["virtual_missing_path"]]
    assert payload["new"] == []


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
    """Plain-API call: ``root`` defaults to ``directory`` (unchanged meaning)."""
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


def test_scan_directory_root_changes_reported_paths(tmp_path):
    """``root`` only re-anchors paths; the walk still covers ``directory``."""
    root = tmp_path
    corpus = root / "corpus"
    corpus.mkdir()
    (corpus / "known.md").write_bytes("中文測試\n".encode("utf-8").decode("latin-1").encode("utf-8"))
    baseline = {"files": [{"path": "corpus/known.md", "allowed_hits": []}], "expected_new": []}

    anchored = scan_cmd.scan_directory(str(corpus), baseline, root=str(root))
    assert anchored["new"] == []
    assert anchored["baselined"][0]["path"] == "corpus/known.md"

    defaulted = scan_cmd.scan_directory(str(corpus), baseline)
    assert defaulted["new"][0]["path"] == "known.md"


def test_render_human_output(capsys):
    code = cli.main(
        ["scan", "--dir", os.path.join(SCAN_FIXTURE, "polluted"), "--baseline", BASELINE,
         "--format", "human"]
    )
    out = capsys.readouterr().out
    assert code == report.EXIT_ATTENTION
    assert out.startswith("scan: ")
    assert "polluted/ja.md:1" in out
    assert "polluted/zh.md:1" in out


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
