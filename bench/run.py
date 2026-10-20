#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""57-case probe benchmark: programmatic generation + lossless replay.

Probe shape (``data/README.md`` §1.3.1 / §4.2): 10 encoders x 7 decoders,
chain depth 2, 10 synthetic CJK samples x 8 incident scenarios = 57 usable
cases. The one-off pre-M1 script described 6 decoders; the frozen
``codecs_table.DECODERS`` has 7, so M1 recomputes with 7.

The probe is a **small-sample feasibility probe, not a product metric**. The
only hard gate is "the true answer is inside the candidate set" (criterion
correctness, not performance).

M2 adds a ``depth3`` block: the real ``attr`` command re-runs the same 57 cases
at the frozen ``MAX_DEPTH`` and records its complete candidate/chain counts.

Determinism: no clock, no randomness, no host paths, no Python version in the
payload. ``--check`` recomputes the payload and compares it byte-for-byte with
``bench/golden/attr.json``.
"""

from __future__ import print_function

import argparse
import os
import statistics
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GOLDEN = os.path.join(ROOT, "bench", "golden", "attr.json")
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from mojibake_forensics import attr as attr_cmd  # noqa: E402
from mojibake_forensics import codecs_table  # noqa: E402
from mojibake_forensics import paths  # noqa: E402
from mojibake_forensics import report  # noqa: E402
from mojibake_forensics import score  # noqa: E402


# The depth-3 block runs the real ``attr`` command with a display cut that is
# far above any observed candidate count, so the counts reported are complete.
ATTR_FULL_TOP = 10 ** 9


PROBE = {
    "encoders": len(codecs_table.ENCODERS),
    "decoders": len(codecs_table.DECODERS),
    "depth": 2,
    "samples": 10,
    "scenarios": 8,
    "cases": 57,
    "note": "small-sample feasibility probe, not a product metric",
}

# Fixed synthetic samples (self-written; no real company/person/client data).
SAMPLES = (
    ("zh1", "zh", "字符显示异常"),
    ("zh2", "zh", "编码事故调查"),
    ("zh3", "zh", "中文注释显示乱码"),
    ("zh4", "zh", "中文測試"),
    ("ja1", "ja", "日本語のテスト"),
    ("ja2", "ja", "文字化け調査"),
    ("ja3", "ja", "東京の資料"),
    ("ko1", "ko", "한국어 테스트"),
    ("ko2", "ko", "인코딩 오류"),
    ("ko3", "ko", "서울 자료"),
)

# Eight incident scenarios: original -> encode(A) -> decode(B) -> mojibake.
SCENARIOS = (
    ("utf8-latin1", "utf-8", "latin-1"),
    ("utf8-cp437", "utf-8", "cp437"),
    ("gb18030-latin1", "gb18030", "latin-1"),
    ("gb18030-cp437", "gb18030", "cp437"),
    ("utf8-cp1252", "utf-8", "cp1252"),
    ("sjis-latin1", "shift_jis", "latin-1"),
    ("euckr-latin1", "euc-kr", "latin-1"),
    ("big5-latin1", "big5", "latin-1"),
)


def _truth_chain(encoder, decoder):
    return paths.Chain(
        steps=(
            paths.Step(
                index=1,
                op="encode",
                codec=decoder,
                input_text=None,
                output_hex=None,
            ),
            paths.Step(
                index=2,
                op="decode",
                codec=encoder,
                input_text=None,
                output_hex=None,
            ),
        )
    )


def _case(sample_id, language, truth, scenario_id, encoder, decoder, corrupted):
    """Build one reproducible case, including its replayable truth chain."""
    chain = _truth_chain(encoder, decoder)
    # The truth chain is valid iff the reverse replay returns the original.
    truth_chain_ok = (
        paths.verify_lossless(corrupted, chain) and paths.replay(corrupted, chain) == truth
    )

    all_chains = paths.enumerate_chains(corrupted, max_depth=PROBE["depth"])
    minimal_chains = [chain for chain in all_chains if chain.depth == 1]
    minimal = paths.collapse_by_result(minimal_chains)
    expanded = paths.collapse_by_result(all_chains)

    minimal_ranked = score.rank(minimal)
    expanded_ranked = score.rank(expanded)

    truth_rank_minimal = _rank_of(minimal_ranked, truth)
    truth_rank_expanded = _rank_of(expanded_ranked, truth)

    return {
        "id": "%s/%s" % (sample_id, scenario_id),
        "sample": sample_id,
        "language": language,
        "scenario": scenario_id,
        "truth": truth,
        "input": corrupted,
        "truth_chain": {
            "path_string": "encode:%s>decode:%s" % (decoder, encoder),
            "verify": bool(truth_chain_ok),
        },
        "minimal_candidate_count": len(minimal),
        "expanded_candidate_count": len(expanded),
        "truth_in_minimal": truth_rank_minimal is not None,
        "truth_in_expanded": truth_rank_expanded is not None,
        "truth_rank_minimal": truth_rank_minimal,
        "truth_rank_expanded": truth_rank_expanded,
        "minimal_candidates": [_candidate_entry(entry) for entry in minimal_ranked],
    }


def _candidate_entry(entry):
    return {
        "rank": entry["rank"],
        "result": entry["result"],
        "path_string": entry["path_string"],
        "depth": entry["depth"],
        "score_total": round(entry["score"]["total"], 12),
    }


def _rank_of(ranked, truth):
    for entry in ranked:
        if entry["result"] == truth:
            return entry["rank"]
    return None


def _size_stats(values):
    return {
        "median": round(float(statistics.median(values)), 6),
        "mean": round(float(statistics.mean(values)), 6),
        "max": max(values),
        "min": min(values),
    }


def _depth3_block(cases):
    """Measure ``attr`` at the frozen ``MAX_DEPTH`` over the same 57 cases.

    This is the M2 hard gate: the true answer must stay inside the candidate
    set when the search runs at the product depth. Numbers are recorded, never
    used as thresholds.
    """
    counts = []
    chain_counts = []
    truth_in = 0
    truth_first = 0
    rows = []
    for case in cases:
        payload = attr_cmd.attribute(case["input"], top=ATTR_FULL_TOP)
        candidates = payload["candidates"]
        counts.append(payload["total_candidates"])
        chain_counts.append(payload["total_chains"])
        truth_rank = None
        for candidate in candidates:
            if candidate["result"] == case["truth"]:
                truth_rank = candidate["rank"]
                break
        if truth_rank is not None:
            truth_in += 1
        if truth_rank == 1:
            truth_first += 1
        rows.append(
            {
                "id": case["id"],
                "total_candidates": payload["total_candidates"],
                "total_chains": payload["total_chains"],
                "truth_rank": truth_rank,
            }
        )

    total = len(cases)
    return {
        "measured": True,
        "max_depth": codecs_table.MAX_DEPTH,
        "cases_total": total,
        "candidate_size": _size_stats(counts),
        "chain_count": _size_stats(chain_counts),
        "truth_in_candidates": truth_in,
        "truth_first": truth_first,
        "truth_first_rate": round(truth_first / float(total), 6),
        "cases": rows,
        "note": (
            "measured by attr at MAX_DEPTH=%d over the same %d probe cases (M2); "
            "small-sample feasibility evidence, not a product metric"
            % (codecs_table.MAX_DEPTH, total)
        ),
    }


def build_payload():
    cases = []
    usable_by_scenario = dict((scenario_id, 0) for scenario_id, _, _ in SCENARIOS)

    for sample_id, language, truth in SAMPLES:
        for scenario_id, encoder, decoder in SCENARIOS:
            try:
                raw = truth.encode(encoder)
                corrupted = raw.decode(decoder)
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            if corrupted == truth:
                continue
            truth_chain = _truth_chain(encoder, decoder)
            if not paths.verify_lossless(corrupted, truth_chain):
                continue
            if paths.replay(corrupted, truth_chain) != truth:
                continue

            case = _case(
                sample_id,
                language,
                truth,
                scenario_id,
                encoder,
                decoder,
                corrupted,
            )
            cases.append(case)
            usable_by_scenario[scenario_id] += 1

    if len(cases) != PROBE["cases"]:
        raise RuntimeError(
            "probe matrix drifted: expected %d cases, generated %d"
            % (PROBE["cases"], len(cases))
        )

    minimal_counts = [case["minimal_candidate_count"] for case in cases]
    expanded_counts = [case["expanded_candidate_count"] for case in cases]
    total = len(cases)

    metrics = {
        "cases_total": total,
        "usable_by_scenario": usable_by_scenario,
        "candidate_size_minimal": _size_stats(minimal_counts),
        "candidate_size_expanded": _size_stats(expanded_counts),
        "single_candidate_cases_minimal": sum(
            1 for count in minimal_counts if count == 1
        ),
        "truth_in_minimal": sum(1 for case in cases if case["truth_in_minimal"]),
        "truth_in_expanded": sum(1 for case in cases if case["truth_in_expanded"]),
        "truth_first_minimal": sum(
            1 for case in cases if case["truth_rank_minimal"] == 1
        ),
        "truth_first_expanded": sum(
            1 for case in cases if case["truth_rank_expanded"] == 1
        ),
        "truth_first_rate_minimal": round(
            sum(1 for case in cases if case["truth_rank_minimal"] == 1) / float(total),
            6,
        ),
        "truth_first_rate_expanded": round(
            sum(1 for case in cases if case["truth_rank_expanded"] == 1) / float(total),
            6,
        ),
    }

    return {
        "schema": "mojibake-forensics/bench/1",
        "probe": dict(PROBE),
        "matrix": {
            "samples": [
                {"id": sample_id, "language": language, "text": truth}
                for sample_id, language, truth in SAMPLES
            ],
            "scenarios": [
                {"id": scenario_id, "encode": encoder, "decode": decoder}
                for scenario_id, encoder, decoder in SCENARIOS
            ],
        },
        "metrics": metrics,
        "cases": cases,
        "depth3": _depth3_block(cases),
        "notes": [
            PROBE["note"],
            "candidate set = distinct recovered texts; one representative chain per text",
            "minimal = depth-1 lossless recoveries; expanded = depth <= 2",
            "depth3 = attr at MAX_DEPTH over the same cases (M2); counts are complete, not top-N",
            "this file is the reproducible record; the pre-M1 one-off script was not archived",
        ],
    }


def _summary(payload):
    metrics = payload["metrics"]
    minimal = metrics["candidate_size_minimal"]
    expanded = metrics["candidate_size_expanded"]
    depth3 = payload["depth3"]
    total = metrics["cases_total"]
    lines = [
        "bench: %d cases (%d samples x %d scenarios, depth %d)"
        % (
            total,
            PROBE["samples"],
            PROBE["scenarios"],
            PROBE["depth"],
        ),
        "minimal candidates: median=%s mean=%s max=%s"
        % (minimal["median"], minimal["mean"], minimal["max"]),
        "expanded candidates: median=%s mean=%s max=%s"
        % (expanded["median"], expanded["mean"], expanded["max"]),
        "truth in minimal: %d/%d" % (metrics["truth_in_minimal"], total),
        "truth in expanded: %d/%d" % (metrics["truth_in_expanded"], total),
        "truth first (minimal): %d/%d (%s)"
        % (
            metrics["truth_first_minimal"],
            total,
            metrics["truth_first_rate_minimal"],
        ),
        "depth %d via attr: candidates median=%s max=%s; truth in set %d/%d"
        % (
            depth3["max_depth"],
            depth3["candidate_size"]["median"],
            depth3["candidate_size"]["max"],
            depth3["truth_in_candidates"],
            total,
        ),
    ]
    return "\n".join(lines)


def _write(path, text):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description="57-case mojibake attribution probe")
    parser.add_argument(
        "--out", default=os.path.join(ROOT, "bench", "out", "attr.json")
    )
    parser.add_argument(
        "--check", action="store_true", help="recompute and compare with bench/golden/attr.json"
    )
    parser.add_argument(
        "--freeze", action="store_true", help="write bench/golden/attr.json (M1 freeze step)"
    )
    args = parser.parse_args(argv)

    if args.check and args.freeze:
        parser.error("--check and --freeze are mutually exclusive")

    try:
        codecs_table.ensure_codecs()
    except codecs_table.CodecUnavailable as exc:
        print("bench: %s" % exc)
        return report.EXIT_ENV

    try:
        payload = build_payload()
    except RuntimeError as exc:
        print("bench: %s" % exc)
        return report.EXIT_ATTENTION

    text = report.dumps(payload)

    if args.check:
        if not os.path.exists(GOLDEN):
            print("bench: golden missing: bench/golden/attr.json")
            return report.EXIT_ATTENTION
        with open(GOLDEN, "r", encoding="utf-8", newline=None) as handle:
            frozen = handle.read()
        if frozen != text:
            print("bench: golden differs from recomputation")
            return report.EXIT_ATTENTION
        print("bench: golden matches")
        print(_summary(payload))
        return report.EXIT_OK

    if args.freeze:
        _write(GOLDEN, text)
        print("bench: froze bench/golden/attr.json")
        print(_summary(payload))
        return report.EXIT_OK

    _write(args.out, text)
    print(_summary(payload))
    try:
        shown = os.path.relpath(args.out, ROOT)
    except ValueError:
        shown = args.out
    print("wrote %s" % shown)
    return report.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
