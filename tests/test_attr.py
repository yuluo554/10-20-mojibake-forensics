# -*- coding: utf-8 -*-
"""M2 ``attr`` tests: bounded candidates, confidence, exit codes, determinism."""

import json
import os

import pytest

from mojibake_forensics import attr
from mojibake_forensics import cli
from mojibake_forensics import codecs_table
from mojibake_forensics import report

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ATTR_FIXTURE = os.path.join(ROOT, "data", "fixtures", "attr", "expect.json")
CLASSIC = "é›…"
CLASSIC_TRUTH = "雅"


def _load_fixture():
    with open(ATTR_FIXTURE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_candidates_are_always_a_list():
    payload = attr.attribute(CLASSIC)
    assert payload["status"] == "candidates"
    assert payload["schema"] == "mojibake-forensics/1"
    assert isinstance(payload["candidates"], list)
    assert len(payload["candidates"]) >= 1
    assert CLASSIC_TRUTH in [item["result"] for item in payload["candidates"]]


def test_candidate_envelope_shape_and_confidence_bounds():
    payload = attr.attribute(CLASSIC, top=10)
    assert payload["total_candidates"] >= len(payload["candidates"])
    assert payload["total_chains"] >= payload["total_candidates"]
    for candidate in payload["candidates"]:
        assert set(candidate) >= {
            "rank",
            "result",
            "path",
            "path_string",
            "depth",
            "score",
            "confidence",
            "note",
        }
        assert set(candidate["score"]) == {"readability", "depth", "language", "total"}
        assert candidate["depth"] >= 1
        assert candidate["path_string"] == ">".join(
            "%s:%s" % (step["op"], step["codec"]) for step in candidate["path"]
        )
        confidence = candidate["confidence"]
        assert confidence is not None
        assert 0.0 <= confidence["lower"] <= confidence["upper"] <= 1.0
    assert [item["rank"] for item in payload["candidates"]] == list(
        range(1, len(payload["candidates"]) + 1)
    )


def test_confidence_normalizes_over_the_full_set():
    entries = [
        {"score_total": 3.0},
        {"score_total": 1.0},
    ]
    intervals, note = attr._confidence(entries)
    assert note is None
    assert round(intervals[0]["lower"], 12) == round(0.75 / 1.05, 12)
    assert round(intervals[1]["upper"], 12) == round(0.25 * 1.05, 12)
    assert round(sum(item["upper"] for item in intervals), 12) > 0


def test_confidence_is_null_when_no_positive_distribution_exists():
    intervals, note = attr._confidence(
        [{"score_total": -0.5}, {"score_total": 0.0}, {"score_total": -0.25}]
    )
    assert intervals == [None, None, None]
    assert note == "no_positive_score"


def test_single_candidate_keeps_a_note():
    payload = attr.attribute(CLASSIC, source_enc="cp1252", target_enc="utf-8")
    assert payload["total_candidates"] == 1
    assert payload["total_chains"] == 1
    candidate = payload["candidates"][0]
    assert candidate["result"] == CLASSIC_TRUTH
    assert candidate["confidence"] == {"lower": 1.0, "upper": 1.0}
    assert candidate["note"] == "single_candidate_in_bounded_search"


def test_no_candidate_is_not_an_empty_success():
    payload = attr.attribute("abc")
    assert payload["status"] == "no_candidate"
    assert payload["candidates"] == []
    assert payload["total_candidates"] == 0
    assert payload["notes"] == ["depth_limit_reached"]


def test_top_one_stays_a_list_and_carries_a_note():
    payload = attr.attribute(CLASSIC, top=1)
    assert isinstance(payload["candidates"], list)
    assert len(payload["candidates"]) == 1
    assert payload["total_candidates"] > 1
    assert payload["candidates"][0]["note"] == "truncated_to_top_n"


def test_truncation_only_affects_display():
    one = attr.attribute(CLASSIC, top=1)
    full = attr.attribute(CLASSIC, top=10 ** 9)
    assert one["total_candidates"] == full["total_candidates"]
    assert one["total_chains"] == full["total_chains"]
    assert one["candidates"][0]["path_string"] == full["candidates"][0]["path_string"]


def test_attr_fixture_cases_replay_into_candidates():
    fixture = _load_fixture()
    inputs = dict((case["id"], case["text"]) for case in fixture["input"]["cases"])
    for case in fixture["expected"]["cases"]:
        full = attr.attribute(inputs[case["id"]], top=10 ** 9)
        assert full["status"] == "candidates", case["id"]
        hits = [item for item in full["candidates"] if item["result"] == case["truth"]]
        assert hits, case["id"]
        assert hits[0]["path_string"] == case["chain"], case["id"]
        shown = attr.attribute(inputs[case["id"]], top=5)
        assert case["truth"] in [item["result"] for item in shown["candidates"]], case["id"]


@pytest.mark.parametrize(
    "argv,code",
    [
        (["--source-enc", "cp932"], "invalid_codec_subset"),
        (["--target-enc", "euc-jp"], "invalid_codec_subset"),
        (["--source-enc", "utf-8,,gbk"], "invalid_codec_subset"),
        (["--freq", "words.txt"], "freq_not_implemented"),
    ],
)
def test_usage_errors_exit_two(argv, code, capsys):
    exit_code = cli.main(["attr", "--text", "x", "--json"] + argv)
    assert exit_code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["code"] == code


def test_subset_shrinks_the_search():
    payload = attr.attribute(CLASSIC, source_enc="cp1252", target_enc="utf-8")
    full = attr.attribute(CLASSIC, top=10 ** 9)
    assert payload["total_chains"] < full["total_chains"]
    assert payload["total_candidates"] < full["total_candidates"]


def test_empty_input_is_a_usage_error(capsys):
    exit_code = cli.main(["attr", "--text", "", "--json"])
    assert exit_code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "empty_input"


def test_file_input_is_read_as_utf8(tmp_path, capsys):
    path = tmp_path / "mojibake.md"
    path.write_text(CLASSIC, encoding="utf-8")
    exit_code = cli.main(["attr", "--file", str(path), "--json"])
    assert exit_code == report.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "candidates"
    assert CLASSIC_TRUTH in [item["result"] for item in payload["candidates"]]


def test_file_input_must_be_utf8(tmp_path, capsys):
    path = tmp_path / "raw.bin"
    path.write_bytes(b"\xff\xfe\x00\x00")
    exit_code = cli.main(["attr", "--file", str(path), "--json"])
    assert exit_code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "file_unreadable"
    assert "`file` subcommand" in payload["message"]


def test_missing_file_does_not_echo_an_absolute_path(tmp_path, capsys):
    missing = tmp_path / "missing.md"
    exit_code = cli.main(["attr", "--file", str(missing), "--json"])
    assert exit_code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "file_unreadable"
    assert str(missing) not in payload["message"]
    assert str(tmp_path) not in payload["message"]


def test_codec_unavailable_exits_three(monkeypatch, capsys):
    monkeypatch.setattr(
        codecs_table, "missing_codecs", lambda *args, **kwargs: ("gb18030",)
    )
    exit_code = cli.main(["attr", "--text", CLASSIC, "--json"])
    assert exit_code == report.EXIT_ENV
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["code"] == "codec_unavailable"


def test_double_run_is_byte_identical(capsys):
    first_code = cli.main(["attr", "--text", CLASSIC, "--top", "7", "--json"])
    first = capsys.readouterr().out
    second_code = cli.main(["attr", "--text", CLASSIC, "--top", "7", "--json"])
    second = capsys.readouterr().out
    assert first_code == second_code == report.EXIT_OK
    assert first == second
    assert first.endswith("\n") and not first.endswith("\n\n")


def test_human_output_is_stable(capsys):
    first_code = cli.main(["attr", "--text", CLASSIC, "--top", "3"])
    first = capsys.readouterr().out
    second_code = cli.main(["attr", "--text", CLASSIC, "--top", "3"])
    second = capsys.readouterr().out
    assert first_code == second_code == report.EXIT_OK
    assert first == second
    assert "candidate(s) in bounded search" in first
    assert "truncated_to_top_n" in first
    assert "not_ready" not in first
    assert os.getcwd() not in first


def test_usage_error_writes_no_files(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    exit_code = cli.main(["attr", "--text", "x", "--source-enc", "cp932", "--json"])
    assert exit_code == report.EXIT_USAGE
    capsys.readouterr()
    assert list(tmp_path.iterdir()) == []
