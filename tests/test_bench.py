# -*- coding: utf-8 -*-
"""57-case bench tests (M1).

The bench is a small-sample feasibility probe, not a product metric. These
tests lock the *structure* and the one hard gate (truth in the candidate set),
never a particular candidate-size number.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BENCH = os.path.join(ROOT, "bench", "run.py")
GOLDEN = os.path.join(ROOT, "bench", "golden", "attr.json")


def _run(*args):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, BENCH] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding="utf-8",
        env=env,
    )


def _golden_text():
    with open(GOLDEN, "r", encoding="utf-8") as handle:
        return handle.read()


def _load_golden():
    return json.loads(_golden_text())


def test_bench_check_is_green():
    proc = _run("--check")
    assert proc.returncode == 0, proc.stdout
    assert "golden matches" in proc.stdout
    assert "57 cases" in proc.stdout


def test_bench_check_is_deterministic():
    first = _run("--check")
    second = _run("--check")
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout


def test_golden_shape_and_hard_gate():
    payload = _load_golden()
    probe = payload["probe"]
    assert probe["cases"] == 57
    assert probe["samples"] == 10
    assert probe["scenarios"] == 8
    assert probe["depth"] == 2
    assert probe["encoders"] == 10
    assert probe["decoders"] == 7

    metrics = payload["metrics"]
    assert metrics["cases_total"] == 57
    assert sum(metrics["usable_by_scenario"].values()) == 57
    assert metrics["truth_in_minimal"] == 57
    assert metrics["truth_in_expanded"] == 57
    assert metrics["single_candidate_cases_minimal"] == 0
    assert 0 <= metrics["truth_first_minimal"] <= 57
    assert metrics["candidate_size_minimal"]["max"] >= 1
    assert metrics["candidate_size_expanded"]["max"] >= metrics["candidate_size_minimal"]["max"]

    assert payload["depth3"]["measured"] is True
    assert payload["depth3"]["max_depth"] == 3
    assert payload["depth3"]["cases_total"] == 57
    assert payload["depth3"]["truth_in_candidates"] == 57
    assert len(payload["depth3"]["cases"]) == 57
    assert (
        payload["depth3"]["candidate_size"]["max"]
        >= metrics["candidate_size_expanded"]["max"]
    )
    assert len(payload["cases"]) == 57


def test_depth3_keeps_every_truth_in_the_candidate_set():
    """M2 hard gate: at the product depth the true answer is never lost."""
    depth3 = _load_golden()["depth3"]
    for case in depth3["cases"]:
        assert case["truth_rank"] is not None, case["id"]
        assert case["truth_rank"] >= 1, case["id"]
        assert case["total_candidates"] >= 1, case["id"]
        assert case["total_chains"] >= case["total_candidates"], case["id"]


def test_every_case_has_a_verifiable_truth_chain():
    payload = _load_golden()
    for case in payload["cases"]:
        assert case["truth_chain"]["verify"] is True, case["id"]
        assert case["truth_in_minimal"] is True, case["id"]
        assert case["truth_in_expanded"] is True, case["id"]
        results = [item["result"] for item in case["minimal_candidates"]]
        assert case["truth"] in results, case["id"]
        assert case["minimal_candidate_count"] == len(case["minimal_candidates"])
        assert case["input"] != case["truth"]


def test_golden_is_canonical_json():
    text = _golden_text()
    assert text.endswith("\n")
    assert not text.endswith("\n\n")
    payload = json.loads(text)
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    assert canonical == text


def test_golden_has_no_host_or_absolute_paths():
    payload = _load_golden()
    needles = [ROOT, "C:\\", "\\\\Users\\\\", "/home/", "/Users/", "ASUS", "AppData"]

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                for nested in walk(item):
                    yield nested
        elif isinstance(value, list):
            for item in value:
                for nested in walk(item):
                    yield nested
        elif isinstance(value, str):
            yield value

    for item in walk(payload):
        for needle in needles:
            assert needle not in item, (needle, item)


def test_bench_write_matches_golden(tmp_path):
    out = os.path.join(str(tmp_path), "attr.json")
    proc = _run("--out", out)
    assert proc.returncode == 0, proc.stdout
    with open(out, "r", encoding="utf-8") as handle:
        written = handle.read()
    assert written == _golden_text()


def test_bench_output_has_no_timestamps():
    payload = _load_golden()

    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                for nested in keys(item):
                    yield nested
        elif isinstance(value, list):
            for item in value:
                for nested in keys(item):
                    yield nested

    forbidden = ("timestamp", "generated_at", "hostname", "run_id", "elapsed")
    for key in keys(payload):
        assert key not in forbidden, key
