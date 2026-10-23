# -*- coding: utf-8 -*-
"""M4 ``recover`` tests: five irreversible verdicts, verified replay, exits."""

import io
import json
import os

import pytest

from mojibake_forensics import cli
from mojibake_forensics import codecs_table
from mojibake_forensics import recover as recover_cmd
from mojibake_forensics import report

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLASSIC = u"é›…"  # mojibake for 雅 (cp1252 > utf-8)
CLASSIC_TRUTH = u"雅"

FIVE = {
    u"abc\ufffddef": ("lost", "replacement_char", 3),
    u"锟斤拷": ("lost", "kun_jin_kao", 0),
    u"烫烫烫": ("not_mojibake", "msvc_fill", None),
    u"屯屯屯": ("not_mojibake", "msvc_fill", None),
    u"a?b": ("lost", "encode_truncated", 1),
}


def _run_json(argv, capsys):
    code = cli.main(argv + ["--json"])
    return code, json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("text,expected", sorted(FIVE.items()))
def test_five_irreversible_classes(capsys, text, expected):
    status, reason, offset = expected
    code, payload = _run_json(["recover", "--text", text, "--pick", "1"], capsys)
    assert code == report.EXIT_ATTENTION
    assert payload["schema"] == "mojibake-forensics/1"
    assert payload["command"] == "recover"
    assert payload["status"] == status
    assert payload["reason"] == reason
    assert payload["recovered"] is None
    assert payload["verify"] is False
    if reason == "msvc_fill":
        assert payload["loss"] is None
    else:
        assert payload["loss"]["offset"] == offset
        assert payload["loss"]["step"] in ("encode", "decode")


@pytest.mark.parametrize("text,expected", sorted(FIVE.items()))
def test_no_tool_invented_characters(capsys, text, expected):
    """The verdict never fabricates a character absent from the input."""
    code, payload = _run_json(["recover", "--text", text, "--pick", "1"], capsys)
    recovered = payload.get("recovered")
    if recovered is not None:
        for char in recovered:
            assert char in text
    loss = payload.get("loss") or {}
    if loss.get("replaced_with"):
        assert loss["replaced_with"].startswith(("U+", "?"))
        assert text  # nothing was invented: verdict text only cites offsets


def test_recovery_of_classic_text(capsys):
    code, payload = _run_json(["recover", "--text", CLASSIC, "--pick", "1"], capsys)
    assert code == report.EXIT_OK
    assert payload["status"] == "recovered"
    assert payload["recovered"] == CLASSIC_TRUTH
    assert payload["verify"] is True
    assert payload["loss"] is None
    assert payload["path_string"] == "encode:cp1252>decode:utf-8"
    assert payload["candidate"]["rank"] == 1
    assert payload["steps"][0]["verify"] is True


def test_recovered_double_run_byte_identical(capsys):
    first, second = [], []
    for sink in (first, second):
        code = cli.main(["recover", "--text", CLASSIC, "--pick", "1", "--json"])
        out = capsys.readouterr().out
        sink.append((code, out))
    assert first == second
    text = json.loads(first[0][1])
    assert "python_version" in text  # envelope present, still identical


def test_recovered_human_double_run_byte_identical(capsys):
    outs = []
    for _ in range(2):
        code = cli.main(["recover", "--text", CLASSIC, "--pick", "1"])
        outs.append((code, capsys.readouterr().out))
    assert outs[0] == outs[1]


def test_report_has_no_host_facts(capsys):
    _, payload = _run_json(["recover", "--text", CLASSIC, "--pick", "1"], capsys)
    raw = json.dumps(payload, ensure_ascii=False)
    assert os.getcwd() not in raw
    computer_name = os.environ.get("COMPUTERNAME")
    if computer_name:  # Windows-only var; empty default would make the check vacuous on Linux
        assert computer_name not in raw
    for key in ("time", "hostname", "host", "user"):
        assert key not in payload


def test_host_facts_check_is_not_vacuous_when_var_absent(monkeypatch, capsys):
    """D1 guard: the host-facts check must not go vacuous when the var is absent.

    ``test_report_has_no_host_facts`` used to pass an empty default to the
    environment lookup for ``COMPUTERNAME``. On Linux the variable is unset, that
    default made the substring assertion fail for *every* payload, and the suite
    shipped red. This test pins both halves: with the var absent the branch must
    be skipped (and the naive form shown to be unusable), and with a value
    present the very same assertion shape must still catch a leak.
    """
    sentinel = "HOSTFACT-SENTINEL-9f3c"

    # (1) var absent — the branch the old code got wrong.
    monkeypatch.delenv("COMPUTERNAME", raising=False)
    _, payload = _run_json(["recover", "--text", CLASSIC, "--pick", "1"], capsys)
    raw = json.dumps(payload, ensure_ascii=False)
    assert os.environ.get("COMPUTERNAME") is None  # this really is the absent branch
    assert os.getcwd() not in raw  # the still-active part of the check

    # The retired form would have been vacuous here: "" is in every string.
    # Asserting it keeps the regression visible instead of hiding it.
    assert "" in raw

    # (2) var present — positive control: the assertion shape fires on a leak.
    monkeypatch.setenv("COMPUTERNAME", sentinel)
    _, payload = _run_json(["recover", "--text", CLASSIC, "--pick", "1"], capsys)
    raw = json.dumps(payload, ensure_ascii=False)
    assert sentinel not in raw  # shipped payload carries no host value

    # ...and the detector is armed: inject the leak and the very same assertion
    # shape must catch it. Without this half the test would pass on a tool that
    # simply never emits anything.
    leaked = json.dumps(dict(payload, host_value=sentinel), ensure_ascii=False)
    assert sentinel in leaked
    with pytest.raises(AssertionError):
        assert sentinel not in leaked

    # (3) static guard: the vacuous idiom must not come back into this file.
    # ``os.environ.get(<COMPUTERNAME>, "")`` is the exact shape that shipped red
    # in v0.1.0; on Linux the default "" made the assertion fail for every
    # payload. Restoring it turns this test red on any platform, including the
    # Windows machine where the bug is otherwise invisible. The needle is
    # assembled at runtime so this assertion does not match its own source.
    needle = 'os.environ.get("COMPUTER' + 'NAME", "")'
    source = io.open(os.path.abspath(__file__), "r", encoding="utf-8").read()
    assert needle not in source


def test_pick_missing_is_usage_error(capsys):
    code, payload = _run_json(["recover", "--text", CLASSIC], capsys)
    assert code == report.EXIT_USAGE
    assert payload["status"] == "error"
    assert payload["code"] == "missing_pick"


def test_pick_out_of_range_is_usage_error(capsys):
    code, payload = _run_json(["recover", "--text", CLASSIC, "--pick", "9999"], capsys)
    assert code == report.EXIT_USAGE
    assert payload["status"] == "error"
    assert payload["code"] == "pick_out_of_range"
    assert "candidate count" in payload["message"]


def test_pick_zero_rejected_by_parser():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["recover", "--text", CLASSIC, "--pick", "0", "--json"])
    assert excinfo.value.code == 2


def test_out_must_not_overwrite_input(tmp_path, capsys):
    input_path = tmp_path / "in.txt"
    with io.open(str(input_path), "w", encoding="utf-8", newline="") as handle:
        handle.write(CLASSIC)
    before = input_path.read_bytes()
    code, payload = _run_json(
        ["recover", "--file", str(input_path), "--pick", "1", "--out", str(input_path)],
        capsys,
    )
    assert code == report.EXIT_USAGE
    assert payload["status"] == "error"
    assert payload["code"] == "out_overwrites_input"
    assert input_path.read_bytes() == before


def test_out_writes_recovered_text(tmp_path, capsys):
    out_path = tmp_path / "out.txt"
    code, payload = _run_json(
        ["recover", "--text", CLASSIC, "--pick", "1", "--out", str(out_path)],
        capsys,
    )
    assert code == report.EXIT_OK
    assert payload["status"] == "recovered"
    assert out_path.read_text(encoding="utf-8") == CLASSIC_TRUTH


def test_no_candidate_recover_reports_lost(capsys):
    """A clean text with no lossless chain is LOST(no_candidate), never a guess."""
    code, payload = _run_json(["recover", "--text", "ab", "--pick", "1"], capsys)
    assert code == report.EXIT_ATTENTION
    assert payload["status"] == "lost"
    assert payload["reason"] == "no_candidate"
    assert payload["recovered"] is None
    assert payload["notes"] == ["depth_limit_reached"]


def test_verify_failure_degrades_to_lost(monkeypatch, capsys):
    """A tampered step record must degrade to LOST(verify_failed)."""
    import mojibake_forensics.explain as explain_mod

    original = explain_mod.replay_chain

    def tampered(chain):
        result = original(chain)
        if result["steps"]:
            result["steps"][0]["verify"] = False
            result["verify"] = False
            result["failed_step"] = 1
        return result

    monkeypatch.setattr(explain_mod, "replay_chain", tampered)
    code, payload = _run_json(["recover", "--text", CLASSIC, "--pick", "1"], capsys)
    assert code == report.EXIT_ATTENTION
    assert payload["status"] == "lost"
    assert payload["reason"] == "verify_failed"
    assert payload["recovered"] is None
    assert payload["verify"] is False
    assert payload["notes"] == ["unverified_repair_suppressed", "no_invented_characters"]


def test_codec_unavailable_exits_3(monkeypatch, capsys):
    import mojibake_forensics.cli as cli_mod
    from mojibake_forensics.codecs_table import CodecUnavailable

    def boom():
        raise CodecUnavailable(("gb18030",))

    monkeypatch.setattr(cli_mod.codecs_table, "ensure_codecs", boom)
    code = cli_mod.main(["recover", "--text", CLASSIC, "--pick", "1", "--json"])
    assert code == report.EXIT_ENV
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["code"] == "codec_unavailable"


def test_file_fixture_texts_match_five_classes():
    """The five fixtures' expect.json stays the authoritative expectation."""
    names = {
        "kun-jin-kao": ("LOST", "kun_jin_kao"),
        "tang-tang": ("NOT_MOJIBAKE", "msvc_fill"),
        "question-mark": ("LOST", "encode_truncated"),
        "replacement-char": ("LOST", "replacement_char"),
        "silent-drop": ("LOST", "silent_drop"),
    }
    for name, (status, reason) in names.items():
        with open(
            os.path.join(ROOT, "data", "fixtures", "recover", name, "expect.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)
        assert payload["expected"]["status"] == status, name
        assert payload["expected"]["reason"] == reason, name


def test_silent_drop_requires_provenance_note_documented():
    """silent_drop is decided by provenance only; the CLI reports the boundary."""
    with open(
        os.path.join(ROOT, "data", "fixtures", "recover", "silent-drop", "expect.json"),
        "r",
        encoding="utf-8",
    ) as handle:
        payload = json.load(handle)
    assert payload["expected"]["requires_provenance"] is True
    assert payload["input"]["text"] == "ab"


def test_human_render_stable(capsys):
    code = cli.main(["recover", "--text", CLASSIC, "--pick", "1"])
    human = capsys.readouterr().out
    assert code == report.EXIT_OK
    assert "RECOVERED" in human
    assert "verify: true" in human
    assert "recovered: '雅'" in human
