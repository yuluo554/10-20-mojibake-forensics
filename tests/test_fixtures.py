# -*- coding: utf-8 -*-
"""Fixture truth tests (M1).

Every expectation is recomputed from a fixed input with the standard library;
the tool is only used for the scan-detection probe, never to define the truth.
"""

import hashlib
import json
import os
import subprocess
import sys

from mojibake_forensics import codecs_table
from mojibake_forensics import paths
from mojibake_forensics import score

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURES = os.path.join(ROOT, "data", "fixtures")


def _load(rel):
    path = os.path.join(FIXTURES, rel)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _generators():
    found = []
    for base, _dirs, files in os.walk(FIXTURES):
        if "gen.py" in files:
            found.append(os.path.join(base, "gen.py"))
    return sorted(found)


def _walk_observed(value, prefix=""):
    hits = []
    if isinstance(value, dict):
        for key in sorted(value):
            path = prefix + "/" + key if prefix else key
            if key.startswith("observed_"):
                hits.append(path)
            hits.extend(_walk_observed(value[key], path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_walk_observed(item, "%s[%d]" % (prefix, index)))
    return hits


def test_fixture_generators_are_discoverable():
    generators = _generators()
    assert len(generators) >= 12
    rels = [os.path.relpath(path, FIXTURES).replace(os.sep, "/") for path in generators]
    for expected in (
        "attr/gen.py",
        "explain/gen.py",
        "recover/kun-jin-kao/gen.py",
        "recover/tang-tang/gen.py",
        "recover/question-mark/gen.py",
        "recover/replacement-char/gen.py",
        "recover/silent-drop/gen.py",
        "file/bom-conflict/gen.py",
        "file/utf16-misalignment/gen.py",
        "file/zip-cjk-utf8/gen.py",
        "file/zip-cjk-cp437/gen.py",
        "scan/gen.py",
    ):
        assert expected in rels, expected


def test_every_generator_check_passes():
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    for generator in _generators():
        proc = subprocess.run(
            [sys.executable, generator, "--check"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
            env=env,
        )
        assert proc.returncode == 0, "%s\n%s" % (generator, proc.stdout)
        assert "PASS" in proc.stdout, proc.stdout


def test_every_expect_json_is_truth_only():
    for generator in _generators():
        directory = os.path.dirname(generator)
        path = os.path.join(directory, "expect.json")
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        assert _walk_observed(payload) == [], path
        for key in ("input", "expected", "criteria", "note"):
            assert key in payload, (path, key)
        assert payload["criteria"]["max_depth"] == 3


def test_fixture_criteria_matches_frozen_codecs_table():
    """Fixtures hardcode the frozen sets; drift must fail here, not in M5."""
    expected = {
        "encoders": list(codecs_table.ENCODERS),
        "decoders": list(codecs_table.DECODERS),
        "max_depth": codecs_table.MAX_DEPTH,
    }
    for generator in _generators():
        path = os.path.join(os.path.dirname(generator), "expect.json")
        with open(path, "r", encoding="utf-8") as handle:
            criteria = json.load(handle)["criteria"]
        for key, value in expected.items():
            assert criteria[key] == value, (path, key)


def _replay_steps(steps):
    state = steps[0]["input"]
    for step in steps:
        if step["op"] == "encode":
            assert isinstance(state, str)
            state = state.encode(step["codec"])
        else:
            assert isinstance(state, bytes)
            state = state.decode(step["codec"])
    return state


def test_attr_fixture_chains_replay_to_truth():
    payload = _load("attr/expect.json")
    inputs = dict((case["id"], case["text"]) for case in payload["input"]["cases"])
    assert payload["expected"]["candidates_are_always_a_list"] is True
    for case in payload["expected"]["cases"]:
        assert case["status"] == "candidates"
        assert inputs[case["id"]] != case["truth"]
        assert _replay_steps(case["steps"]) == case["truth"]
        assert case["truth_in_candidates"] is True
        assert case["chain"].startswith("encode:")


def test_explain_fixture_positive_and_negative():
    payload = _load("explain/expect.json")
    text = payload["input"]["text"]
    positive = payload["expected"]["positive"]
    assert _replay_steps(positive["steps"]) == positive["result"]
    assert positive["verify"] is True
    assert positive["failed_step"] is None

    negative = payload["expected"]["negative"]
    assert negative["verify"] is False
    parts = [item.split(":", 1) for item in payload["input"]["negative_chain"].split(">")]
    state = text
    failed = None
    for index, (op, codec) in enumerate(parts, 1):
        try:
            state = state.encode(codec) if op == "encode" else state.decode(codec)
        except (UnicodeEncodeError, UnicodeDecodeError):
            failed = index
            break
    assert failed == negative["failed_step"] == 2
    assert negative["byte_offset"] == 2


def _recover_case(rel):
    payload = _load("recover/%s/expect.json" % rel)
    input_block = payload["input"]
    construction = input_block["construction"]
    expected = payload["expected"]

    kind = construction["kind"]
    if kind == "bytes_decode":
        raw = bytes.fromhex(construction["bytes_hex"])
        assert raw.decode(construction["codec"]) == input_block["text"]
    elif kind == "fill_byte_decode":
        assert construction["fill_bytes"] == ["CC", "CD"]
        for fill, expected_text in (
            ("CC", input_block["text"]),
            ("CD", input_block["alternative_text"]),
        ):
            raw = bytes.fromhex(construction["bytes_hex"][fill])
            assert raw == bytes([int(fill, 16)]) * construction["repeat"]
            assert raw.decode(construction["codec"]) == expected_text
    elif kind == "encode_errors_replace":
        raw = construction["original"].encode(
            construction["encode"], construction["errors"]
        )
        assert raw.decode(construction["decode"]) == input_block["text"]
        assert raw.hex().upper().replace(" ", "") == construction["bytes_hex"].replace(" ", "")
    elif kind == "decode_errors_replace":
        raw = bytes.fromhex(construction["bytes_hex"])
        assert raw.decode(construction["decode"], construction["errors"]) == input_block["text"]
    elif kind == "encode_errors_ignore":
        raw = construction["original"].encode(
            construction["encode"], construction["errors"]
        )
        assert raw.decode(construction["decode"]) == input_block["text"]
        assert construction["original"] != input_block["text"]
    else:
        raise AssertionError("unknown construction kind: %r" % kind)

    assert expected["recovered"] is None
    assert expected["contains_tool_invented_chars"] is False
    return payload


def test_recover_five_irreversible_classes():
    expected = {
        "kun-jin-kao": ("LOST", "kun_jin_kao"),
        "tang-tang": ("NOT_MOJIBAKE", "msvc_fill"),
        "question-mark": ("LOST", "encode_truncated"),
        "replacement-char": ("LOST", "replacement_char"),
        "silent-drop": ("LOST", "silent_drop"),
    }
    for name, (status, reason) in expected.items():
        payload = _recover_case(name)
        assert payload["expected"]["status"] == status, name
        assert payload["expected"]["reason"] == reason, name
        if status == "LOST":
            loss = payload["expected"]["loss"]
            assert loss is not None, name
            assert "offset" in loss, name
        else:
            assert payload["expected"]["loss"] is None, name


def test_silent_drop_is_not_claimed_from_visible_text_alone():
    payload = _load("recover/silent-drop/expect.json")
    assert payload["input"]["text"] == "ab"
    assert payload["expected"]["requires_provenance"] is True
    assert "雅" not in payload["input"]["text"]


def test_file_fixtures_are_frozen_and_read_only_evidence():
    expectations = {
        "bom-conflict": "bom-conflict.bin",
        "utf16-misalignment": "utf16-misalignment.bin",
        "zip-cjk-utf8": "zip-cjk-utf8.zip",
        "zip-cjk-cp437": "zip-cjk-cp437.zip",
    }
    for name, artifact in expectations.items():
        payload = _load("file/%s/expect.json" % name)
        path = os.path.join(FIXTURES, "file", name, artifact)
        with open(path, "rb") as handle:
            data = handle.read()
        assert os.path.getsize(path) == len(data)
        assert hashlib.sha256(data).hexdigest() == payload["input"]["sha256"]
        if "archive_sha256" in payload["expected"]:
            assert payload["expected"]["archive_sha256"] == payload["input"]["sha256"]
        assert payload["expected"]["mutates_input"] is False
        assert payload["input"]["path"] == artifact

    bom = _load("file/bom-conflict/expect.json")["expected"]
    assert bom["bom_conflict"] is True
    assert bom["bom"]["bytes_hex"] == "EF BB BF"
    assert bom["content"]["as_utf8"]["decodable"] is False
    assert bom["content"]["as_gb18030"]["text"] == "中文"

    utf16 = _load("file/utf16-misalignment/expect.json")["expected"]["utf16_misalignment"]
    assert utf16["byte_length"] % 2 == 1
    assert utf16["shift_offset"] == 1
    with open(os.path.join(FIXTURES, "file", "utf16-misalignment", "utf16-misalignment.bin"), "rb") as handle:
        data = handle.read()
    assert data[1:].decode("utf-16-le") == utf16["shifted_text"] == "中文测试"

    import zipfile

    utf8 = _load("file/zip-cjk-utf8/expect.json")["expected"]
    assert utf8["zip_names"][0]["flag_utf8"] is True
    with zipfile.ZipFile(os.path.join(FIXTURES, "file", "zip-cjk-utf8", "zip-cjk-utf8.zip")) as archive:
        info = archive.infolist()[0]
        assert info.flag_bits & 0x800
        assert info.filename == "中文.txt"

    cp437 = _load("file/zip-cjk-cp437/expect.json")["expected"]
    assert cp437["zip_names"][0]["flag_utf8"] is False
    with zipfile.ZipFile(os.path.join(FIXTURES, "file", "zip-cjk-cp437", "zip-cjk-cp437.zip")) as archive:
        info = archive.infolist()[0]
        assert not info.flag_bits & 0x800
        assert info.filename == cp437["zip_names"][0]["name"]
        assert info.filename != "中文.txt"


def _detect(text):
    """M1 scan probe: the §4.8 hit rule, applied per non-empty line."""
    hits = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        input_readability = score.readability(line)
        if input_readability >= 0.5:
            continue
        chains = paths.collapse_by_result(paths.enumerate_chains(line, max_depth=3))
        best = None
        for chain in chains:
            readability = score.readability(chain.result)
            if best is None or readability > best:
                best = readability
        if best is not None and best >= 0.8 and best - input_readability >= 0.3:
            hits.append((line_number, chains))
    return hits


def test_scan_hit_thresholds_match_documented_values():
    criteria = _load("scan/expect.json")["criteria"]["scan_hit"]
    assert criteria == {
        "input_readability_below": 0.5,
        "candidate_readability_at_least": 0.8,
        "readability_gain_at_least": 0.3,
    }


def test_clean_corpus_baseline_has_no_text_and_no_hits():
    baseline_path = os.path.join(FIXTURES, "scan", "clean-corpus.json")
    with open(baseline_path, "r", encoding="utf-8") as handle:
        raw = handle.read()
    payload = json.loads(raw)
    assert payload["expected_new"] == []
    assert payload["sample_size"]["files"] == len(payload["files"]) == 10
    assert payload["sample_size"]["chars"] > 0
    for char in raw:
        code = ord(char)
        assert not (0x4E00 <= code <= 0x9FFF), "baseline must not contain CJK text"
        assert not (0x3040 <= code <= 0x30FF), "baseline must not contain kana text"
        assert not (0xAC00 <= code <= 0xD7AF), "baseline must not contain hangul text"

    for item in payload["files"]:
        path = os.path.join(FIXTURES, "scan", item["path"])
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        hits = _detect(text)
        assert hits == [], item["path"]
        assert item["allowed_hits"] == []


def test_polluted_corpus_is_detected_and_truth_is_in_candidates():
    payload = _load("scan/expect.json")
    for item in payload["expected"]["polluted"]["new"]:
        path = os.path.join(FIXTURES, "scan", item["path"])
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        hits = _detect(text)
        assert hits, item["path"]
        results = []
        for _line_number, chains in hits:
            results.extend(chain.result for chain in chains)
        assert item["candidate_contains"] in results, item["path"]
    assert payload["expected"]["clean"]["new"] == []
    assert payload["expected"]["polluted"]["exit_code"] == 1
