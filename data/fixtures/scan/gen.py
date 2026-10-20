#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan fixture generator (M1): clean corpus baseline + polluted corpus.

The baseline JSON contains **statistics and relative paths only**; no corpus
text is copied into it. The clean files themselves are synthetic short
sentences (self-written), not sampled real-world text.
"""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.dirname(FIXTURE_DIR)
if FIXTURES_DIR not in sys.path:
    sys.path.insert(0, FIXTURES_DIR)

import genlib  # noqa: E402


CLEAN_FILES = (
    ("clean/zh-01.md", "# 合成样本\n\n这是一段干净的说明文字。\n"),
    ("clean/zh-02.md", "编码说明：本文档只用于误报基线。\n"),
    ("clean/zh-03.md", "表格与字段名称均为合成样本。\n"),
    ("clean/ja-01.md", "日本語のテスト文です。\n"),
    ("clean/ja-02.md", "文字化けではありません。\n"),
    ("clean/ko-01.md", "한국어 테스트 문장입니다.\n"),
    ("clean/ko-02.md", "인코딩 오류가 없습니다.\n"),
    ("clean/en-01.md", "Clean ASCII baseline line.\n"),
    ("clean/en-02.md", "# Fixture header\n\nNo mojibake here.\n"),
    ("clean/mixed-01.md", "合成样本 fixture line 42\n"),
)

POLLUTED_FILES = (
    # (path, truth, corruption encoder, corruption decoder)
    ("polluted/zh.md", "中文測試", "utf-8", "latin-1"),
    ("polluted/ja.md", "日本語", "utf-8", "cp437"),
)


def _stats(text):
    counts = {
        "ascii": 0,
        "cjk": 0,
        "kana": 0,
        "hangul": 0,
        "controls": 0,
        "other": 0,
    }
    for char in text:
        code = ord(char)
        if char in "\t\n\r":
            continue
        if 0x20 <= code <= 0x7E:
            counts["ascii"] += 1
        elif 0x4E00 <= code <= 0x9FFF:
            counts["cjk"] += 1
        elif 0x3040 <= code <= 0x30FF:
            counts["kana"] += 1
        elif 0xAC00 <= code <= 0xD7AF:
            counts["hangul"] += 1
        elif code < 0x20 or code == 0x7F:
            counts["controls"] += 1
        else:
            counts["other"] += 1
    counts["chars"] = len(text)
    counts["lines"] = text.count("\n") if text.endswith("\n") else text.count("\n") + 1
    counts["utf8_decodable"] = True
    return counts


def build():
    artifacts = {}
    baseline_files = []

    for rel, text in CLEAN_FILES:
        data = text.encode("utf-8")
        artifacts[rel] = data
        baseline_files.append(
            {
                "path": rel,
                "allowed_hits": [],
                "stats": _stats(text),
            }
        )

    total_chars = sum(item["stats"]["chars"] for item in baseline_files)
    total_lines = sum(item["stats"]["lines"] for item in baseline_files)
    baseline = {
        "schema": "mojibake-forensics/clean-corpus/1",
        "source_category": "synthetic-clean-sentences",
        "sample_size": {
            "files": len(baseline_files),
            "chars": total_chars,
            "lines": total_lines,
        },
        "files": sorted(baseline_files, key=lambda item: item["path"]),
        "expected_new": [],
        "note": "statistics and relative paths only; no corpus text is stored here",
    }

    polluted_expected = []
    for rel, truth, encoder, decoder in POLLUTED_FILES:
        raw, corrupted = genlib.transform(truth, encoder, decoder)
        artifacts[rel] = (corrupted + "\n").encode("utf-8")
        polluted_expected.append(
            {
                "path": rel,
                "candidate_contains": truth,
                "corruption_chain": "encode:%s>decode:%s" % (encoder, decoder),
                "truth_bytes_hex": genlib.hexdump(raw),
                "category": "mojibake",
            }
        )

    payload = {
        "input": {
            "directory": ".",
            "baseline": "clean-corpus.json",
            "clean_files": [item["path"] for item in baseline_files],
            "polluted_files": [item["path"] for item in polluted_expected],
        },
        "expected": {
            "clean": {
                "new": [],
                "baselined": [],
                "stale": [],
                "exit_code": 0,
                "files_scanned": len(baseline_files),
            },
            "polluted": {
                "new": sorted(polluted_expected, key=lambda item: item["path"]),
                "exit_code": 1,
            },
            "stale_probe": {
                "virtual_missing_path": "clean/missing.md",
                "bucket": "stale",
                "exit_code_effect": "none",
            },
        },
        "criteria": {
            "encoders": [
                "utf-8",
                "gb18030",
                "gbk",
                "big5",
                "shift_jis",
                "euc-jp",
                "euc-kr",
                "cp1252",
                "latin-1",
                "cp437",
            ],
            "decoders": [
                "utf-8",
                "gb18030",
                "big5",
                "shift_jis",
                "euc-kr",
                "cp1252",
                "latin-1",
            ],
            "max_depth": 3,
            "scan_hit": {
                "input_readability_below": 0.5,
                "candidate_readability_at_least": 0.8,
                "readability_gain_at_least": 0.3,
            },
        },
        "note": "M5 consumes this fixture; clean must be 0 new / 0 file changes",
    }
    artifacts["clean-corpus.json"] = genlib.canonical_json(baseline).encode("utf-8")
    return payload, artifacts


if __name__ == "__main__":
    sys.exit(
        genlib.run(
            build,
            FIXTURE_DIR,
            description="scan fixture generator (M1)",
        )
    )
