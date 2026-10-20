# -*- coding: utf-8 -*-
"""M3 ``explain`` tests: replay proofs, exact failure steps, divergence, exits."""

import json
import os
import subprocess
import sys

import pytest

from mojibake_forensics import attr
from mojibake_forensics import cli
from mojibake_forensics import codecs_table
from mojibake_forensics import explain
from mojibake_forensics import paths
from mojibake_forensics import report

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPLAIN_FIXTURE = os.path.join(ROOT, "data", "fixtures", "explain", "expect.json")
INDEPENDENT = os.path.join(ROOT, "tests", "independent_replay.py")
CLASSIC = "é›…"
CLASSIC_TRUTH = "雅"


def _fixture():
    with open(EXPLAIN_FIXTURE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _run_json(argv, capsys):
    code = cli.main(argv + ["--json"])
    return code, json.loads(capsys.readouterr().out)


def _enc(index, codec, input_text, output_hex):
    return {
        "index": index,
        "op": "encode",
        "codec": codec,
        "input": input_text,
        "output_hex": output_hex,
        "verify": True,
    }


def _dec(index, codec, input_hex, output):
    return {
        "index": index,
        "op": "decode",
        "codec": codec,
        "input_hex": input_hex,
        "output": output,
        "verify": True,
    }


def _proof(steps, result):
    return {
        "rank": 1,
        "result": result,
        "steps": steps,
        "verify": True,
        "failed_step": None,
        "output": result,
    }


def _entry(result, path_string):
    return {"result": result, "path_string": path_string}


def _independent(payload, text=CLASSIC):
    return subprocess.run(
        [sys.executable, INDEPENDENT],
        input=json.dumps({"text": text, "payload": payload}, ensure_ascii=False),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
    )


def test_pick_one_proof_shape(capsys):
    code, payload = _run_json(
        ["explain", "--text", CLASSIC, "--pick", "1", "--vs", "2"], capsys
    )
    assert code == report.EXIT_OK
    assert payload["schema"] == "mojibake-forensics/1"
    assert payload["command"] == "explain"
    assert payload["status"] == "ok"
    assert payload["mode"] == "pick"
    assert payload["pick"] == 1
    assert payload["total_candidates"] >= 1
    assert payload["total_chains"] >= payload["total_candidates"]
    proof = payload["proofs"][0]
    assert proof["rank"] == 1
    assert proof["path_string"] == ">".join(
        "%s:%s" % (step["op"], step["codec"]) for step in proof["path"]
    )
    assert proof["steps"]
    assert proof["verify"] is True
    assert proof["failed_step"] is None
    assert proof["output"] == proof["result"]
    for step in proof["steps"]:
        assert step["verify"] is True
        if step["op"] == "encode":
            assert isinstance(step["input"], str)
            for token in step["output_hex"].split():
                assert len(token) == 2
                assert token == token.upper()
                assert token.isalnum()
        else:
            assert isinstance(step["output"], str)
            for token in step["input_hex"].split():
                assert len(token) == 2
                assert token == token.upper()
                assert token.isalnum()
    assert proof["divergence"]["vs_rank"] == 2


def test_independent_replay_accepts_the_reported_proof(capsys):
    code, payload = _run_json(
        ["explain", "--text", CLASSIC, "--pick", "1", "--vs", "2"], capsys
    )
    assert code == report.EXIT_OK
    proc = _independent(payload)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "summary: 1 proof(s), 0 failure(s)" in proc.stdout


def test_independent_replay_accepts_every_candidate(capsys):
    payload = explain.explain(CLASSIC, all_candidates=True)
    proc = _independent(payload)
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr
    assert "summary: %d proof(s), 0 failure(s)" % payload["total_candidates"] in proc.stdout


def test_independent_replay_catches_a_tampered_step(capsys):
    code, payload = _run_json(["explain", "--text", CLASSIC, "--pick", "1"], capsys)
    assert code == report.EXIT_OK
    payload["proofs"][0]["steps"][0]["output_hex"] = "00"
    proc = _independent(payload)
    assert proc.returncode == 1
    assert "FAIL" in proc.stdout


def test_fixture_positive_chain_is_reported_step_for_step(capsys):
    fixture = _fixture()
    expected = fixture["expected"]["positive"]
    code, payload = _run_json(["explain", "--text", fixture["input"]["text"], "--pick", "1"], capsys)
    assert code == report.EXIT_OK
    hits = [
        proof
        for proof in payload["proofs"]
        if proof["path_string"] == fixture["input"]["positive_chain"]
    ]
    assert len(hits) == 1
    proof = hits[0]
    assert proof["result"] == expected["result"]
    assert proof["verify"] is expected["verify"]
    assert proof["failed_step"] is expected["failed_step"]
    assert len(proof["steps"]) == len(expected["steps"])
    for actual, wanted in zip(proof["steps"], expected["steps"]):
        assert actual["index"] == wanted["index"]
        assert actual["op"] == wanted["op"]
        assert actual["codec"] == wanted["codec"]
        for key in ("input", "input_hex", "output", "output_hex"):
            if key in wanted:
                assert actual[key] == wanted[key]
        assert actual["verify"] is True


def test_mutated_codec_is_reported_at_the_exact_step():
    """Fixture negative: encode:cp1252>decode:gb18030 fails at step 2."""
    fixture = _fixture()
    negative = fixture["expected"]["negative"]
    data = fixture["input"]
    chain = paths.Chain(
        steps=(
            paths.Step(
                index=1,
                op="encode",
                codec="cp1252",
                input_text=data["text"],
                output_hex=data["corrupted_bytes_hex"],
            ),
            paths.Step(
                index=2,
                op="decode",
                codec="gb18030",
                input_hex=data["corrupted_bytes_hex"],
                output_text=None,
            ),
        )
    )
    replayed = explain.replay_chain(chain)
    assert replayed["verify"] is False
    assert replayed["failed_step"] == negative["failed_step"] == 2
    failure = replayed["steps"][-1]["failure"]
    assert failure["reason"] == "decode_error"
    assert failure["byte_offset"] == negative["byte_offset"] == 2


def test_mutated_codec_mismatch_is_reported_at_the_exact_step():
    """Change a passing decode codec but keep the recorded text: mismatch at 2."""
    ranked, _ = attr.search(CLASSIC)
    original = ranked[0]["chain"]
    mutated = paths.Chain(
        steps=(
            original.steps[0],
            paths.Step(
                index=2,
                op="decode",
                codec="latin-1",
                input_hex=original.steps[1].input_hex,
                output_text=original.steps[1].output_text,
            ),
        )
    )
    replayed = explain.replay_chain(mutated)
    assert replayed["verify"] is False
    assert replayed["failed_step"] == 2
    failure = replayed["steps"][-1]["failure"]
    assert failure["reason"] == "mismatch"
    assert failure["char_offset"] == 0


def test_divergence_reports_the_first_differing_byte():
    left = _proof(
        [_enc(1, "cp1252", CLASSIC, "E9 9B 85"), _dec(2, "utf-8", "E9 9B 85", CLASSIC_TRUTH)],
        CLASSIC_TRUTH,
    )
    right = _proof(
        [_enc(1, "cp1252", CLASSIC, "E9 9B 84"), _dec(2, "utf-8", "E9 9B 84", "雄")],
        "雄",
    )
    divergence = explain.compare_proofs(left, right, 2, _entry("雄", "encode:cp1252>decode:utf-8"))
    assert divergence["kind"] == "bytes"
    assert divergence["at_step"] == 1
    assert divergence["byte_offset"] == 2
    assert divergence["left"]["byte"] == "85"
    assert divergence["right"]["byte"] == "84"


def test_divergence_reports_the_first_differing_character():
    left = _proof([_dec(1, "cp1252", "9B", "\u203a")], "\u203a")
    right = _proof([_dec(1, "cp1252", "9B", "\u009b")], "\u009b")
    divergence = explain.compare_proofs(left, right, 2, _entry("\u009b", "decode:cp1252"))
    assert divergence["kind"] == "text"
    assert divergence["at_step"] == 1
    assert divergence["char_offset"] == 0
    assert divergence["left"]["codepoint"] == "U+203A"
    assert divergence["right"]["codepoint"] == "U+009B"


def test_divergence_reports_the_first_differing_step():
    left = _proof(
        [_enc(1, "cp1252", CLASSIC, "E9 9B 85"), _dec(2, "utf-8", "E9 9B 85", CLASSIC_TRUTH)],
        CLASSIC_TRUTH,
    )
    right = _proof(
        [_enc(1, "cp1252", CLASSIC, "E9 9B 85"), _dec(2, "latin-1", "E9 9B 85", "é›…")],
        "é›…",
    )
    divergence = explain.compare_proofs(left, right, 2, _entry("é›…", "encode:cp1252>decode:latin-1"))
    assert divergence["kind"] == "step"
    assert divergence["at_step"] == 2
    assert divergence["left"] == {"op": "decode", "codec": "utf-8"}
    assert divergence["right"] == {"op": "decode", "codec": "latin-1"}


def test_divergence_reports_depth_and_none():
    one = _proof([_enc(1, "cp1252", CLASSIC, "E9 9B 85")], "é›…")
    two = _proof(
        [_enc(1, "cp1252", CLASSIC, "E9 9B 85"), _dec(2, "latin-1", "E9 9B 85", "é›…")],
        "é›…",
    )
    divergence = explain.compare_proofs(one, two, 2, _entry("é›…", "encode:cp1252>decode:latin-1"))
    assert divergence["kind"] == "depth"
    assert divergence["at_step"] == 2
    assert divergence["left"] == {"steps": 1}
    assert divergence["right"] == {"steps": 2}

    same = explain.compare_proofs(two, two, 1, _entry("é›…", "encode:cp1252>decode:latin-1"))
    assert same["kind"] == "none"
    assert same["at_step"] is None


def test_vs_statement_states_difference_only(capsys):
    code, payload = _run_json(
        ["explain", "--text", CLASSIC, "--pick", "1", "--vs", "2"], capsys
    )
    assert code == report.EXIT_OK
    divergence = payload["proofs"][0]["divergence"]
    assert divergence["kind"] == "step"
    assert divergence["at_step"] == 2
    statement = divergence["statement"].lower()
    assert "differs" in statement
    for word in ("better", "best", "likely", "correct", "should"):
        assert word not in statement


def test_default_vs_does_not_compare_a_candidate_with_itself():
    assert explain._default_vs(1, 5) == 2
    assert explain._default_vs(2, 5) == 1
    assert explain._default_vs(3, 5) == 2
    assert explain._default_vs(1, 1) is None
    assert explain._default_vs(2, 2) == 1


def test_single_candidate_has_no_second_candidate_note(monkeypatch):
    ranked, total_chains = attr.search(CLASSIC)
    monkeypatch.setattr(explain.attr, "search", lambda text: (ranked[:1], total_chains))
    payload = explain.explain(CLASSIC, pick=1)
    assert payload["status"] == "ok"
    assert payload["total_candidates"] == 1
    assert payload["notes"] == ["no_second_candidate"]
    assert payload["proofs"][0]["divergence"] is None

    with pytest.raises(attr.UsageError):
        explain.explain(CLASSIC, pick=1, versus=2)


def test_verify_failed_status_and_exit_code(monkeypatch, capsys):
    def fake_replay(chain):
        return {"steps": [], "verify": False, "failed_step": 2, "output": None}

    monkeypatch.setattr(explain, "replay_chain", fake_replay)
    code = cli.main(["explain", "--text", CLASSIC, "--pick", "1", "--json"])
    assert code == report.EXIT_ATTENTION
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "verify_failed"
    assert payload["proofs"][0]["verify"] is False
    assert payload["proofs"][0]["failed_step"] == 2


def test_no_candidate_is_attention_not_a_fake_proof(capsys):
    code, payload = _run_json(["explain", "--text", "/", "--pick", "1"], capsys)
    assert code == report.EXIT_ATTENTION
    assert payload["status"] == "no_candidate"
    assert payload["proofs"] == []
    assert payload["notes"] == ["depth_limit_reached"]
    assert payload["pick"] == 1


def test_pick_out_of_range_exits_two_without_writing_files(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code = cli.main(["explain", "--text", CLASSIC, "--pick", "999", "--json"])
    assert code == report.EXIT_USAGE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["code"] == "pick_out_of_range"
    assert list(tmp_path.iterdir()) == []


def test_vs_out_of_range_exits_two(capsys):
    code, payload = _run_json(
        ["explain", "--text", CLASSIC, "--pick", "1", "--vs", "999"], capsys
    )
    assert code == report.EXIT_USAGE
    assert payload["code"] == "vs_out_of_range"


def test_pick_and_all_are_mutually_exclusive():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["explain", "--text", CLASSIC, "--pick", "1", "--all"])
    assert excinfo.value.code == 2


def test_all_with_vs_is_rejected():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["explain", "--text", CLASSIC, "--all", "--vs", "2"])
    assert excinfo.value.code == 2


def test_all_mode_returns_every_candidate(capsys):
    code, payload = _run_json(["explain", "--text", CLASSIC, "--all"], capsys)
    assert code == report.EXIT_OK
    assert payload["mode"] == "all"
    assert len(payload["proofs"]) == payload["total_candidates"]
    assert [proof["rank"] for proof in payload["proofs"]] == list(
        range(1, payload["total_candidates"] + 1)
    )
    assert all(proof["verify"] for proof in payload["proofs"])
    assert all(proof["divergence"] is None for proof in payload["proofs"])


def test_file_input_is_read_as_utf8(tmp_path, capsys):
    path = tmp_path / "mojibake.md"
    path.write_text(CLASSIC, encoding="utf-8")
    code, payload = _run_json(["explain", "--file", str(path), "--pick", "1"], capsys)
    assert code == report.EXIT_OK
    assert payload["status"] == "ok"
    assert payload["proofs"][0]["verify"] is True


def test_file_input_must_be_utf8(tmp_path, capsys):
    path = tmp_path / "raw.bin"
    path.write_bytes(b"\xff\xfe\x00\x00")
    code, payload = _run_json(["explain", "--file", str(path), "--pick", "1"], capsys)
    assert code == report.EXIT_USAGE
    assert payload["code"] == "file_unreadable"
    assert "`file` subcommand" in payload["message"]
    assert len(list(tmp_path.iterdir())) == 1


def test_codec_unavailable_exits_three(monkeypatch, capsys):
    monkeypatch.setattr(
        codecs_table, "missing_codecs", lambda *args, **kwargs: ("gb18030",)
    )
    code = cli.main(["explain", "--text", CLASSIC, "--pick", "1", "--json"])
    assert code == report.EXIT_ENV
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["code"] == "codec_unavailable"


def test_double_run_is_byte_identical(capsys):
    first_code = cli.main(["explain", "--text", CLASSIC, "--pick", "1", "--vs", "2", "--json"])
    first = capsys.readouterr().out
    second_code = cli.main(["explain", "--text", CLASSIC, "--pick", "1", "--vs", "2", "--json"])
    second = capsys.readouterr().out
    assert first_code == second_code == report.EXIT_OK
    assert first == second
    assert first.endswith("\n") and not first.endswith("\n\n")


def test_human_output_is_stable_and_path_free(capsys):
    first_code = cli.main(["explain", "--text", CLASSIC, "--pick", "1", "--vs", "2"])
    first = capsys.readouterr().out
    second_code = cli.main(["explain", "--text", CLASSIC, "--pick", "1", "--vs", "2"])
    second = capsys.readouterr().out
    assert first_code == second_code == report.EXIT_OK
    assert first == second
    assert "recompute: PASS" in first
    assert "divergence:" in first
    assert "not_ready" not in first
    assert os.getcwd() not in first
    assert "better" not in first.lower()
