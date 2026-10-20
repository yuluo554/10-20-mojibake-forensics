# -*- coding: utf-8 -*-
from mojibake_forensics import paths


def test_hexdump_is_uppercase_single_spaced():
    assert paths.hexdump(b"\x65\xc3\x8b") == "65 C3 8B"


def test_chain_depth_counts_decode_steps():
    chain = paths.Chain(
        steps=(
            paths.Step(index=1, op="encode", codec="cp1252"),
            paths.Step(index=2, op="decode", codec="utf-8"),
            paths.Step(index=3, op="encode", codec="cp1252"),
            paths.Step(index=4, op="decode", codec="utf-8"),
        )
    )
    assert chain.depth == 2


def test_path_string_is_canonical():
    chain = paths.Chain(
        steps=(
            paths.Step(index=1, op="encode", codec="cp1252"),
            paths.Step(index=2, op="decode", codec="utf-8"),
        )
    )
    assert chain.path_string == "encode:cp1252>decode:utf-8"
    assert chain.path == [
        {"op": "encode", "codec": "cp1252"},
        {"op": "decode", "codec": "utf-8"},
    ]


def test_chain_as_dict_keeps_steps():
    chain = paths.Chain(
        steps=(
            paths.Step(index=1, op="encode", codec="cp1252", input_text="é", output_hex="E9"),
        )
    )
    payload = chain.as_dict()
    assert payload["depth"] == 0
    assert payload["steps"][0]["output_hex"] == "E9"


def test_validate_depth_rejects_zero():
    try:
        paths.validate_depth(0)
    except ValueError:
        return
    raise AssertionError("validate_depth(0) must raise")


def _chain(*pairs):
    return paths.Chain(
        steps=tuple(
            paths.Step(index=index + 1, op=op, codec=codec)
            for index, (op, codec) in enumerate(pairs)
        )
    )


def test_verify_lossless_accepts_truth_chain():
    text = "é›…"
    chain = _chain(("encode", "cp1252"), ("decode", "utf-8"))
    assert paths.verify_lossless(text, chain) is True
    assert paths.replay(text, chain) == "雅"


def test_verify_lossless_rejects_mutated_chain():
    text = "é›…"
    chain = _chain(("encode", "cp1252"), ("decode", "gb18030"))
    assert paths.verify_lossless(text, chain) is False
    assert paths.replay(text, chain) is None


def test_enumerate_chains_includes_truth_and_respects_depth():
    text = "é›…"
    chains = paths.enumerate_chains(text, max_depth=2)
    results = [chain.result for chain in chains]
    assert "雅" in results
    assert all(chain.depth <= 2 for chain in chains)
    assert all(chain.steps[0].op == "encode" for chain in chains)
    assert all(chain.steps[-1].op == "decode" for chain in chains)
    assert all(chain.result != text for chain in chains)
    assert all(paths.verify_lossless(text, chain) for chain in chains)


def test_enumerate_chains_depth_one_only():
    chains = paths.enumerate_chains("é›…", max_depth=1)
    assert chains
    assert all(chain.depth == 1 for chain in chains)
    assert "encode:cp1252>decode:utf-8" in [chain.path_string for chain in chains]


def test_enumerate_chains_is_deterministic():
    first = paths.enumerate_chains("ä¸­æ–‡", max_depth=2)
    second = paths.enumerate_chains("ä¸­æ–‡", max_depth=2)
    assert [chain.path_string for chain in first] == [chain.path_string for chain in second]
    assert [chain.result for chain in first] == [chain.result for chain in second]


def test_collapse_by_result_keeps_one_chain_per_text():
    chains = paths.enumerate_chains("ä¸­æ–‡", max_depth=2)
    collapsed = paths.collapse_by_result(chains)
    results = [chain.result for chain in collapsed]
    assert len(results) == len(set(results))
    assert len(collapsed) <= len(chains)
