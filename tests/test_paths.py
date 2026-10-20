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
