# -*- coding: utf-8 -*-
from mojibake_forensics import paths
from mojibake_forensics import score


def _chain(result, depth, path_string):
    pairs = []
    for _level in range(depth):
        pairs.append(("encode", "latin-1"))
        pairs.append(("decode", "utf-8"))
    steps = tuple(
        paths.Step(index=index + 1, op=op, codec=codec, output_text=result)
        for index, (op, codec) in enumerate(pairs)
    )
    chain = paths.Chain(steps=steps)
    return chain


def test_readability_classes():
    assert score.readability("") == 0.0
    assert score.readability("中文") == 1.0
    assert score.readability("日本語") == 1.0
    assert score.readability("한국어") == 1.0
    assert round(score.readability("abc"), 6) == 0.2
    assert round(score.readability("é"), 6) == 0.1
    assert round(score.readability("…"), 6) == 0.0
    assert round(score.readability("\ufffd"), 6) == -1.0  # -1.5 clamped to the documented range
    assert round(score.readability("\x00"), 6) == -1.0
    assert round(score.readability("ｱ"), 6) == -0.5


def test_depth_score_is_shallow_first():
    assert score.depth_score(0) == 1.0
    assert score.depth_score(1) == 0.5
    assert round(score.depth_score(2), 6) == round(1.0 / 3.0, 6)


def test_rank_uses_frozen_sort_key():
    shallow = _chain("中文", 1, "encode:latin-1>decode:utf-8")
    deep = _chain("中文", 2, "encode:latin-1>decode:utf-8>encode:latin-1>decode:utf-8")
    ranked = score.rank([deep, shallow])
    assert [entry["depth"] for entry in ranked] == [1, 2]
    assert ranked[0]["rank"] == 1
    assert ranked[0]["score"]["readability"] == 1.0
    assert ranked[0]["score"]["depth"] == 0.5
    assert ranked[0]["score"]["language"] == 0.0
    assert ranked[0]["score"]["total"] == 1.25


def test_sort_key_ties_break_on_path_string():
    entries = [
        {"score_total": 1.0, "depth": 1, "path_string": "encode:utf-8>decode:latin-1"},
        {"score_total": 1.0, "depth": 1, "path_string": "encode:cp1252>decode:utf-8"},
    ]
    entries.sort(key=score.sort_key)
    assert entries[0]["path_string"] == "encode:cp1252>decode:utf-8"


def test_sort_key_accepts_nested_score():
    entry = {"score": {"total": 0.5}, "depth": 1, "path_string": "x"}
    assert score.sort_key(entry) == (-0.5, 1, "x")
